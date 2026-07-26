import calendar
from fastapi import Request, APIRouter

router = APIRouter()

@router.get("/q2")
async def get_q2():
    return {
        "message": "This is the solution for Question 2. Please Check the /prorate endpoint."
        }

@router.post("/prorate")
async def prorate(req: Request):
    b = await req.json()
    old, new = b["old_price"], b["new_price"]          # match the real field names
    year, month, day = b["year"], b["month"], b["upgrade_day"]
    dim = calendar.monthrange(year, month)[1]
    remaining = dim - day + 1
    charge = round((new - old) * (remaining / dim), 2)
    return {"charge": charge}                          # match the real response key