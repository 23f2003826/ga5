from hashlib import sha256

from fastapi import APIRouter
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers

EMAIL = "23f2003826@ds.study.iitm.ac.in".strip().lower()

router = APIRouter()

mcp = FastMCP("Exam MCP")


@router.get("/q6")
async def get_q6():
    return {
        "message": "Question 6 MCP server is running."
    }


@mcp.tool(
    name="solve_challenge",
    description="Returns the challenge response."
)
async def solve_challenge() -> str:
    headers = get_http_headers()

    challenge = (
        headers.get("x-exam-challenge")
        or headers.get("X-Exam-Challenge")
    )

    if challenge is None:
        raise ValueError("Missing X-Exam-Challenge")

    return sha256(
        f"{challenge}:{EMAIL}".encode("utf-8")
    ).hexdigest()[:16]


# Create the MCP ASGI app
mcp_app = mcp.http_app()