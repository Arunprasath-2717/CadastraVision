"""
app/models/parcel.py
─────────────────────
Parcel ORM model — AI-detected cadastral parcel.

This is NOT a survey-record based model. Parcels are created by the
AI segmentation pipeline from imagery tiles, then reviewed and approved
by human validators.

Workflow lifecycle
──────────────────
    draft
      ↓
    validation_pending   (after edit or first creation)
      ↓
    validated            (topology + confidence checks pass)
      ↓
    approved             (human sign-off — eligible for export)

    draft / validation_pending / validated
      ↓
    rejected             (human rejection — excluded from export)

Geometry
────────
Stored as WKT TEXT (portable). PostGIS migration will add a native
geometry column; the WKT column will be kept for backward compatibility
during the transition.

GEOMETRY LIMITATION (documented per PRD):
  SQLite does NOT support PostGIS spatial functions. Spatial queries
  (bounding box intersection, overlap detection) will be added via
  a PostGIS migration. For the pilot, geometry is stored and returned
  as WKT text without server-side spatial indexing.
"""

from __future__ import annotations

import enum

from sqlalchemy import Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class ParcelWorkflowStatus(str, enum.Enum):
    DRAFT = "draft"
    VALIDATION_PENDING = "validation_pending"
    VALIDATED = "validated"
    APPROVED = "approved"
    REJECTED = "rejected"


# Valid state transitions (used by parcel_service.py)
ALLOWED_TRANSITIONS: dict[ParcelWorkflowStatus, set[ParcelWorkflowStatus]] = {
    ParcelWorkflowStatus.DRAFT: {
        ParcelWorkflowStatus.VALIDATION_PENDING,
        ParcelWorkflowStatus.REJECTED,
    },
    ParcelWorkflowStatus.VALIDATION_PENDING: {
        ParcelWorkflowStatus.VALIDATED,
        ParcelWorkflowStatus.REJECTED,
    },
    ParcelWorkflowStatus.VALIDATED: {
        ParcelWorkflowStatus.APPROVED,
        ParcelWorkflowStatus.REJECTED,
        ParcelWorkflowStatus.VALIDATION_PENDING,  # re-validate after edit
    },
    ParcelWorkflowStatus.APPROVED: set(),   # terminal — no further transitions
    ParcelWorkflowStatus.REJECTED: {
        ParcelWorkflowStatus.VALIDATION_PENDING,  # can be reopened for correction
    },
}


class Parcel(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """AI-detected cadastral land parcel."""

    __tablename__ = "parcels"

    # Geometry — WKT polygon string
    # LIMITATION: no spatial index on SQLite; PostGIS migration required for production.
    geometry_wkt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Source provenance
    source_tile_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("imagery_tiles.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0 – 1.0

    # Administrative classification
    zone: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    jurisdiction: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)

    # Workflow state
    workflow_status: Mapped[ParcelWorkflowStatus] = mapped_column(
        Enum(
            ParcelWorkflowStatus,
            values_callable=lambda e: [m.value for m in e],
            native_enum=False,
        ),
        default=ParcelWorkflowStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # Human review
    reviewed_by_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    source_tile: Mapped["ImageryTile | None"] = relationship(  # noqa: F821
        "ImageryTile", back_populates="parcels", lazy="select"
    )
    reviewed_by: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys=[reviewed_by_id], back_populates="reviewed_parcels", lazy="select"
    )
    buildings: Mapped[list["BuildingFootprint"]] = relationship(  # noqa: F821
        "BuildingFootprint", back_populates="parcel", lazy="select"
    )
    flags: Mapped[list["ValidationFlag"]] = relationship(  # noqa: F821
        "ValidationFlag", back_populates="parcel", lazy="select"
    )
    conflicts_as_a: Mapped[list["Conflict"]] = relationship(  # noqa: F821
        "Conflict", foreign_keys="Conflict.parcel_a_id", back_populates="parcel_a", lazy="select"
    )
    conflicts_as_b: Mapped[list["Conflict"]] = relationship(  # noqa: F821
        "Conflict", foreign_keys="Conflict.parcel_b_id", back_populates="parcel_b", lazy="select"
    )
    audit_entries: Mapped[list["AuditLogEntry"]] = relationship(  # noqa: F821
        "AuditLogEntry",
        primaryjoin="and_(AuditLogEntry.entity_type=='parcel', foreign(AuditLogEntry.entity_id)==Parcel.id)",
        lazy="select",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<Parcel id={self.id!r} status={self.workflow_status!r} confidence={self.confidence}>"
