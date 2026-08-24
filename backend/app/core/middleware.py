"""
app/core/middleware.py
────────────────────────
Production request correlation & observability middleware.

Every HTTP request receives a unique X-Request-ID for request correlation
across logs, service layers, and client responses.
"""

from __future__ import annotations

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger("cadastravision.middleware")


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware attaching a unique X-Request-ID header to incoming HTTP requests
    and measuring end-to-end request latency.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract existing request ID or generate new UUID4
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        start_time = time.perf_counter()
        
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Request failed: method={request.method} path={request.url.path} "
                f"request_id={request_id} duration_ms={duration_ms:.2f} error={exc}"
            )
            raise exc

        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        
        # Operational logging (credentials/tokens automatically excluded)
        logger.info(
            f"HTTP {response.status_code} {request.method} {request.url.path} "
            f"request_id={request_id} duration_ms={duration_ms:.2f}"
        )
        return response
