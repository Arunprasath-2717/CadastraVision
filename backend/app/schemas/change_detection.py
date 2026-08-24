"""app/schemas/change_detection.py — Change detection run and job schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ChangeDetectionRunRequest(BaseModel):
    """POST /v1/change-detection/run."""
    tile_id_before: str = Field(description="Baseline imagery tile ID")
    tile_id_after: str = Field(description="New imagery tile ID to compare against")
    area_of_interest_wkt: str | None = Field(
        default=None,
        description="Optional WKT polygon to restrict detection area",
    )


class ChangeDetectionRunResponse(BaseModel):
    job_id: str
    status: str = "queued"
    message: str = "Change detection job queued."


class ChangeDetectionJobResponse(BaseModel):
    """GET /v1/change-detection/{job_id}."""
    job_id: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    changes_detected: int | None = None
    error_message: str | None = None
