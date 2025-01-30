"""
Custom middlewares.
"""

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.logs import logger


class LogRequestsMiddleware(BaseHTTPMiddleware):
    """Middleware to log incoming requests and outgoing responses."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        logger.info(f"Incoming request: {request.method} {request.url}")
        response = await call_next(request)
        duration = time.time() - start_time
        logger.info(
            f"Response status: {response.status_code}, Response time: {duration:.2f} seconds"
        )
        return response
