"""
FastAPI server factory — creates the Uvicorn server instance.
"""

from fastapi import FastAPI
from api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Work Assistant Core",
        version="0.1.0",
        description="Local backend for monitoring, simulating and recording user activity.",
    )
    app.include_router(router)
    return app
