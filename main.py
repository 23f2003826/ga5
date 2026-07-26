from fastapi import FastAPI
from q2.q2_sol import router as q2_router

app = FastAPI()

app.include_router(q2_router)

@app.get("/")
async def root():
    return {"message": "Hello World! This is GA5."}