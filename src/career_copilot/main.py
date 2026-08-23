from fastapi import FastAPI

from career_copilot.api.health import router as health_router

app = FastAPI(
    title="Career Copilot",
    description="AI-powered CV tailoring grounded in real experience",
    version="0.2.0",
)

app.include_router(health_router)
