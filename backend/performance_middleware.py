# file: backend/performance_middleware.py
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from logging_config import get_logger

logger = get_logger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    🧱 LEGO Performance Monitoring Brick
    
    Tracks request execution times and logs them with color-coded emojis:
    - ⚡ < 100ms (Fast - LEGO brick snaps right in!)
    - ✅ 100-500ms (Good - Building smoothly)
    - ⚠️ 500-2000ms (Slow - Assembly taking time)
    - 🐌 > 2000ms (Very slow - Construction delay!)
    
    Only active when LOG_LEVEL=DEBUG
    Skips health check endpoints from detailed logging
    Adds X-Response-Time header to all responses
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and measure execution time."""
        start_time = time.perf_counter()
        
        # Process the request
        response = await call_next(request)
        
        # Calculate execution time in milliseconds
        execution_time_ms = (time.perf_counter() - start_time) * 1000
        
        # Add response time header
        response.headers["X-Response-Time"] = f"{execution_time_ms:.2f}ms"
        
        # Log request timing (only for non-health endpoints in DEBUG mode)
        if not self._is_health_endpoint(request.url.path):
            self._log_request_timing(
                method=request.method,
                path=request.url.path,
                query_params=dict(request.query_params) if request.query_params else None,
                execution_time_ms=execution_time_ms,
                status_code=response.status_code
            )
        
        return response

    def _is_health_endpoint(self, path: str) -> bool:
        """Check if path is a health check endpoint."""
        health_paths = ["/", "/health", "/health/detailed"]
        return path in health_paths

    def _log_request_timing(
        self,
        method: str,
        path: str,
        query_params: dict | None,
        execution_time_ms: float,
        status_code: int
    ) -> None:
        """
        Log request timing with color-coded emoji indicators.
        
        🧱 Building blocks of performance monitoring!
        """
        # Determine emoji based on execution time
        if execution_time_ms < 100:
            emoji = "⚡"
            speed_label = "Fast"
        elif execution_time_ms < 500:
            emoji = "✅"
            speed_label = "Good"
        elif execution_time_ms < 2000:
            emoji = "⚠️"
            speed_label = "Slow"
        else:
            emoji = "🐌"
            speed_label = "Very Slow"
        
        # Format query parameters if present
        query_str = ""
        if query_params:
            query_str = f" | Query: {query_params}"
        
        # Log with detailed context
        logger.debug(
            f"{emoji} {speed_label} | {method} {path}{query_str} | "
            f"{execution_time_ms:.2f}ms | Status: {status_code}"
        )
