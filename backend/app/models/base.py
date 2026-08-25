"""
app/models/base.py
───────────────────
Shared SQLAlchemy ORM mixins and the project-wide declarative base.

Design decisions
────────────────
* **UUID primary keys** — portable between SQLite (stored as CHAR(32)) and
  PostgreSQL (native UUID column). Generated server-side via Python's
  ``uuid.uuid4()`` so IDs are available before the row is flushed.

* **Timestamps** — ``created_at`` is set once on insert; ``updated_at`` is
  refreshed automatically on every UPDATE using SQLAlchemy's ``onupdate``
  hook. Both are timezone-aware UTC.

* **Soft delete** — ``deleted_at`` is NULL for live rows and set to the
  deletion timestamp for "deleted" rows. Hard deletes are avoided for
  auditing purposes. Callers must filter ``deleted_at IS NULL`` explicitly;
  a future phase will add a global query filter helper.

Usage
─────
    from app.models.base import Base, TimestampMixin, SoftDeleteMixin, UUIDMixin

    class MyModel(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
        __tablename__ = "my_table"
        name: Mapped[str] = mapped_column(String(255))
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


# ── Declarative base ──────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """Project-wide SQLAlchemy declarative base.

    Imported and re-exported here so all models share one metadata object.
    ``app.core.database`` imports *this* Base so Alembic sees every table.
    """


# ── Mixins ────────────────────────────────────────────────────────────────────

class UUIDMixin:
    """Add a UUID primary key column named ``id``."""

    id: Mapped[str] = mapped_column(
        # Store as CHAR(32) for SQLite; PostgreSQL uses UUID natively
        # via dialect-specific type coercion at migration time.
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        sort_order=-100,
    )


class TimestampMixin:
    """Add ``created_at`` and ``updated_at`` audit timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        nullable=False,
        sort_order=90,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        server_default=func.now(),
        nullable=False,
        sort_order=91,
    )


class SoftDeleteMixin:
    """
    Add a ``deleted_at`` column for soft deletes.

    A NULL value means the row is active.
    A non-NULL value contains the UTC timestamp of deletion.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        sort_order=99,
    )

    @property
    def is_deleted(self) -> bool:
        """Return True if this record has been soft-deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark this record as deleted without removing the database row."""
        self.deleted_at = _utcnow()
