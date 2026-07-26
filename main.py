from fastapi import FastAPI

from q2.q2_sol import router as q2_router
from q3.q3_sol import router as q3_router
from q4.q4_sol import router as q4_router
from q5.q5_sol import router as q5_router
from q6.q6_sol import (router as q6_router, mcp_app)
from q8.q8_sol import router as q8_router

app = FastAPI(lifespan=mcp_app.lifespan)

app.include_router(q2_router)
app.include_router(q3_router)
app.include_router(q4_router)
app.include_router(q5_router)
app.include_router(q6_router)
app.include_router(q8_router)

# Mount MCP server at /mcp endpoint
app.mount("/", mcp_app)

@app.get("/")
async def root():
    return {"message": "Hello World! This is GA5."}
