"""
app/models/validation.py
─────────────────────────
ValidationFlag — topology or confidence issue on a Parcel.

Created by the topology validation service (Arun's workstream).
The backend creates the schema and integration boundary; Arun's
algorithms populate flags via the TopologyValidationService interface.
"""

from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class FlagType(str, enum.Enum):
    OVERLAP = "overlap"
    GAP = "gap"
    SELF_INTERSECTION = "self_intersection"
    CONFIDENCE_LOW = "confidence_low"
    BOUNDARY_MISMATCH = "boundary_mismatch"
    OTHER = "other"


class FlagSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationFlag(UUIDMixin, TimestampMixin, Base):
    """Validation issue flagged against a Parcel by the topology pipeline."""

    __tablename__ = "validation_flags"

    parcel_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("parcels.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    flag_type: Mapped[FlagType] = mapped_column(
        Enum(FlagType, values_callable=lambda e: [m.value for m in e], native_enum=False),
        nullable=False, index=True,
    )
    severity: Mapped[FlagSeverity] = mapped_column(
        Enum(FlagSeverity, values_callable=lambda e: [m.value for m in e], native_enum=False),
        default=FlagSeverity.WARNING,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    parcel: Mapped["Parcel"] = relationship(  # noqa: F821
        "Parcel", back_populates="flags", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<ValidationFlag id={self.id!r} type={self.flag_type!r} severity={self.severity!r}>"
