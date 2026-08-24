"""
app/models/feature.py
──────────────────────
BuildingFootprint — AI-extracted geospatial feature.

Linked to both the source ImageryTile and the ProcessingJob that
produced it. Optionally associated with a reviewed Parcel.

Geometry stored as WKT TEXT (same SQLite/PostGIS migration strategy
as Parcel.geometry_wkt).
"""

from __future__ import annotations

import enum

from sqlalchemy import Enum, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class FeatureType(str, enum.Enum):
    BUILDING = "building"
    ROAD = "road"
    WATER = "water"
    VEGETATION = "vegetation"
    LAND = "land"
    OTHER = "other"


class BuildingFootprint(UUIDMixin, TimestampMixin, Base):
    """
    AI-extracted geospatial feature (building, road, water body, etc.).

    STUB: Phase 2 creates the schema. Phase 3 populates from AI pipeline output.
    """

    __tablename__ = "building_footprints"

    tile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("imagery_tiles.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    job_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("processing_jobs.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    parcel_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("parcels.id", ondelete="SET NULL"),
        nullable=True, index=True
    )

    geometry_wkt: Mapped[str | None] = mapped_column(Text, nullable=True)
    feature_type: Mapped[FeatureType] = mapped_column(
        Enum(FeatureType, values_callable=lambda e: [m.value for m in e], native_enum=False),
        default=FeatureType.BUILDING,
        nullable=False,
        index=True,
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    tile: Mapped["ImageryTile"] = relationship(  # noqa: F821
        "ImageryTile", back_populates="features", lazy="select"
    )
    job: Mapped["ProcessingJob | None"] = relationship(  # noqa: F821
        "ProcessingJob", back_populates="features", lazy="select"
    )
    parcel: Mapped["Parcel | None"] = relationship(  # noqa: F821
        "Parcel", back_populates="buildings", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<BuildingFootprint id={self.id!r} type={self.feature_type!r}>"
