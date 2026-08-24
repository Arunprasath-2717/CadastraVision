"""
app/models/sync.py
───────────────────
SyncAction — persistent idempotency record for offline sync.

Every action submitted via POST /v1/parcels/sync is recorded here
using the client-supplied ``client_action_id``. Replayed requests
return the original result without re-executing the action.

This fulfils the PRD idempotency requirement and survives application
restarts (database-backed, not in-memory).
"""

from __future__ import annotations

import enum

from sqlalchemy import Enum, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class SyncActionStatus(str, enum.Enum):
    APPLIED = "applied"
    CONFLICT = "conflict"
    FAILED = "failed"


class SyncAction(UUIDMixin, TimestampMixin, Base):
    """Persistent idempotency record for an offline sync action."""

    __tablename__ = "sync_actions"

    # Client-generated unique identifier — idempotency key
    client_action_id: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, index=True
    )
    action_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Original request payload (stored for idempotent replay)
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    status: Mapped[SyncActionStatus] = mapped_column(
        Enum(SyncActionStatus, values_callable=lambda e: [m.value for m in e], native_enum=False),
        nullable=False,
        index=True,
    )

    # Stored result — returned on replay without re-executing
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Conflict details when status == CONFLICT
    conflict_detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    conflict_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SyncAction client_id={self.client_action_id!r} status={self.status!r}>"
