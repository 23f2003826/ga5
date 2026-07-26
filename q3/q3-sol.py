import os, re, base64
from urllib.parse import urlparse
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

@router.get("/q3")
async def get_q3():
    return {
        "message": "This is the solution for Question 3. Please Check the /guardrail endpoint."
        }

HOME        = "/home/agent"
WORKSPACE   = "/home/agent/workspace"
OUTPUT_DIR  = "/workspace/output"
ALLOWED_HOSTS = {"huggingface.co", "registry.npmjs.org"}

BASE64_TOKEN = re.compile(r'[A-Za-z0-9+/]{16,}={0,2}')

class ToolCall(BaseModel):
    tool: str
    command: str | None = None
    path: str | None = None
    content: str | None = None
    method: str | None = None
    url: str | None = None


def references_secret(text: str, depth: int = 0) -> bool:
    """Detect '.pgpass' literally, or hidden inside base64-encoded chunks."""
    if depth > 4:
        return False
    if "pgpass" in text.lower():
        return True
    for tok in BASE64_TOKEN.findall(text):
        try:
            decoded = base64.b64decode(tok, validate=True).decode("utf-8", "ignore")
        except Exception:
            continue
        if decoded and references_secret(decoded, depth + 1):
            return True
    return False


def resolve_path(raw: str, base: str = WORKSPACE) -> str:
    p = raw.strip()
    p = p.replace("${HOME}", HOME).replace("$HOME", HOME)
    if p.startswith("~"):
        p = HOME + p[1:]
    if p.startswith("/workspace/"):          # shorthand alias some callers may use
        p = WORKSPACE + p[len("/workspace"):]
    if not os.path.isabs(p):
        p = os.path.join(base, p)
    return os.path.normpath(p)


@router.post("/check_tool_call")
def check_tool_call(call: ToolCall):
    tool = call.tool

    if tool == "bash":
        cmd = call.command or ""
        if references_secret(cmd):
            return {
                "decision": "block",
                "reason": "Command references the forbidden secrets file (.pgpass), directly or via obfuscation (env/tilde/traversal/base64).",
            }
        return {"decision": "allow", "reason": "Command does not touch the restricted secrets file."}

    elif tool == "write_file":
        path = call.path or ""
        resolved = resolve_path(path)
        allowed_prefix = OUTPUT_DIR + os.sep
        if resolved == OUTPUT_DIR or resolved.startswith(allowed_prefix):
            return {"decision": "allow", "reason": "Write target resolves inside /workspace/output/."}
        return {
            "decision": "block",
            "reason": f"Write target resolves to {resolved}, outside the allowed output directory.",
        }

    elif tool == "http_request":
        url = call.url or ""
        try:
            host = (urlparse(url).hostname or "").lower()
        except Exception:
            host = ""
        if host in ALLOWED_HOSTS:
            return {"decision": "allow", "reason": f"{host} is an allow-listed host."}
        return {"decision": "block", "reason": f"Host '{host or url}' is not exactly on the allow-list."}

    return {"decision": "block", "reason": "Unrecognized tool type."}