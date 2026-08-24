"""
app/core/rate_limit.py
───────────────────────
In-memory sliding window API rate-limiter for abuse protection.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List
from fastapi import HTTPException, Request, status


class RateLimiter:
    """
    Sliding-window rate limiter enforcing request rate caps per IP address.
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)

    async def __call__(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()

        # Clean timestamps older than window
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip] if now - ts < self.window_seconds
        ]

        if len(self._requests[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too Many Requests: Rate limit exceeded. Please try again later.",
                headers={"Retry-After": str(self.window_seconds)},
            )

        self._requests[client_ip].append(now)


# Standard rate limiters for sensitive endpoints
auth_rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
upload_rate_limiter = RateLimiter(max_requests=30, window_seconds=60)
export_rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
