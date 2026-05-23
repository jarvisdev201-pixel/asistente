"""
FastAPI server factory — creates the Uvicorn server instance.
"""

from fastapi import FastAPI
from api.routes import router, system_state
from core.system_state import SystemState


def create_app(state: SystemState | None = None) -> FastAPI:
    app = FastAPI(
        title="Work Assistant Core",
        version="0.2.0",
        description="Local backend for monitoring, simulating and recording user activity.",
    )

    # Inject system state into routes module
    if state is not None:
        import api.routes as routes
        routes.system_state = state

    app.include_router(router)
    return app
