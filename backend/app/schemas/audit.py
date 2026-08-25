"""app/schemas/audit.py — Audit log entry, verify, and export schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.audit import AuditAction


class AuditEntryResponse(BaseModel):
    entry_id: str
    entity_type: str
    entity_id: str
    action: AuditAction
    user_id: str | None = None
    diff_json: dict | None = None
    ip_address: str | None = None
    created_at: datetime
    # Hash-chain fields — populated by Prajith's module (nullable in Phase 2)
    entry_hash: str | None = Field(
        default=None,
        description="SHA-256 hash of this entry (Prajith's chain — stub in Phase 2)",
    )


class AuditTrailResponse(BaseModel):
    """GET /v1/audit/{parcel_id}."""
    parcel_id: str
    entries: list[AuditEntryResponse]
    total: int


class AuditVerifyResponse(BaseModel):
    """GET /v1/audit/verify/{parcel_id}."""
    parcel_id: str
    chain_valid: bool
    entry_count: int
    # INTEGRATION STUB — Prajith's hash-chain verification
    verification_note: str = "Hash-chain verification: integration stub (Phase 2)"


class AuditExportResponse(BaseModel):
    """GET /v1/audit/export/{batch_id}."""
    batch_id: str
    download_url: str | None = None
    status: str
    entry_count: int | None = None
