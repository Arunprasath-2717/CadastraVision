"""
app/routers/health.py
──────────────────────
Liveness and Readiness health-check endpoints for orchestration engines (Kubernetes, Docker, ECS).

GET /health → Lightweight liveness probe
GET /health/live → Explicit liveness status
GET /health/ready → Readiness probe checking database connectivity
"""

from __future__ import annotations

from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check liveness probe")
async def health() -> Dict[str, str]:
    """
    Lightweight liveness probe.
    """
    return {"status": "ok", "service": "cadastravision-backend"}


@router.get("/health/live", summary="Liveness probe")
async def liveness() -> Dict[str, str]:
    """
    Explicit liveness probe for container orchestrators.
    """
    return {"status": "ok", "liveness": "pass", "service": "cadastravision-backend"}


@router.get("/health/ready", summary="Readiness probe")
async def readiness(db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """
    Readiness probe verifying database connectivity and session health.
    """
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "readiness": "pass",
            "database": "connected",
            "service": "cadastravision-backend",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "degraded",
                "readiness": "fail",
                "database": "disconnected",
                "error": "Database connectivity check failed",
            },
        )
