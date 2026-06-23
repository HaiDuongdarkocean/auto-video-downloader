"""Logging setup for the video downloader application."""

import logging
import os
from typing import Dict

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_loggers: Dict[str, logging.Logger] = {}


def setup_logger(name: str, log_file: str = "video_downloader.log") -> logging.Logger:
    """Configure and return a logger with file and console handlers.

    Args:
        name: Logger name (typically __name__ of the caller).
        log_file: Path to the log file. A file handler writing UTF-8 is
            attached. Defaults to "video_downloader.log".

    Returns:
        A configured logging.Logger instance at INFO level.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(_LOG_FORMAT)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.propagate = False
    _loggers[name] = logger
    return logger


def get_logger(name: str) -> logging.Logger:
    """Return an existing configured logger or create a new one.

    Args:
        name: Logger name.

    Returns:
        A logging.Logger instance.
    """
    if name in _loggers:
        return _loggers[name]
    return setup_logger(name)
