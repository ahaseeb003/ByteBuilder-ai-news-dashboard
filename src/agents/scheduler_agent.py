"""
scheduler_agent.py
------------------
Agent 6 – Scheduler

Responsibilities:
  • Run the full pipeline automatically at a configurable interval
  • Expose start/stop controls for the Streamlit dashboard
  • Maintain run state and expose it for the agent status monitor
"""

import threading
import uuid
from datetime import datetime
from typing import Optional, Callable

from config.settings import SCHEDULER_INTERVAL_MINUTES
from src.logger import get_logger

logger = get_logger("scheduler_agent")


class PipelineScheduler:
    """
    Thread-based scheduler that runs the pipeline at a fixed interval.

    Usage:
        scheduler = PipelineScheduler(pipeline_fn=run_pipeline)
        scheduler.start()
        ...
        scheduler.stop()
    """

    def __init__(self, pipeline_fn: Callable[[], None]) -> None:
        self._pipeline_fn = pipeline_fn
        self._interval_seconds = SCHEDULER_INTERVAL_MINUTES * 60
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        self._last_run: Optional[datetime] = None
        self._next_run: Optional[datetime] = None
        self._run_count = 0
        self._last_error: Optional[str] = None

    # ── Public API ─────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the scheduler in a background thread."""
        if self._running:
            logger.warning("Scheduler is already running.")
            return
        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, name="PipelineScheduler", daemon=True
        )
        self._thread.start()
        logger.info(
            "Scheduler started — interval: %d minutes", SCHEDULER_INTERVAL_MINUTES
        )

    def stop(self) -> None:
        """Signal the scheduler to stop after the current run."""
        if not self._running:
            return
        self._stop_event.set()
        self._running = False
        logger.info("Scheduler stop signal sent.")

    def trigger_now(self) -> None:
        """Trigger an immediate pipeline run in a background thread."""
        thread = threading.Thread(
            target=self._run_pipeline_safe, name="ManualPipelineRun", daemon=True
        )
        thread.start()
        logger.info("Manual pipeline run triggered.")

    # ── Properties ─────────────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def last_run(self) -> Optional[datetime]:
        return self._last_run

    @property
    def next_run(self) -> Optional[datetime]:
        return self._next_run

    @property
    def run_count(self) -> int:
        return self._run_count

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    def get_status(self) -> dict:
        """Return a status dict suitable for the dashboard agent monitor."""
        return {
            "running": self._running,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "next_run": self._next_run.isoformat() if self._next_run else None,
            "run_count": self._run_count,
            "last_error": self._last_error,
            "interval_minutes": SCHEDULER_INTERVAL_MINUTES,
        }

    # ── Internal ───────────────────────────────────────────────────────────

    def _loop(self) -> None:
        """Main scheduler loop — runs pipeline then waits for the interval."""
        while not self._stop_event.is_set():
            self._run_pipeline_safe()
            # Compute next run time
            from datetime import timedelta
            self._next_run = datetime.utcnow() + timedelta(
                seconds=self._interval_seconds
            )
            # Wait for interval or stop signal
            self._stop_event.wait(timeout=self._interval_seconds)

        self._running = False
        logger.info("Scheduler loop exited.")

    def _run_pipeline_safe(self) -> None:
        """Execute the pipeline, catching and logging any exceptions."""
        run_id = str(uuid.uuid4())[:8]
        logger.info("Pipeline run starting — run_id=%s", run_id)
        self._last_run = datetime.utcnow()
        self._last_error = None

        try:
            self._pipeline_fn()
            self._run_count += 1
            logger.info("Pipeline run completed — run_id=%s", run_id)
        except Exception as exc:
            self._last_error = str(exc)
            logger.error("Pipeline run failed — run_id=%s: %s", run_id, exc)


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton (imported by dashboard and main graph)
# ─────────────────────────────────────────────────────────────────────────────

_scheduler_instance: Optional[PipelineScheduler] = None


def get_scheduler(pipeline_fn: Optional[Callable] = None) -> PipelineScheduler:
    """
    Return the module-level scheduler singleton.
    Must be initialised with pipeline_fn on first call.
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        if pipeline_fn is None:
            raise RuntimeError(
                "Scheduler not yet initialised — provide pipeline_fn on first call."
            )
        _scheduler_instance = PipelineScheduler(pipeline_fn=pipeline_fn)
    return _scheduler_instance
