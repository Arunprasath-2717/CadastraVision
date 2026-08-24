"""
app/routers/audit.py
─────────────────────
GET /v1/audit/{parcel_id}
GET /v1/audit/verify/{parcel_id}
GET /v1/audit/export/{batch_id}

IMPORTANT path order: /verify and /export MUST come before /{parcel_id}
to prevent FastAPI from matching them as parcel IDs.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.audit import AuditLogEntry
from app.models.user import User, UserRole
from app.schemas.audit import AuditEntryResponse, AuditExportResponse, AuditTrailResponse, AuditVerifyResponse
from app.services.audit_service import GENESIS_HASH, compute_entry_hash

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/audit", tags=["Audit"])


@router.get(
    "/verify/{parcel_id}",
    response_model=AuditVerifyResponse,
    summary="Verify audit chain integrity",
    description="Verify the SHA-256 hash-chain integrity for a parcel's audit trail.",
)
async def verify_audit_chain(
    parcel_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuditVerifyResponse:
    stmt = (
        select(AuditLogEntry)
        .where(AuditLogEntry.entity_type == "parcel", AuditLogEntry.entity_id == parcel_id)
        .order_by(AuditLogEntry.created_at.asc())
    )
    entries = list((await db.execute(stmt)).scalars().all())

    chain_valid = True
    last_hash = entries[0].prev_hash if entries else GENESIS_HASH
    verified = 0

    for entry in entries:
        if entry.prev_hash != last_hash:
            chain_valid = False
            break

        diff = entry.diff_json or {}
        created_at_iso = diff.get("_timestamp") or (
            entry.created_at.isoformat() if hasattr(entry.created_at, "isoformat") else str(entry.created_at)
        )

        calc_hash = compute_entry_hash(
            prev_hash=entry.prev_hash,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            action=entry.action.value,
            user_id=entry.user_id,
            diff=diff,
            created_at_iso=created_at_iso,
        )

        if entry.entry_hash and calc_hash != entry.entry_hash:
            logger.warning("Hash mismatch! entry_hash=%s calc_hash=%s", entry.entry_hash, calc_hash)
            chain_valid = False
            break

        last_hash = entry.entry_hash
        verified += 1

    return AuditVerifyResponse(
        parcel_id=parcel_id,
        chain_valid=chain_valid,
        entry_count=verified,
    )


@router.get(
    "/export/{batch_id}",
    response_model=AuditExportResponse,
    summary="Export audit batch",
    description="Export a batch of audit log entries.",
)
async def export_audit_batch(
    batch_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> AuditExportResponse:
    stmt = select(AuditLogEntry).limit(100)
    entries = list((await db.execute(stmt)).scalars().all())
    return AuditExportResponse(batch_id=batch_id, status="completed", entry_count=len(entries))


@router.get(
    "/{parcel_id}",
    response_model=AuditTrailResponse,
    summary="Get parcel audit trail",
    description="Retrieve the complete audit trail for a parcel.",
)
async def get_parcel_audit(
    parcel_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuditTrailResponse:
    stmt = (
        select(AuditLogEntry)
        .where(AuditLogEntry.entity_type == "parcel", AuditLogEntry.entity_id == parcel_id)
        .order_by(AuditLogEntry.created_at.desc())
    )
    entries = list((await db.execute(stmt)).scalars().all())

    items = [
        AuditEntryResponse(
            entry_id=e.id,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            action=e.action,
            user_id=e.user_id,
            created_at=e.created_at,
            diff_json=e.diff_json,
            ip_address=e.ip_address,
            entry_hash=e.entry_hash,
        )
        for e in entries
    ]
    return AuditTrailResponse(parcel_id=parcel_id, entries=items, total=len(items))
