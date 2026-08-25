"""
app/models/conflict.py
───────────────────────
Conflict — spatial or data conflict between two Parcels.

Created by Arun's topology validation (overlap/gap detection).
Backend owns the persistence and API; Arun's algorithms identify
the conflicts via the TopologyValidationService integration boundary.
"""

from __future__ import annotations

import enum

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ConflictType(str, enum.Enum):
    OVERLAP = "overlap"
    GAP = "gap"
    BOUNDARY_MISMATCH = "boundary_mismatch"
    ATTRIBUTE_CONFLICT = "attribute_conflict"
    OTHER = "other"


class ConflictStatus(str, enum.Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class Conflict(UUIDMixin, TimestampMixin, Base):
    """Spatial or data conflict between two parcels."""

    __tablename__ = "conflicts"

    parcel_a_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("parcels.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    parcel_b_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("parcels.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    conflict_type: Mapped[ConflictType] = mapped_column(
        Enum(ConflictType, values_callable=lambda e: [m.value for m in e], native_enum=False),
        nullable=False, index=True,
    )
    status: Mapped[ConflictStatus] = mapped_column(
        Enum(ConflictStatus, values_callable=lambda e: [m.value for m in e], native_enum=False),
        default=ConflictStatus.OPEN,
        nullable=False, index=True,
    )
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolved_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    parcel_a: Mapped["Parcel"] = relationship(  # noqa: F821
        "Parcel", foreign_keys=[parcel_a_id], back_populates="conflicts_as_a", lazy="select"
    )
    parcel_b: Mapped["Parcel"] = relationship(  # noqa: F821
        "Parcel", foreign_keys=[parcel_b_id], back_populates="conflicts_as_b", lazy="select"
    )
    resolved_by: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys=[resolved_by_id], lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Conflict id={self.id!r} type={self.conflict_type!r} status={self.status!r}>"
