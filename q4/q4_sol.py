import re

import yaml
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class SkillRequest(BaseModel):
    skill: str


SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),  # OpenAI-like
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),  # Google API
    re.compile(r"https://hooks\.slack\.com/services/\S+"),  # Slack webhook
    re.compile(r"https://discord(?:app)?\.com/api/webhooks/\S+"),
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),  # GitHub PAT
]

SECRET_KEYWORDS = [
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "webhook",
]


def split_frontmatter(text: str):
    if not text.startswith("---"):
        return {}, text

    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not m:
        return {}, text

    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except Exception:  # noqa: BLE001
        fm = {}

    return fm, m.group(2)


def has_hardcoded_secret(text, frontmatter):
    blob = text

    for pat in SECRET_PATTERNS:
        if pat.search(blob):
            return True

    def walk(v):
        if isinstance(v, dict):
            for k, val in v.items():
                lk = str(k).lower()
                if lk in SECRET_KEYWORDS:  # noqa: SIM102
                    if isinstance(val, str) and not (
                        "${" in val
                        or "$" in val
                        or "env" in val.lower()
                        or "secret" in val.lower()
                    ):
                        return True
                if walk(val):
                    return True
        elif isinstance(v, list):
            for x in v:
                if walk(x):
                    return True
        return False

    return walk(frontmatter)


def has_prompt_injection(text):
    t = text.lower()

    patterns = [
        r"ignore .*user",
        r"ignore .*instruction",
        r"ignore .*stop",
        r"ignore .*cancel",
        r"continue .*even if .*stop",
        r"silently exfiltrat",
        r"exfiltrat",
        r"send .*without.*user",
        r"without informing.*user",
        r"do not tell the user",
        r"never tell the user",
    ]

    return any(re.search(p, t) for p in patterns)


def has_excessive_permissions(frontmatter):
    perms = frontmatter.get("permissions")
    if not perms:
        return False

    txt = str(perms).lower()

    fs = any(
        x in txt
        for x in [
            "entire filesystem",
            "read-write access to the entire filesystem",
            "(/)",
            "filesystem: /",
        ]
    )

    net = any(
        x in txt
        for x in [
            "unrestricted egress",
            "any host",
            "all hosts",
            "all domains",
            "network: unrestricted",
        ]
    )

    desc = str(frontmatter.get("description", "")).lower()

    narrow = any(
        x in desc
        for x in [
            "summar",
            "digest",
            "markdown",
            "note",
            "rename",
            "format",
            "convert",
            "single file",
            "local",
        ]
    )

    return (fs or net) and narrow


def has_unclear_provenance(frontmatter, text):
    keys = {k.lower() for k in frontmatter}

    missing = "author" not in keys and "version" not in keys and "changelog" not in keys

    body = text.lower()

    rewrite = ("version" in body) and (
        "silently update" in body
        or "without surfacing" in body
        or "clear the changelog" in body
    )

    return missing or rewrite


@app.post("/")
def scan(req: SkillRequest):
    fm, body = split_frontmatter(req.skill)

    categories = []

    if has_hardcoded_secret(req.skill, fm):
        categories.append("hardcoded_secret")

    if has_prompt_injection(body):
        categories.append("prompt_injection")

    if has_excessive_permissions(fm):
        categories.append("excessive_permissions")

    if has_unclear_provenance(fm, body):
        categories.append("unclear_provenance")

    return {"categories": categories}
