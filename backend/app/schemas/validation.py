"""app/schemas/validation.py — Validation queue, run request, and flag schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.validation import FlagSeverity, FlagType


class ValidationQueueItem(BaseModel):
    parcel_id: str
    workflow_status: str
    flag_count: int
    oldest_flag_at: datetime | None = None


class ValidationQueueResponse(BaseModel):
    """GET /v1/validations/queue."""
    items: list[ValidationQueueItem]
    next_cursor: str | None = None


class ValidationRunRequest(BaseModel):
    """POST /v1/validations/run."""
    parcel_ids: list[str] = Field(
        min_length=1, max_length=50,
        description="IDs of parcels to validate",
    )


class ValidationRunResponse(BaseModel):
    job_id: str
    status: str = "queued"
    parcel_count: int


class FlagResponse(BaseModel):
    """Single validation flag on a parcel."""
    flag_id: str
    parcel_id: str
    flag_type: FlagType
    severity: FlagSeverity
    description: str | None = None
    resolved: bool
    created_at: datetime
    resolved_at: datetime | None = None


class ParcelFlagsResponse(BaseModel):
    """GET /v1/parcels/{parcel_id}/flags."""
    parcel_id: str
    flags: list[FlagResponse]
    total: int
