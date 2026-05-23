"""
FastAPI routes for the Work Assistant API.
"""

from fastapi import APIRouter
from services.activity_service import ActivityService

router = APIRouter()
service = ActivityService()

SYSTEM_STATE = {"status": "active"}


@router.get("/")
async def system_status():
    return {"system": "Work Assistant Core", **SYSTEM_STATE}


@router.get("/activities")
async def get_activities(limit: int = 20):
    records = service.get_recent(limit=limit)
    return {"count": len(records), "activities": [r.__dict__ for r in records]}


@router.get("/summary")
async def get_summary():
    data = service.get_today_summary()
    return {"date_summary": data}
