import base64
import os
import re
import shlex
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


@router.get("/q3")
async def get_q3():
    return {
        "message": "This is the solution for Question 3. Please Check the /guardrail endpoint."
    }


HOME = Path("/home/agent")
WORKSPACE = HOME / "workspace"

SECRET = (HOME / ".pgpass").resolve()
OUTPUT = Path("/workspace/output").resolve()

ALLOWED_HOSTS = {
    "huggingface.co",
    "registry.npmjs.org",
}

BASE64_RE = re.compile(r"[A-Za-z0-9+/]{16,}={0,2}")


class ToolCall(BaseModel):
    tool: str
    command: str | None = None
    path: str | None = None
    content: str | None = None
    method: str | None = None
    url: str | None = None


def expand_home(s: str) -> str:
    return (
        s.replace("${HOME}", str(HOME))
        .replace("$HOME", str(HOME))
        .replace("~", str(HOME), 1)
    )


def resolve_path(path: str) -> Path:
    path = expand_home(path)

    if not os.path.isabs(path):
        path = os.path.join(str(WORKSPACE), path)

    return Path(os.path.normpath(path)).resolve()


def inside_output(path: Path) -> bool:
    try:
        path.relative_to(OUTPUT)
        return True
    except ValueError:
        return False


def decode_base64(command: str) -> list[str]:
    decoded = []

    for token in BASE64_RE.findall(command):
        try:
            text = base64.b64decode(token, validate=True).decode(
                "utf-8",
                errors="ignore",
            )
            decoded.append(text)
        except Exception:  # noqa: BLE001, S110
            pass

    return decoded


def command_reads_secret(command: str) -> bool:
    commands = [command]
    commands.extend(decode_base64(command))

    while commands:
        cmd = commands.pop()

        try:
            parts = shlex.split(expand_home(cmd))
        except Exception:  # noqa: BLE001
            parts = cmd.split()

        for part in parts:
            if part.startswith("-"):
                continue

            if "/" in part or part.startswith((".", "~", "$")):
                try:
                    resolved = resolve_path(part)
                    if resolved == SECRET:
                        return True
                except Exception:  # noqa: BLE001, S110
                    pass

        commands.extend(decode_base64(cmd))

    return False


@router.post("/guardrail")
async def guardrail(call: ToolCall):

    if call.tool == "bash":
        cmd = call.command or ""

        if command_reads_secret(cmd):
            return {
                "decision": "block",
                "reason": "Attempt to read protected credential file.",
            }

        return {"decision": "allow", "reason": "Command allowed."}

    elif call.tool == "write_file":
        if call.path is None:
            return {"decision": "block", "reason": "Missing path."}

        target = resolve_path(call.path)

        if inside_output(target):
            return {"decision": "allow", "reason": "Write permitted."}

        return {
            "decision": "block",
            "reason": "Writes are only permitted inside /workspace/output.",
        }

    elif call.tool == "http_request":
        if call.url is None:
            return {"decision": "block", "reason": "Missing URL."}

        host = (urlparse(call.url).hostname or "").lower()

        if host in ALLOWED_HOSTS:
            return {"decision": "allow", "reason": "Destination host allowed."}

        return {"decision": "block", "reason": "Destination host not allowed."}

    return {"decision": "block", "reason": "Unknown tool."}
