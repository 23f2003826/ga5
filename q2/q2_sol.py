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
    old_price, new_price = b["old_price"], b["new_price"]          # match the real field names
    days_remaining = b["days_remaining"]                                  # match the real field name
    days_in_actual_month = b["days_in_actual_month"]                          # match the real field name
    spec = b["spec"]

    difference = new_price - old_price

    if spec == "v1":
        charge = difference * (days_remaining / 30)
    elif spec == "v2":
        charge = difference * (days_remaining / days_in_actual_month)
    else:
        return {"error": "Invalid spec"}

    return {"charge": round(charge, 2)}