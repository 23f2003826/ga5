from fastapi import FastAPI

from q2.q2_sol import router as q2_router
from q3.q3_sol import router as q3_router

app = FastAPI()

app.include_router(q2_router)
app.include_router(q3_router)


@app.get("/")
async def root():
    return {"message": "Hello World! This is GA5."}
