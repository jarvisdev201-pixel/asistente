"""
Work Assistant Core — Entry point.
Initialises all layers and keeps the system alive.
"""

import threading
import uvicorn

from core.event_bus import EventBus
from core.activity_tracker import ActivityTracker
from core.processor import Processor
from api.server import create_app
from db.database import init_db
from services.logger import info


def main() -> None:
    info("=== Work Assistant Core starting ===")

    # Database
    init_db()

    # Event system
    bus = EventBus()

    # Activity simulation
    tracker = ActivityTracker(bus)

    # Processing layer
    from services.activity_service import ActivityService

    activity_service = ActivityService()
    processor = Processor(bus, activity_service)

    # Start internal subsystems
    processor.start()
    tracker.start()

    # FastAPI server
    app = create_app()

    info("Work Assistant Core is running on http://127.0.0.1:8000")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
