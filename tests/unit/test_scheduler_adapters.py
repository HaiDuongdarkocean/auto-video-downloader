import pytest

from src.core.ports.mock_scheduler_adapter import MockSchedulerAdapter


class TestMockSchedulerAdapter:
    """Tests for MockSchedulerAdapter."""

    def test_start_sets_running(self):
        adapter = MockSchedulerAdapter()
        adapter.start()
        assert adapter._running is True

    def test_shutdown_sets_not_running(self):
        adapter = MockSchedulerAdapter()
        adapter.start()
        adapter.shutdown()
        assert adapter._running is False

    def test_add_job(self):
        adapter = MockSchedulerAdapter()
        job_id = adapter.add_job(lambda: None, "cron", "job1", hour=12)
        assert job_id == "job1"
        assert "job1" in adapter.get_jobs()

    def test_remove_job(self):
        adapter = MockSchedulerAdapter()
        adapter.add_job(lambda: None, "cron", "job1")
        adapter.remove_job("job1")
        assert "job1" not in adapter.get_jobs()

    def test_remove_job_not_found_raises(self):
        adapter = MockSchedulerAdapter()
        with pytest.raises(KeyError):
            adapter.remove_job("nonexistent")

    def test_get_jobs_empty(self):
        adapter = MockSchedulerAdapter()
        assert adapter.get_jobs() == []

    def test_get_jobs_multiple(self):
        adapter = MockSchedulerAdapter()
        adapter.add_job(lambda: None, "cron", "job1")
        adapter.add_job(lambda: None, "cron", "job2")
        assert set(adapter.get_jobs()) == {"job1", "job2"}
