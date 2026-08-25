"""app/schemas/conflict.py — Conflict list and resolve schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.conflict import ConflictStatus, ConflictType


class ConflictSummary(BaseModel):
    conflict_id: str
    parcel_a_id: str
    parcel_b_id: str
    conflict_type: ConflictType
    status: ConflictStatus
    created_at: datetime
    resolved_at: datetime | None = None


class ConflictsResponse(BaseModel):
    """GET /v1/conflicts."""
    items: list[ConflictSummary]
    next_cursor: str | None = None


class ResolveConflictRequest(BaseModel):
    """POST /v1/conflicts/{conflict_id}/resolve."""
    resolution: str = Field(description="keep_a | keep_b | merge | ignore")
    notes: str | None = None


class ResolveConflictResponse(BaseModel):
    conflict_id: str
    status: ConflictStatus
    message: str
