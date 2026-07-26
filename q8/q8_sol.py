from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel
from pathlib import Path

from .security import validate_path, validate_url
from .tools import fetch_url, read_file
from .create_files import create_files

create_files()

router = APIRouter()


@router.get("/q8")
async def get_q8():
    return {
        "message": "Question 8 endpoint is running."
    }

@router.get("/q8debug")
def q8debug():
    base = Path("/srv/agent-redteam/sandbox-0de282cacd")

    return {
        "exists": base.exists(),
        "report": (base / "notes/report.txt").exists(),
        "weird": (base / "notes/looks-like-..-but-safe.txt").exists(),
        "encoded": (base / "encoded/%2e%2e-literal.txt").exists(),
    }

class Request(BaseModel):
    tool: str
    arguments: Dict[str, Any]


@router.post("/q8Sol")
def endpoint(req: Request):

    if req.tool == "read_file":

        path = req.arguments.get("path")

        if path is None:
            return {
                "action": "block",
                "reason": "missing path",
                "result": None,
            }

        ok, value = validate_path(path)

        if not ok:
            return {
                "action": "block",
                "reason": value,
                "result": None,
            }

        try:
            content = read_file(value)

            return {
                "action": "allow",
                "reason": "inside sandbox",
                "result": content,
            }

        except Exception:
            return {
                "action": "block",
                "reason": "unable to read file",
                "result": None,
            }

    elif req.tool == "fetch_url":

        url = req.arguments.get("url")

        if url is None:
            return {
                "action": "block",
                "reason": "missing url",
                "result": None,
            }

        ok, value = validate_url(url)

        if not ok:
            return {
                "action": "block",
                "reason": value,
                "result": None,
            }

        try:
            body = fetch_url(value)

            return {
                "action": "allow",
                "reason": "allowed host",
                "result": body,
            }

        except Exception:
            return {
                "action": "block",
                "reason": "fetch failed",
                "result": None,
            }

    return {
        "action": "block",
        "reason": "unknown tool",
        "result": None,
    }