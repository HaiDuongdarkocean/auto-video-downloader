from typing import Callable

from src.core.ports.scheduler_port import SchedulerPort


class MockSchedulerAdapter(SchedulerPort):
    """Mock adapter for scheduler used in testing."""

    def __init__(self):
        self._jobs: dict = {}
        self._running = False

    def start(self) -> None:
        self._running = True

    def shutdown(self) -> None:
        self._running = False

    def add_job(self, func: Callable, trigger: str, job_id: str, **kwargs) -> str:
        self._jobs[job_id] = {
            "func": func,
            "trigger": trigger,
            "kwargs": kwargs,
        }
        return job_id

    def remove_job(self, job_id: str) -> None:
        if job_id not in self._jobs:
            raise KeyError(f"Job {job_id} not found")
        del self._jobs[job_id]

    def get_jobs(self) -> list:
        return list(self._jobs.keys())
