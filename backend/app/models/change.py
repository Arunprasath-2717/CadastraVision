"""
app/models/change.py
─────────────────────
ChangeRecord — Geospatial feature change detection ORM model.

Tracks detected changes between historical and current imagery / feature datasets.
"""

from __future__ import annotations

import enum

from sqlalchemy import Enum, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ChangeType(str, enum.Enum):
    NEW = "NEW"
    REMOVED = "REMOVED"
    MODIFIED = "MODIFIED"
    UNCHANGED = "UNCHANGED"


class ChangeStatus(str, enum.Enum):
    DETECTED = "DETECTED"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ChangeRecord(UUIDMixin, TimestampMixin, Base):
    """Geospatial change candidate generated between two imagery/feature datasets."""

    __tablename__ = "change_records"

    historical_tile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("imagery_tiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    current_tile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("imagery_tiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("processing_jobs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    parcel_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("parcels.id", ondelete="SET NULL"), nullable=True, index=True
    )
    previous_feature_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("building_footprints.id", ondelete="SET NULL"), nullable=True, index=True
    )
    current_feature_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("building_footprints.id", ondelete="SET NULL"), nullable=True, index=True
    )

    change_type: Mapped[ChangeType] = mapped_column(
        Enum(ChangeType, values_callable=lambda e: [m.value for m in e], native_enum=False),
        nullable=False,
        index=True,
    )
    status: Mapped[ChangeStatus] = mapped_column(
        Enum(ChangeStatus, values_callable=lambda e: [m.value for m in e], native_enum=False),
        default=ChangeStatus.DETECTED,
        nullable=False,
        index=True,
    )

    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    geometry_diff_wkt: Mapped[str | None] = mapped_column(Text, nullable=True)
    attribute_diff_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    idempotency_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # Human review tracking
    reviewed_by_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reviewed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    historical_tile: Mapped["ImageryTile"] = relationship(  # noqa: F821
        "ImageryTile", foreign_keys=[historical_tile_id], lazy="select"
    )
    current_tile: Mapped["ImageryTile"] = relationship(  # noqa: F821
        "ImageryTile", foreign_keys=[current_tile_id], lazy="select"
    )
    job: Mapped["ProcessingJob | None"] = relationship(  # noqa: F821
        "ProcessingJob", foreign_keys=[job_id], lazy="select"
    )
    parcel: Mapped["Parcel | None"] = relationship(  # noqa: F821
        "Parcel", foreign_keys=[parcel_id], lazy="select"
    )
    previous_feature: Mapped["BuildingFootprint | None"] = relationship(  # noqa: F821
        "BuildingFootprint", foreign_keys=[previous_feature_id], lazy="select"
    )
    current_feature: Mapped["BuildingFootprint | None"] = relationship(  # noqa: F821
        "BuildingFootprint", foreign_keys=[current_feature_id], lazy="select"
    )
    reviewed_by: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys=[reviewed_by_id], lazy="select"
    )

    def __repr__(self) -> str:
        return f"<ChangeRecord id={self.id!r} type={self.change_type!r} status={self.status!r}>"
