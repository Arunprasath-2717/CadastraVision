"""
app/models/audit.py
────────────────────
AuditLogEntry — immutable audit trail per PRD terminology.

INTEGRATION BOUNDARY (Prajith's workstream):
  The ``prev_hash`` and ``entry_hash`` columns are reserved for
  Prajith's hash-chain implementation. They are nullable in Phase 2.
  Phase 3 will wire the AuditChainService to populate these fields.

APPEND-ONLY: Rows in this table are NEVER updated or deleted by
application code. created_at is the definitive event timestamp.
"""

from __future__ import annotations

import enum

from sqlalchemy import Enum, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class AuditAction(str, enum.Enum):
    CREATE = "create"
    EDIT = "edit"
    APPROVE = "approve"
    REJECT = "reject"
    SYNC = "sync"
    VIEW = "view"
    LOGIN = "login"
    LOGOUT = "logout"
    CHANGE_DETECTED = "change_detected"
    CHANGE_APPROVED = "change_approved"
    CHANGE_REJECTED = "change_rejected"
    EXPORT_GENERATED = "export_generated"


class AuditLogEntry(UUIDMixin, TimestampMixin, Base):
    """Immutable audit log entry. Append-only — never update or delete."""

    __tablename__ = "audit_log_entries"

    # Actor
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True
    )

    # Subject (entity-agnostic — no FK to allow hard-deleted entities)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Event
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, values_callable=lambda e: [m.value for m in e], native_enum=False),
        nullable=False, index=True,
    )
    diff_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # Prajith's hash-chain fields (nullable until Phase 3 integration)
    # INTEGRATION STUB: populated by AuditChainService
    prev_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entry_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationship
    user: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys=[user_id], back_populates="audit_entries", lazy="select"
    )

    __table_args__ = (
        Index("ix_audit_entity", "entity_type", "entity_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLogEntry id={self.id!r} action={self.action!r} "
            f"entity={self.entity_type}/{self.entity_id}>"
        )
