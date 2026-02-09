"""
Performance monitoring middleware for FastAPI.

Tracks request durations and logs slow endpoints when LOG_LEVEL=DEBUG.
Adds X-Response-Time header to all responses for monitoring.
"""

import logging
import os
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track and log API request performance.

    Features:
    - Adds X-Response-Time header to all responses
    - Logs request durations with color-coded emojis (only in DEBUG mode)
    - Skips health check endpoints from detailed logging
    """

    def __init__(self, app, log_enabled: bool = None):
        """
        Initialize performance monitoring middleware.

        Args:
            app: FastAPI application instance
            log_enabled: Whether to log performance metrics (defaults to LOG_LEVEL=DEBUG)
        """
        super().__init__(app)
        if log_enabled is None:
            log_level = os.getenv("LOG_LEVEL", "INFO").upper()
            log_enabled = log_level == "DEBUG"
        self.log_enabled = log_enabled

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and track performance.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            Response with X-Response-Time header added
        """
        # Skip tracking for health check endpoints
        skip_logging = request.url.path in ["/health", "/health/detailed"]

        start_time = time.time()

        try:
            # Process the request
            response = await call_next(request)
        except Exception as exc:
            # Still log the timing even if request failed
            duration_ms = (time.time() - start_time) * 1000
            if self.log_enabled and not skip_logging:
                logger.error(
                    "🐌 Request failed: %s %s - %.2fms - Error: %s",
                    request.method,
                    request.url.path,
                    duration_ms,
                    str(exc),
                )
            raise

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Add X-Response-Time header
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        # Log performance metrics (only in DEBUG mode and not for health checks)
        if self.log_enabled and not skip_logging:
            self._log_performance(request, duration_ms)

        return response

    def _log_performance(self, request: Request, duration_ms: float) -> None:
        """
        Log request performance with color-coded emoji indicators.

        Performance levels:
        - ⚡ Fast: < 100ms
        - ✅ Good: 100-500ms
        - ⚠️  Slow: 500-2000ms
        - 🐌 Very slow: > 2000ms

        Args:
            request: The HTTP request
            duration_ms: Request duration in milliseconds
        """
        # Choose emoji based on duration
        if duration_ms < 100:
            emoji = "⚡"
            level = "Fast"
        elif duration_ms < 500:
            emoji = "✅"
            level = "Good"
        elif duration_ms < 2000:
            emoji = "⚠️"
            level = "Slow"
        else:
            emoji = "🐌"
            level = "Very slow"

        # Build query params string if present
        query_params = ""
        if request.query_params:
            query_params = f" - Params: {dict(request.query_params)}"

        # Log with appropriate level based on duration
        log_message = (
            f"{emoji} {level}: {request.method} {request.url.path} - "
            f"{duration_ms:.2f}ms{query_params}"
        )

        if duration_ms >= 2000:
            logger.warning(log_message)
        else:
            logger.debug(log_message)
