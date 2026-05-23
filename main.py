"""
Work Assistant Core — Entry point.
Initialises all layers and keeps the system alive.
"""

import asyncio
import threading

import uvicorn

from core.event_bus import EventBus
from core.system_state import SystemState
from core.event_stream import EventStream
from core.processor import Processor
from api.server import create_app
from db.database import init_db
from services.logger import info


def main() -> None:
    info("=== Work Assistant Core v0.5 starting ===")

    # Database
    init_db()

    # ClickUp cache tables
    from integrations.clickup_db import init_clickup_tables
    init_clickup_tables()

    # Daily log tables
    from integrations.daily_log import init_daily_log_tables
    init_daily_log_tables()

    # Event system
    bus = EventBus()

    # Live system state
    state = SystemState()

    # Event stream (WebSocket bridge)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    stream = EventStream(bus, state, loop=loop)

    # ── Real activity monitoring (macOS) ─────────────────────────────
    from core.real_activity_tracker import RealActivityTracker
    tracker = RealActivityTracker(bus, use_simulation_fallback=True)

    # Processing layer
    from services.activity_service import ActivityService

    activity_service = ActivityService()
    processor = Processor(bus, activity_service, state, stream)

    # ── Start internal subsystems ─────────────────────────────────────
    processor.start()
    tracker.start()

    # ── FastAPI with streaming layer ──────────────────────────────────
    app = create_app(state=state, stream=stream)

    # ── Start heartbeat loop on the same event loop ───────────────────
    def run_async_loop():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(stream.heartbeat_loop(interval=5.0))

    hb_thread = threading.Thread(target=run_async_loop, daemon=True)
    hb_thread.start()

    info("Work Assistant Core v0.5 running on http://127.0.0.1:8000")
    info("WebSocket endpoint: ws://127.0.0.1:8000/ws/state")
    info("ClickUp integration ready")
    info("Real activity monitoring active (macOS)")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
