import logging
import os
import tempfile
import uuid

from src.utils.logger import _loggers, get_logger, setup_logger


def _close_handlers(logger: logging.Logger) -> None:
    """Close all handlers attached to a logger."""
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)


def _unique_name() -> str:
    """Return a unique logger name to avoid cross-test cache collisions."""
    return "test_logger_" + uuid.uuid4().hex


class TestSetupLogger:
    """Tests for setup_logger."""

    def test_setup_logger_returns_logger(self):
        name = _unique_name()
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "test.log")
            try:
                logger = setup_logger(name, log_path)
                assert isinstance(logger, logging.Logger)
            finally:
                _close_handlers(logger)
                _loggers.pop(name, None)

    def test_setup_logger_has_file_handler(self):
        name = _unique_name()
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "test.log")
            try:
                logger = setup_logger(name, log_path)
                has_file = any(
                    isinstance(h, logging.FileHandler) for h in logger.handlers
                )
                assert has_file is True
            finally:
                _close_handlers(logger)
                _loggers.pop(name, None)

    def test_setup_logger_has_console_handler(self):
        name = _unique_name()
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "test.log")
            try:
                logger = setup_logger(name, log_path)
                has_console = any(
                    isinstance(h, logging.StreamHandler)
                    and not isinstance(h, logging.FileHandler)
                    for h in logger.handlers
                )
                assert has_console is True
            finally:
                _close_handlers(logger)
                _loggers.pop(name, None)


class TestGetLogger:
    """Tests for get_logger."""

    def test_get_logger_returns_same_instance(self):
        name = _unique_name()
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "test.log")
            try:
                logger1 = setup_logger(name, log_path)
                logger2 = get_logger(name)
                assert logger1 is logger2
            finally:
                _close_handlers(logger1)
                _loggers.pop(name, None)


class TestLoggerWritesToFile:
    """Tests that log records are persisted to the log file."""

    def test_logger_writes_to_file(self):
        name = _unique_name()
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "test_writes.log")
            try:
                logger = setup_logger(name, log_path)
                logger.info("hello from test")
                for handler in logger.handlers:
                    handler.flush()
                with open(log_path, "r", encoding="utf-8") as f:
                    content = f.read()
                assert "hello from test" in content
            finally:
                _close_handlers(logger)
                _loggers.pop(name, None)
