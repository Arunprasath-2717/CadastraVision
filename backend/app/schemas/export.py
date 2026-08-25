"""app/schemas/export.py — Export creation and status schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.export import ExportFormat, ExportStatus


class CreateExportRequest(BaseModel):
    """POST /v1/exports."""
    export_format: ExportFormat = Field(description="geojson | shapefile | geopackage | csv")
    filters: dict | None = Field(
        default=None,
        description="Optional filter params (zone, jurisdiction, status, etc.)",
    )


class ExportStatusResponse(BaseModel):
    """GET /v1/exports/{export_id}."""
    export_id: str
    export_format: ExportFormat
    status: ExportStatus
    created_at: datetime
    completed_at: datetime | None = None
    download_url: str | None = Field(
        default=None,
        description="Signed download URL — available when status is complete",
    )
    file_size_bytes: int | None = None
    error_message: str | None = None
