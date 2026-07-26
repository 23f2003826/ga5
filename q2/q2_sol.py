import calendar
from fastapi import Request, APIRouter, HTTPException

router = APIRouter()

@router.get("/q2")
async def get_q2():
    return {
        "message": "This is the solution for Question 2. Please Check the /prorate endpoint."
        }

@router.post("/prorate")
async def prorate(req: Request):
    b = await req.json()

    old_price = b["old_price"]
    new_price = b["new_price"]          
    days_remaining = b["days_remaining"]                                
    days_in_actual_month = b["days_in_actual_month"]
    spec = b["spec"]

    difference = new_price - old_price

    if spec == "v1":
        charge = difference * (days_remaining / 30)
    elif spec == "v2":
        charge = difference * (days_remaining / days_in_actual_month)
    else:
        raise HTTPException(status_code=400, detail="Invalid spec")

    return {"charge": charge}
