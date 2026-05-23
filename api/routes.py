"""
FastAPI routes for the Work Assistant API.
"""

from fastapi import APIRouter
from services.activity_service import ActivityService
from core.system_state import SystemState

router = APIRouter()
service = ActivityService()

# Will be injected by main.py
system_state: SystemState | None = None

SYSTEM_STATUS = {"status": "active"}


@router.get("/")
async def system_status():
    return {"system": "Work Assistant Core", **SYSTEM_STATUS}


@router.get("/state")
async def get_live_state():
    """Return the live in-memory system state."""
    if system_state is None:
        return {"error": "System state not initialized"}
    return system_state.get_state()


@router.get("/activities")
async def get_activities(limit: int = 20):
    records = service.get_recent(limit=limit)
    return {"count": len(records), "activities": [r.__dict__ for r in records]}


@router.get("/summary")
async def get_summary():
    data = service.get_today_summary()
    return {"date_summary": data}
