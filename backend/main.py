"""
FastAPI entry point — wraps the existing adminFee agent CLI code
into a REST API without modifying the original files.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.processing import router as processing_router
from routes.analysis import router as analysis_router

app = FastAPI(
    title="hunterAI AdminFee Automation",
    description="Web frontend wrapper for AdminFee processing and analysis agents",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(processing_router)
app.include_router(analysis_router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "adminFee-agent-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
