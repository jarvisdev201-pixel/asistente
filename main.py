"""
Work Assistant Core — Entry point.
Initialises all layers and keeps the system alive.
"""

import uvicorn

from core.event_bus import EventBus
from core.activity_tracker import ActivityTracker
from core.system_state import SystemState
from core.processor import Processor
from api.server import create_app
from db.database import init_db
from services.logger import info


def main() -> None:
    info("=== Work Assistant Core v0.2 starting ===")

    # Database
    init_db()

    # Event system
    bus = EventBus()

    # Live system state (new in v0.2)
    state = SystemState()

    # Activity simulation
    tracker = ActivityTracker(bus)

    # Processing layer
    from services.activity_service import ActivityService

    activity_service = ActivityService()
    processor = Processor(bus, activity_service, state)

    # Start internal subsystems
    processor.start()
    tracker.start()

    # FastAPI server with state injected
    app = create_app(state)

    info("Work Assistant Core v0.2 running on http://127.0.0.1:8000")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
