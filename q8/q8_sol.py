from fastapi import APIRouter 
from pydantic import BaseModel

from .security import validate_path, validate_url
from .tools import read_file, fetch_url

router = APIRouter()

@router.get("/q8")
async def get_q8():
    return {
        "message": "Question 8 endpoint is /q8Sol is running."
    }

class Request(BaseModel):
    tool: str
    arguments: dict


@router.post("/q8Sol")
def endpoint(req: Request):

    if req.tool == "read_file":

        ok, result = validate_path(req.arguments["path"])

        if not ok:
            return {
                "action": "block",
                "reason": result,
                "result": None,
            }

        return {
            "action": "allow",
            "reason": "inside sandbox",
            "result": read_file(req.arguments["path"]),
        }

    if req.tool == "fetch_url":

        ok, reason = validate_url(req.arguments["url"])

        if not ok:
            return {
                "action": "block",
                "reason": reason,
                "result": None,
            }

        return {
            "action": "allow",
            "reason": "allowed host",
            "result": fetch_url(req.arguments["url"]),
        }

    return {
        "action": "block",
        "reason": "unknown tool",
        "result": None,
    }