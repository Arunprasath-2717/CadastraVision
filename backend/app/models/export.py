"""
app/models/export.py
─────────────────────
Export — data export job record.

Tracks the lifecycle of a data export request (GeoJSON, Shapefile,
GeoPackage). The actual export generation is a background operation;
the record provides status polling.
"""

from __future__ import annotations

import enum

from sqlalchemy import Enum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ExportFormat(str, enum.Enum):
    GEOJSON = "geojson"
    SHAPEFILE = "shapefile"
    GEOPACKAGE = "geopackage"
    CSV = "csv"


class ExportStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class Export(UUIDMixin, TimestampMixin, Base):
    """Data export job record."""

    __tablename__ = "exports"

    export_format: Mapped[ExportFormat] = mapped_column(
        Enum(ExportFormat, values_callable=lambda e: [m.value for m in e], native_enum=False),
        nullable=False,
    )
    status: Mapped[ExportStatus] = mapped_column(
        Enum(ExportStatus, values_callable=lambda e: [m.value for m in e], native_enum=False),
        default=ExportStatus.QUEUED,
        nullable=False,
        index=True,
    )

    # Filters applied when generating the export
    filter_params_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Output file path (available when status == COMPLETE)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(nullable=True)

    completed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    created_by_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_by: Mapped["User | None"] = relationship(  # noqa: F821
        "User", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Export id={self.id!r} format={self.export_format!r} status={self.status!r}>"
