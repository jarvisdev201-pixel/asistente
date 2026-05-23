"""
Daily Log routes — API endpoints for daily work logging and report generation.
"""

from datetime import date, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from integrations.daily_log import (
    init_daily_log_tables,
    add_log_entry,
    get_logs_by_date,
    get_recent_logs,
    delete_log_entry,
    generate_report,
)

router = APIRouter(prefix="/report", tags=["report"])


# ── Request models ────────────────────────────────────────────────────


class LogEntryRequest(BaseModel):
    project_name: str
    list_name: str
    task_name: str
    task_id: str = ""
    progress: int = 0
    notes: str = ""


# ── Endpoints ─────────────────────────────────────────────────────────


@router.post("/log")
async def create_log_entry(entry: LogEntryRequest):
    """Add a new daily log entry."""
    today = date.today().isoformat()
    entry_id = add_log_entry(
        date=today,
        project_name=entry.project_name,
        list_name=entry.list_name,
        task_name=entry.task_name,
        task_id=entry.task_id,
        progress=entry.progress,
        notes=entry.notes,
    )
    return {"id": entry_id, "message": "Log entry added", "date": today}


@router.get("/log")
async def get_logs(
    date_str: str | None = Query(None, alias="date"),
    limit: int = 50,
):
    """Get log entries for a specific date or recent ones."""
    if date_str:
        logs = get_logs_by_date(date_str)
    else:
        logs = get_recent_logs(limit=limit)
    return {"count": len(logs), "logs": logs}


@router.delete("/log/{entry_id}")
async def delete_entry(entry_id: int):
    """Delete a log entry."""
    if delete_log_entry(entry_id):
        return {"message": "Entry deleted"}
    raise HTTPException(404, "Entry not found")


@router.get("/daily")
async def get_daily_report(date_str: str | None = Query(None, alias="date")):
    """Generate the formatted daily report."""
    today = date.today().isoformat()
    report_date = date_str or today
    report = generate_report(report_date)
    return {"date": report_date, "report": report}
