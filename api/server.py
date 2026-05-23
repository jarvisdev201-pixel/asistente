"""
FastAPI server factory — creates the Uvicorn server instance.
"""

from fastapi import FastAPI
from api.routes import router
from core.system_state import SystemState
from core.event_stream import EventStream


def create_app(
    state: SystemState | None = None,
    stream: EventStream | None = None,
) -> FastAPI:
    app = FastAPI(
        title="Work Assistant Core",
        version="0.3.0",
        description="Local backend for monitoring, simulating and recording user activity.",
    )

    # Inject dependencies into routes module
    import api.routes as routes

    if state is not None:
        routes.system_state = state
    if stream is not None:
        routes.event_stream = stream

    app.include_router(router)
    return app
