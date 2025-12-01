import logging
import os
import time
from datetime import datetime
from functools import wraps
from logging.config import dictConfig
from pathlib import Path
from typing import Any

from empatia.settings import BASE_PATH

LOG_FILENAME = f"empatia_model_{datetime.now().strftime('%Y_%m_%d_%H_%M')}.log"
LOCAL_LOG_DIR = Path(BASE_PATH) / "log"
LOCAL_LOG_PATH = Path(LOCAL_LOG_DIR) / LOG_FILENAME

if not os.path.exists(LOCAL_LOG_DIR):
    os.makedirs(LOCAL_LOG_DIR)


class LevelFilter(logging.Filter):
    """Filter records by exact level or minimum level.

    Parameters passed via dictConfig must be JSON-serializable, so levels
    are passed as integers (e.g. 10 for DEBUG, 20 for INFO).
    """

    def __init__(self, level: int = logging.INFO, only: bool = False):
        super().__init__()
        self.level = int(level)
        self.only = bool(only)

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - trivial
        if self.only:
            return record.levelno == self.level
        return record.levelno >= self.level


LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "debug": {
            "format": "🔵 - %(levelname)s %(processName)s(pid=%(process)d) - %(module)s:%(lineno)d - %(message)s"
        },
        "standard": {
            "format": "🟢 - %(levelname)s - "
            "%(module)s:%(lineno)d - %(message)s"
        },
        "verbose": {
            "format": "🟢 - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(funcName)s() - %(message)s"
        },
        "warning": {
            "format": "🟡 - %(levelname)s - "
            "%(module)s:%(lineno)d - %(message)s"
        },
        "error": {
            "format": "🔴 - %(levelname)s - "
            "%(module)s:%(lineno)d - %(message)s"
        },
    },
    "handlers": {
        "console_info": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
        },
        "console_warning": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "warning",
        },
        "file_debug": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "debug",
            "filename": str(LOCAL_LOG_PATH),
            "mode": "a",
        },
        "file_error": {
            "class": "logging.FileHandler",
            "level": "ERROR",
            "formatter": "error",
            "filename": str(LOCAL_LOG_PATH),
            "mode": "a",
        },
    },
    "loggers": {
        "empatia": {
            "handlers": ["console_info", "console_warning", "file_debug", "file_error"],
            "level": "DEBUG",
            "propagate": False,
        }
    },
}

dictConfig(LOGGING)
logger = logging.getLogger("empatia")

# Attach LevelFilter instances programmatically to avoid resolution issues
# when dictConfig attempts to import the filter factory while this module
# is still being initialized.
debug_filter = LevelFilter(logging.DEBUG, only=True)
info_filter = LevelFilter(logging.INFO, only=True)
warning_filter = LevelFilter(logging.WARNING, only=True)
error_filter = LevelFilter(logging.ERROR, only=True)

for h in logger.handlers:
    # prefer explicit level checks to identify handlers
    try:
        lvl = h.level
    except Exception:
        lvl = None

    if isinstance(h, logging.FileHandler) and lvl == logging.DEBUG:
        h.addFilter(debug_filter)
    elif isinstance(h, logging.FileHandler) and lvl == logging.ERROR:
        h.addFilter(error_filter)
    elif isinstance(h, logging.StreamHandler) and lvl == logging.INFO:
        h.addFilter(info_filter)
    elif isinstance(h, logging.StreamHandler) and lvl == logging.WARNING:
        h.addFilter(warning_filter)


def timed(func: Any) -> Any:
    """This decorator prints the execution time for the decorated function."""

    @wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        start = time.time()
        result = func(self, *args, **kwargs)
        end = time.time()
        logger.info(f"{self.__class__.__name__} ran in {round(end - start, 4)}s")
        return result

    return wrapper
