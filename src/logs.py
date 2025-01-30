"""Logging configuration for the application."""

import logging
import os
import sys

from loguru import logger

from src.settings import settings

# Log file path
LOG_PATH = os.path.join(settings.root_path, "logs")
LOG_FILE = os.path.join(LOG_PATH, settings.LOG_FILE)

# Ensure logs directory exists at the root level
os.makedirs(LOG_PATH, exist_ok=True)

# Remove default handlers to prevent duplicate logs
logger.remove()

# Console logging (stdout for Docker logs)
logger.add(sys.stdout, format="{time} - {level} - {message}", level=settings.LOG_LEVEL)

# File logging (persistent logs)
logger.add(
    LOG_FILE,
    format="{time} - {level} - {message}",
    level=settings.LOG_LEVEL,
    rotation=settings.LOG_ROTATION,
)


# Intercept Python's logging module (Uvicorn, FastAPI logs)
class InterceptHandler(logging.Handler):
    """Intercepts `logging` logs and redirects to `loguru`."""

    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = "INFO"
        logger.log(level, record.getMessage())


def setup_logging():
    """Redirects FastAPI & Uvicorn logs to `loguru`."""

    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO)

    # Redirect Uvicorn & FastAPI logs
    for log_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"]:
        logging.getLogger(log_name).handlers = [InterceptHandler()]


setup_logging()
