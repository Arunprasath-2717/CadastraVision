"""app/schemas/parcel.py — Parcel list, detail, edit, approve/reject, and sync schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.parcel import ParcelWorkflowStatus


class ParcelSummary(BaseModel):
    """Compact parcel representation for list endpoints."""
    parcel_id: str
    workflow_status: ParcelWorkflowStatus
    confidence: float | None = None
    zone: str | None = None
    jurisdiction: str | None = None
    created_at: datetime


class ParcelDetail(BaseModel):
    """Full parcel representation for GET /v1/parcels/{parcel_id}."""
    parcel_id: str
    geometry_wkt: str | None = None
    source_tile_id: str | None = None
    confidence: float | None = None
    zone: str | None = None
    jurisdiction: str | None = None
    workflow_status: ParcelWorkflowStatus
    reviewed_by_id: str | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class EditOperation(BaseModel):
    """A single geometry edit operation."""
    operation: str = Field(description="vertex_edit | split | merge")
    payload: dict[str, Any] = Field(description="Operation-specific geometry payload")


class ParcelEditRequest(BaseModel):
    """POST /v1/parcels/{parcel_id}/edit."""
    idempotency_key: str | None = Field(
        default=None,
        description="Client-generated key to make this edit idempotent",
    )
    edit: EditOperation
    notes: str | None = None


class ParcelEditResponse(BaseModel):
    parcel_id: str
    workflow_status: ParcelWorkflowStatus
    message: str


class ApproveRequest(BaseModel):
    """POST /v1/parcels/{parcel_id}/approve."""
    notes: str | None = None


class RejectRequest(BaseModel):
    """POST /v1/parcels/{parcel_id}/reject."""
    reason: str = Field(description="Mandatory reason for rejection")


class ParcelActionResponse(BaseModel):
    parcel_id: str
    workflow_status: ParcelWorkflowStatus
    message: str
    reviewed_at: datetime | None = None


# ── Offline Sync ──────────────────────────────────────────────────────────────

class SyncActionItem(BaseModel):
    """A single action in a sync batch."""
    client_action_id: str = Field(
        description="Client-generated unique identifier for idempotency"
    )
    action_type: str = Field(description="edit | approve | reject | create")
    parcel_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class SyncRequest(BaseModel):
    """POST /v1/parcels/sync — offline action batch."""
    actions: list[SyncActionItem] = Field(min_length=1, max_length=100)


class SyncResultItem(BaseModel):
    client_action_id: str
    status: str = Field(description="applied | conflict | failed")
    parcel_id: str | None = None
    conflict_detail: dict | None = None
    error: str | None = None


class SyncResponse(BaseModel):
    """Response from POST /v1/parcels/sync."""
    applied: int
    conflicts: int
    failed: int
    results: list[SyncResultItem]
