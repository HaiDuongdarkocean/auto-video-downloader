from src.core.ports.mock_scheduler_adapter import MockSchedulerAdapter
from src.core.tracking.scheduler_manager import SchedulerManager


class TestSchedulerManager:
    """Tests for SchedulerManager."""

    def test_is_running_false_before_start(self):
        port = MockSchedulerAdapter()
        manager = SchedulerManager(port)
        assert manager.is_running() is False

    def test_start_sets_running(self):
        port = MockSchedulerAdapter()
        manager = SchedulerManager(port)
        manager.start_scheduler()
        assert manager.is_running() is True

    def test_stop_sets_not_running(self):
        port = MockSchedulerAdapter()
        manager = SchedulerManager(port)
        manager.start_scheduler()
        manager.stop_scheduler()
        assert manager.is_running() is False

    def test_is_running_true_after_start(self):
        port = MockSchedulerAdapter()
        manager = SchedulerManager(port)
        manager.start_scheduler()
        assert manager.is_running() is True

    def test_add_job_called_on_port(self):
        port = MockSchedulerAdapter()
        manager = SchedulerManager(port)
        manager.start_scheduler()

        def callback():
            return None

        manager.add_job("watch1", "0 * * * *", callback)
        assert "watch1" in port.get_jobs()

    def test_remove_job_called_on_port(self):
        port = MockSchedulerAdapter()
        manager = SchedulerManager(port)
        manager.start_scheduler()

        def callback():
            return None

        manager.add_job("watch1", "0 * * * *", callback)
        manager.remove_job("watch1")
        assert "watch1" not in port.get_jobs()
