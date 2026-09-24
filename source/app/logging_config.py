"""Logging setup: console output plus a rotating JSON log file."""

import logging
import logging.config
import os
from pathlib import Path

from app.config import get_settings

LOG_FILE = Path(os.getenv("APP_LOG_FILE") or get_settings().app_log_file)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        },
        "file": {
            "format": (
                '{"time": "%(asctime)s", "level": "%(levelname)s", '
                '"logger": "%(name)s", "message": "%(message)s"}'
            ),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "file",
            "filename": str(LOG_FILE),
            "maxBytes": 5_000_000,
            "backupCount": 3,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "app": {
            "level": "INFO",
            "propagate": False,
            "handlers": ["console", "file"],
        },
        "uvicorn.access": {
            "level": "INFO",
            "propagate": False,
            "handlers": ["console", "file"],
        },
    },
    "root": {
        "level": "WARNING",
        "handlers": ["console"],
    },
}


def _log_file_is_writable() -> bool:
    """Check that the log file's directory can actually be written to."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8"):
            pass
        return True
    except OSError:
        return False


def setup_logging() -> None:
    """Configure application and Uvicorn log handlers.

    Falls back to console-only logging if the log file location is not
    writable (e.g. read-only volume or permission issue in a container).
    """
    config = LOGGING_CONFIG
    if not _log_file_is_writable():
        config = {**LOGGING_CONFIG, "handlers": dict(LOGGING_CONFIG["handlers"])}
        config["handlers"].pop("file", None)
        for logger_cfg in config["loggers"].values():
            logger_cfg["handlers"] = [
                h for h in logger_cfg["handlers"] if h != "file"
            ]
    logging.config.dictConfig(config)
