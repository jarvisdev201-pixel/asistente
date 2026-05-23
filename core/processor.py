"""
Processor — listens to EventBus events, normalizes data and forwards
to the service layer for persistence.
"""

from typing import Any
from core.event_bus import EventBus
from services.logger import info


class Processor:
    """Listens to events, normalizes payloads and pushes them to storage."""

    def __init__(self, event_bus: EventBus, activity_service: Any) -> None:
        self._bus = event_bus
        self._activity_service = activity_service

    def start(self) -> None:
        self._bus.subscribe("activity.update", self._on_activity)
        self._bus.subscribe("activity.switch", self._on_switch)
        self._bus.subscribe("activity.idle", self._on_idle)
        info("Processor started and listening for events")

    def _normalize(self, data: dict) -> dict:
        return {
            "timestamp": data.get("timestamp"),
            "activity_type": data.get("activity_type", "unknown"),
            "window_name": data.get("window_name", "unknown"),
            "duration": data.get("duration", 0.0),
            "session_id": data.get("session_id", "unknown"),
        }

    def _on_activity(self, event: str, data: dict) -> None:
        info(f"Processing activity.update: {data.get('activity_type')}")
        record = self._normalize(data)
        self._activity_service.save_activity(record)

    def _on_switch(self, event: str, data: dict) -> None:
        info(
            f"Activity switch: {data.get('previous_type')} → {data.get('activity_type')}"
        )

    def _on_idle(self, event: str, data: dict) -> None:
        info(f"Idle event — no persistence needed")
