from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

from src.core.ports.scheduler_port import SchedulerPort


class APSchedulerAdapter(SchedulerPort):
    """Production adapter for scheduler using APScheduler."""

    def __init__(self):
        self._scheduler = BackgroundScheduler()

    def start(self) -> None:
        if not self._scheduler.running:
            self._scheduler.start()

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    def add_job(self, func: Callable, trigger: str, job_id: str, **kwargs) -> str:
        if trigger == "cron":
            trigger_obj = CronTrigger(**kwargs)
        elif trigger == "interval":
            trigger_obj = IntervalTrigger(**kwargs)
        elif trigger == "date":
            trigger_obj = DateTrigger(**kwargs)
        else:
            raise ValueError(f"Unknown trigger type: {trigger}")

        self._scheduler.add_job(func=func, trigger=trigger_obj, id=job_id, replace_existing=True)
        return job_id

    def remove_job(self, job_id: str) -> None:
        self._scheduler.remove_job(job_id)

    def get_jobs(self) -> list:
        return [job.id for job in self._scheduler.get_jobs()]
