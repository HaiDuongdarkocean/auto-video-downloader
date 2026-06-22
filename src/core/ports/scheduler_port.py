from abc import ABC, abstractmethod
from typing import Callable, Optional


class SchedulerPort(ABC):
    """Port interface for scheduler operations."""

    @abstractmethod
    def start(self) -> None:
        """Start the scheduler."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shut down the scheduler."""
        pass

    @abstractmethod
    def add_job(
        self,
        func: Callable,
        trigger: str,
        job_id: str,
        **kwargs,
    ) -> str:
        """Add a scheduled job.

        Args:
            func: The function to execute.
            trigger: Trigger type (e.g., 'cron', 'interval', 'date').
            job_id: Unique identifier for the job.
            **kwargs: Additional trigger arguments (e.g., hour, minute for cron).

        Returns:
            The job ID.
        """
        pass

    @abstractmethod
    def remove_job(self, job_id: str) -> None:
        """Remove a scheduled job by ID.

        Args:
            job_id: The unique identifier of the job to remove.

        Raises:
            KeyError: If the job does not exist.
        """
        pass

    @abstractmethod
    def get_jobs(self) -> list:
        """Get all scheduled jobs.

        Returns:
            List of job IDs.
        """
        pass
