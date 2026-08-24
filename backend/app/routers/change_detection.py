"""app/routers/change_detection.py — POST /v1/change-detection/run, GET /v1/change-detection/{job_id}."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter

from app.schemas.change_detection import (
    ChangeDetectionJobResponse,
    ChangeDetectionRunRequest,
    ChangeDetectionRunResponse,
)

router = APIRouter(prefix="/v1/change-detection", tags=["Change Detection"])

_NOW = lambda: datetime.now(timezone.utc)  # noqa: E731


@router.post(
    "/run",
    response_model=ChangeDetectionRunResponse,
    summary="Run change detection",
    description=(
        "Compare two imagery tiles to detect land-use changes. "
        "**STUB** — Akshaya's pipeline (Phase 3)."
    ),
)
async def run_change_detection(body: ChangeDetectionRunRequest) -> ChangeDetectionRunResponse:
    return ChangeDetectionRunResponse(job_id=str(uuid.uuid4()))


@router.get(
    "/{job_id}",
    response_model=ChangeDetectionJobResponse,
    summary="Get change detection job status",
    description="Poll the status of a change detection job. **STUB** — Phase 3.",
)
async def get_change_detection_job(job_id: str) -> ChangeDetectionJobResponse:
    return ChangeDetectionJobResponse(job_id=job_id, status="queued", created_at=_NOW())
