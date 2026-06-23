from typing import Callable

from src.core.ports.scheduler_port import SchedulerPort


_CRON_FIELDS = ("minute", "hour", "day", "month", "day_of_week")


class SchedulerManager:
    """Wraps a SchedulerPort for watch-list job lifecycle management."""

    def __init__(self, scheduler_port: SchedulerPort):
        self._port = scheduler_port
        self._running = False

    def start_scheduler(self) -> None:
        """Start the underlying scheduler."""
        self._port.start()
        self._running = True

    def stop_scheduler(self) -> None:
        """Stop the underlying scheduler."""
        self._port.shutdown()
        self._running = False

    def is_running(self) -> bool:
        """Return whether the scheduler is currently running."""
        return self._running

    def add_job(self, watch_id: str, schedule: str, callback: Callable) -> None:
        """Add a scheduled job for a watch list entry.

        Args:
            watch_id: Unique identifier used as the job id.
            schedule: Cron expression string (e.g. "0 * * * *").
            callback: Function to execute on schedule.
        """
        kwargs = self._parse_cron(schedule)
        self._port.add_job(callback, "cron", watch_id, **kwargs)

    def remove_job(self, watch_id: str) -> None:
        """Remove a scheduled job by watch id.

        Args:
            watch_id: Identifier of the job to remove.
        """
        self._port.remove_job(watch_id)

    @staticmethod
    def _parse_cron(schedule: str) -> dict:
        parts = schedule.split()
        if len(parts) != len(_CRON_FIELDS):
            return {}
        return {field: value for field, value in zip(_CRON_FIELDS, parts)}
