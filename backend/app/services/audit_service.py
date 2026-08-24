"""
app/services/audit_service.py
──────────────────────────────
Audit event recording service with cryptographic SHA-256 hash chaining.

INTEGRATION BOUNDARY (Prajith's workstream):
  Computes prev_hash and entry_hash for every AuditLogEntry to form
  a tamper-evident hash chain across all system actions.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditAction, AuditLogEntry

logger = logging.getLogger(__name__)

GENESIS_HASH = "0" * 64


def compute_entry_hash(
    *,
    prev_hash: str,
    entity_type: str,
    entity_id: str,
    action: str,
    user_id: str | None = None,
    diff: dict[str, Any] | None = None,
    created_at_iso: str,
) -> str:
    """Compute deterministic SHA-256 hash for an audit log entry."""
    payload = {
        "prev_hash": prev_hash,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "user_id": user_id or "",
        "diff": diff or {},
        "created_at": created_at_iso,
    }
    serialized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class AuditEventService:
    """Records immutable audit events with SHA-256 hash-chaining."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_last_entry_hash(self) -> str:
        """Fetch the entry_hash of the most recent audit log entry."""
        stmt = select(AuditLogEntry.entry_hash).order_by(AuditLogEntry.created_at.desc()).limit(1)
        res = await self.db.execute(stmt)
        last_hash = res.scalar_one_or_none()
        return last_hash or GENESIS_HASH

    async def record(
        self,
        *,
        entity_type: str,
        entity_id: str,
        action: AuditAction,
        user_id: str | None = None,
        diff: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLogEntry:
        """
        Create, hash-chain, and persist an AuditLogEntry record.
        """
        prev_hash = await self._get_last_entry_hash()
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        action_str = action.value if isinstance(action, AuditAction) else str(action)

        diff_data = dict(diff) if diff else {}
        diff_data["_timestamp"] = now_iso

        entry_hash = compute_entry_hash(
            prev_hash=prev_hash,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action_str,
            user_id=user_id,
            diff=diff_data,
            created_at_iso=now_iso,
        )

        entry = AuditLogEntry(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action if isinstance(action, AuditAction) else AuditAction(action),
            user_id=user_id,
            diff_json=diff_data,
            ip_address=ip_address,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
            created_at=now_dt,
        )
        self.db.add(entry)
        await self.db.flush()
        logger.info(
            "Audit record created: action=%s entity=%s/%s hash=%s",
            action, entity_type, entity_id, entry_hash[:12]
        )
        return entry
