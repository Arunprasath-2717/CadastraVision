"""
app/models/imagery.py
──────────────────────
ImageryTile and ProcessingJob ORM models.

ImageryTile
───────────
Represents an uploaded satellite or drone imagery file. Geometry
stored as WKT bounding box (SQLite compatible). PostGIS migration
will add a native geometry column via Alembic.

ProcessingJob
─────────────
Tracks asynchronous AI processing tasks. Status lifecycle:
    queued → processing → complete
                       → failed
"""

from __future__ import annotations

import enum

from sqlalchemy import Enum, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class TileSource(str, enum.Enum):
    SATELLITE = "satellite"
    DRONE = "drone"
    AERIAL = "aerial"
    OTHER = "other"


class TileStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class JobType(str, enum.Enum):
    SEGMENTATION = "segmentation"
    CHANGE_DETECTION = "change_detection"
    FEATURE_EXTRACTION = "feature_extraction"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class ImageryTile(UUIDMixin, TimestampMixin, Base):
    """Uploaded imagery tile — satellite, drone, or aerial."""

    __tablename__ = "imagery_tiles"

    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Georeferencing
    crs: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g. "EPSG:4326"
    bounds_wkt: Mapped[str | None] = mapped_column(Text, nullable=True)  # bounding box WKT
    resolution_m: Mapped[float | None] = mapped_column(Float, nullable=True)  # metres/pixel

    source: Mapped[TileSource] = mapped_column(
        Enum(TileSource, values_callable=lambda e: [m.value for m in e], native_enum=False),
        default=TileSource.SATELLITE,
        nullable=False,
    )
    status: Mapped[TileStatus] = mapped_column(
        Enum(TileStatus, values_callable=lambda e: [m.value for m in e], native_enum=False),
        default=TileStatus.UPLOADED,
        nullable=False,
        index=True,
    )

    uploaded_by_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relationships
    uploaded_by: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys=[uploaded_by_id], back_populates="uploaded_tiles", lazy="select"
    )
    jobs: Mapped[list["ProcessingJob"]] = relationship(
        "ProcessingJob", back_populates="tile", lazy="select"
    )
    parcels: Mapped[list["Parcel"]] = relationship(  # noqa: F821
        "Parcel", back_populates="source_tile", lazy="select"
    )
    features: Mapped[list["BuildingFootprint"]] = relationship(  # noqa: F821
        "BuildingFootprint", back_populates="tile", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<ImageryTile id={self.id!r} filename={self.filename!r} status={self.status!r}>"


class ProcessingJob(UUIDMixin, TimestampMixin, Base):
    """Async processing job linked to an ImageryTile."""

    __tablename__ = "processing_jobs"

    tile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("imagery_tiles.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    job_type: Mapped[JobType] = mapped_column(
        Enum(JobType, values_callable=lambda e: [m.value for m in e], native_enum=False),
        nullable=False,
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, values_callable=lambda e: [m.value for m in e], native_enum=False),
        default=JobStatus.QUEUED,
        nullable=False,
        index=True,
    )

    # Timing
    started_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Results / errors
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    tile: Mapped["ImageryTile"] = relationship(
        "ImageryTile", back_populates="jobs", lazy="select"
    )
    features: Mapped[list["BuildingFootprint"]] = relationship(  # noqa: F821
        "BuildingFootprint", back_populates="job", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<ProcessingJob id={self.id!r} type={self.job_type!r} status={self.status!r}>"
