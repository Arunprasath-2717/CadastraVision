"""
app/routers/health.py
──────────────────────
Health-check endpoint.

GET /health → {"status": "ok", "service": "cadastravision-backend"}
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check")
async def health() -> dict[str, str]:
    """
    Lightweight liveness probe.

    Returns a static JSON payload that load-balancers and orchestration
    platforms (Kubernetes, ECS, Railway, etc.) can poll.
    """
    return {"status": "ok", "service": "cadastravision-backend"}
