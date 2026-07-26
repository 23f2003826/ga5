import re
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


@router.get("/q5")
async def get_q5():
    return {
        "message": "This is the solution for Question 5. Please check the /run-control endpoint."
    }


class Step(BaseModel):
    step_number: int
    tool: str
    args: dict
    tokens_used: int


class RunRequest(BaseModel):
    budget_tokens: int
    steps: list[Step]


def normalize_string(s: str) -> str:
    """Collapse whitespace and trim."""
    return re.sub(r"\s+", " ", s).strip()


def canonicalize(obj: Any):
    """
    Canonical representation of args:
    - remove client_ts recursively
    - normalize whitespace in strings
    - sort dict keys
    """
    if isinstance(obj, dict):
        return tuple(
            sorted(
                (
                    k,
                    canonicalize(v),
                )
                for k, v in obj.items()
                if k != "client_ts"
            )
        )

    if isinstance(obj, list):
        return tuple(canonicalize(x) for x in obj)

    if isinstance(obj, str):
        return normalize_string(obj)

    return obj


def same_call(a: Step, b: Step):
    return a.tool == b.tool and canonicalize(a.args) == canonicalize(b.args)


def has_three_identical(steps):
    """
    Detect A A A at the end.
    """

    if len(steps) < 3:
        return False

    s1 = steps[-1]
    s2 = steps[-2]
    s3 = steps[-3]

    return same_call(s1, s2) and same_call(s2, s3)


def has_two_step_cycle(steps):
    """
    Detect

    A B A B A B ...

    over the trailing history.

    Requires at least 6 trailing steps.
    """

    n = len(steps)

    if n < 6:
        return False

    tail = steps[-6:]

    A = tail[0]
    B = tail[1]

    if same_call(A, B):
        return False

    for i, step in enumerate(tail):
        if i % 2 == 0:
            if not same_call(step, A):
                return False
        else:
            if not same_call(step, B):
                return False

    return True


@router.post("/run-control")
async def run_control(req: RunRequest):
    total = sum(step.tokens_used for step in req.steps)

    if total >= req.budget_tokens:
        return {
            "decision": "halt",
            "reason": f"Cumulative tokens_used ({total}) has reached the budget ({req.budget_tokens}).",
        }

    if has_three_identical(req.steps):
        return {
            "decision": "halt",
            "reason": "Detected three identical consecutive tool calls.",
        }

    if has_two_step_cycle(req.steps):
        return {
            "decision": "halt",
            "reason": "Detected repeating two-step cycle.",
        }

    return {
        "decision": "continue",
        "reason": "Budget available and no execution loop detected.",
    }
