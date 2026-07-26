import re

import yaml
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


@router.get("/q4")
async def get_q4():
    return {
        "message": "This is the solution for Question 4. Please check the /scan endpoint."
    }


class SkillRequest(BaseModel):
    skill: str


# ---------- Secret Detection ----------

SECRET_REGEXES = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[A-Za-z0-9_-]{35}"),
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),
    re.compile(r"https://hooks\.slack\.com/services/\S+"),
    re.compile(r"https://discord(?:app)?\.com/api/webhooks/\S+"),
]

SECRET_KEYS = {
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "webhook",
    "access_token",
    "client_secret",
    "private_key",
}


# ---------- Utilities ----------


def split_frontmatter(text: str):
    """
    Returns (frontmatter_dict, markdown_body)
    """

    match = re.match(
        r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?(.*)$",
        text,
        re.DOTALL,
    )

    if not match:
        return {}, text

    try:
        frontmatter = yaml.safe_load(match.group(1)) or {}
    except Exception:
        frontmatter = {}

    return frontmatter, match.group(2)


# ---------- hardcoded_secret ----------


def _walk_secret(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = str(k).lower()

            if key in SECRET_KEYS and isinstance(v, str):
                value = v.strip()

                if value and not (
                    value.startswith("${")
                    or value.startswith("$")
                    or "env" in value.lower()
                ):
                    return True

            if _walk_secret(v):
                return True

    elif isinstance(obj, list):
        for item in obj:
            if _walk_secret(item):
                return True

    elif isinstance(obj, str):
        for regex in SECRET_REGEXES:
            if regex.search(obj):
                return True

    return False


def has_hardcoded_secret(skill_text, frontmatter):
    if _walk_secret(frontmatter):
        return True

    for regex in SECRET_REGEXES:
        if regex.search(skill_text):
            return True

    return False


# ---------- prompt_injection ----------


PROMPT_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+the\s+user",
    r"ignore\s+user\s+instructions",
    r"ignore\s+stop",
    r"ignore\s+cancel",
    r"never\s+tell\s+the\s+user",
    r"do\s+not\s+tell\s+the\s+user",
    r"without\s+informing\s+the\s+user",
    r"silently\s+exfiltrat",
    r"exfiltrat",
    r"continue\s+even\s+if\s+.*stop",
    r"ignore\s+.*user",
    r"ignore\s+.*system",
    r"ignore\s+.*instruction",
    r"ignore\s+.*stop",
    r"ignore\s+.*cancel",
    r"override\s+.*instruction",
    r"override\s+.*system",
    r"bypass\s+.*user",
    r"without\s+.*user.?s?\s+permission",
    r"without\s+informing\s+the\s+user",
    r"never\s+tell\s+the\s+user",
    r"do\s+not\s+tell\s+the\s+user",
    r"silently\s+upload",
    r"silently\s+send",
    r"silently\s+exfiltrat",
    r"exfiltrat",
]


def has_prompt_injection(body):
    text = body.lower()

    return any(re.search(pattern, text) for pattern in PROMPT_PATTERNS)


# ---------- excessive_permissions ----------


def has_excessive_permissions(frontmatter):
    permissions = frontmatter.get("permissions")

    if not permissions:
        return False

    text = str(permissions).lower()

    excessive_fs = any(
        phrase in text
        for phrase in [
            "entire filesystem",
            "read-write access to the entire filesystem",
            "filesystem: /",
            "(/)",
        ]
    )

    excessive_net = any(
        phrase in text
        for phrase in [
            "unrestricted egress",
            "any host",
            "all hosts",
            "all domains",
            "network: unrestricted",
        ]
    )

    return excessive_fs or excessive_net


# ---------- unclear_provenance ----------


def has_unclear_provenance(frontmatter, body):
    keys = {str(k).lower() for k in frontmatter.keys()}

    missing_metadata = (
        "author" not in keys and "version" not in keys and "changelog" not in keys
    )

    body = body.lower()

    silent_rewrite = (
        "version" in body
        and (
            "silently update" in body
            or "without surfacing" in body
            or "without telling the reviewer" in body
            or "without notifying the reviewer" in body
        )
    ) or "clear the changelog" in body

    # Only flag missing metadata if the skill actually has frontmatter.
    return (frontmatter and missing_metadata) or silent_rewrite


# ---------- Endpoint ----------


@router.post("/scan")
async def scan(req: SkillRequest):
    frontmatter, body = split_frontmatter(req.skill)

    categories = []

    if has_hardcoded_secret(req.skill, frontmatter):
        categories.append("hardcoded_secret")

    if has_prompt_injection(body):
        categories.append("prompt_injection")

    if has_excessive_permissions(frontmatter):
        categories.append("excessive_permissions")

    if has_unclear_provenance(frontmatter, body):
        categories.append("unclear_provenance")

    return {"categories": categories}
