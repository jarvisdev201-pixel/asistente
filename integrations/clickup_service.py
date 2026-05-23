"""
ClickUp Service — high-level operations: sync, query, and report generation.
"""

from datetime import datetime, timezone
from typing import Any

from integrations.clickup_client import ClickUpClient
from integrations.clickup_config import load_token
from integrations.clickup_db import (
    init_clickup_tables,
    clear_cache,
    upsert_teams,
    upsert_spaces,
    upsert_folders,
    upsert_lists,
    upsert_tasks,
    get_cached_tasks,
    get_cached_structure,
)
from services.logger import info, error


class ClickUpService:
    """High-level service for ClickUp integration."""

    def __init__(self) -> None:
        self._client: ClickUpClient | None = None
        self._user_id: str | None = None

    # ── Connection ────────────────────────────────────────────────────

    def is_connected(self) -> bool:
        token = load_token()
        return token is not None

    def connect(self, token: str) -> dict:
        """Test connection and fetch user/team info."""
        from integrations.clickup_config import save_token
        save_token(token)
        self._client = ClickUpClient(token)
        teams = self._client.get_teams()
        if not teams:
            raise ValueError("No teams found for this token")
        info(f"Connected to ClickUp: {', '.join(t['name'] for t in teams)}")
        return {"teams": [{"id": t["id"], "name": t["name"]} for t in teams]}

    def disconnect(self) -> None:
        from integrations.clickup_config import delete_token
        delete_token()
        self._client = None

    # ── Client lazy loader ────────────────────────────────────────────

    def _ensure_client(self) -> ClickUpClient:
        if self._client is not None:
            return self._client
        token = load_token()
        if not token:
            raise RuntimeError("ClickUp not configured. Set your API token first.")
        self._client = ClickUpClient(token)
        return self._client

    # ── Sync ──────────────────────────────────────────────────────────

    def sync_all(self, days_back: int = 7) -> dict:
        """
        Full sync: teams → spaces → folders → lists → tasks.
        Only fetches tasks updated in the last `days_back` days for performance.
        """
        import time
        client = self._ensure_client()
        init_clickup_tables()
        clear_cache()

        teams = client.get_teams()
        upsert_teams(teams)
        total_tasks = 0
        lists_count = 0

        # Only fetch recently updated tasks
        from datetime import timedelta
        date_updated_gt = int((datetime.now(timezone.utc) - timedelta(days=days_back)).timestamp() * 1000)

        start = time.time()

        for team in teams:
            tid = team["id"]
            spaces = client.get_spaces(tid)
            upsert_spaces(spaces, tid)

            for space in spaces:
                sid = space["id"]
                # Folders with lists
                folders = client.get_folders(sid)
                upsert_folders(folders, sid)
                for folder in folders:
                    lists = client.get_lists(folder["id"])
                    upsert_lists(lists, folder["id"], sid)
                    for lst in lists:
                        lists_count += 1
                        tasks = client.get_tasks(
                            lst["id"],
                            include_closed=True,
                            date_updated_gt=date_updated_gt,
                            max_pages=1,
                        )
                        if tasks:
                            upsert_tasks(tasks)
                            total_tasks += len(tasks)
                            info(f"    sync {lst['name']}: {len(tasks)} tasks")

                # Folderless lists
                folderless = client.get_folderless_lists(sid)
                upsert_lists(folderless, None, sid)
                for lst in folderless:
                    lists_count += 1
                    tasks = client.get_tasks(
                        lst["id"],
                        include_closed=True,
                        date_updated_gt=date_updated_gt,
                        max_pages=1,
                    )
                    if tasks:
                        upsert_tasks(tasks)
                        total_tasks += len(tasks)
                        info(f"    sync {lst['name']}: {len(tasks)} tasks")

        elapsed = round(time.time() - start, 2)
        info(f"Sync complete: {lists_count} lists, {total_tasks} tasks in {elapsed}s")
        return {"teams": len(teams), "lists": lists_count, "tasks_synced": total_tasks, "elapsed": elapsed}

    # ── Queries ───────────────────────────────────────────────────────

    def get_structure(self) -> dict:
        return get_cached_structure()

    def get_tasks(
        self,
        list_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        return get_cached_tasks(list_id=list_id, status=status, limit=limit)

    def get_today_tasks(self) -> list[dict]:
        """Return tasks updated in the last 24 hours."""
        return get_cached_tasks(limit=200)

    # ── Report ────────────────────────────────────────────────────────

    def generate_daily_report(self) -> dict:
        """Generate end-of-day report crossing activity data with ClickUp tasks."""
        from services.activity_service import ActivityService
        from db.database import get_connection

        activity_svc = ActivityService()
        summary = activity_svc.get_today_summary()
        recent_activities = activity_svc.get_recent(limit=200)

        # Get today's cached tasks
        today_tasks = get_cached_tasks(limit=100)

        # Group activities by type for time breakdown
        time_breakdown = {item["activity_type"]: {
            "count": item["count"],
            "total_duration": item["total_duration"],
        } for item in summary}

        # Identify projects from tasks
        projects = {}
        for task in today_tasks:
            pname = task.get("project_name", "Sin proyecto") or "Sin proyecto"
            if pname not in projects:
                projects[pname] = {"tasks": [], "total": 0}
            projects[pname]["tasks"].append({
                "id": task["id"],
                "name": task["name"],
                "status": task["status"],
            })
            projects[pname]["total"] += 1

        return {
            "date": datetime.now(timezone.utc).date().isoformat(),
            "time_breakdown": time_breakdown,
            "total_activities": len(recent_activities),
            "projects": projects,
            "tasks_in_clickup": len(today_tasks),
        }
