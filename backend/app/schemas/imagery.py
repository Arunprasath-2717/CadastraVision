"""app/schemas/imagery.py — Imagery upload, job status, tile, and feature schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.imagery import JobStatus, JobType, TileSource, TileStatus


class UploadResponse(BaseModel):
    """Response from POST /v1/imagery/upload."""
    tile_id: str
    job_id: str
    status: JobStatus
    message: str = "Imagery accepted. Processing queued."

    model_config = {"json_schema_extra": {"example": {
        "tile_id": "uuid-tile",
        "job_id": "uuid-job",
        "status": "queued",
        "message": "Imagery accepted. Processing queued.",
    }}}


class JobStatusResponse(BaseModel):
    """GET /v1/imagery/jobs/{job_id} — job lifecycle status."""
    job_id: str
    tile_id: str
    job_type: JobType
    status: JobStatus
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    result_summary: dict | None = None


class TileResponse(BaseModel):
    """GET /v1/imagery/tiles/{tile_id}."""
    tile_id: str
    filename: str
    source: TileSource
    status: TileStatus
    crs: str | None = None
    bounds_wkt: str | None = None
    resolution_m: float | None = None
    file_size_bytes: int | None = None
    created_at: datetime


class FeatureItem(BaseModel):
    """Single extracted feature in a tile's feature list."""
    feature_id: str
    feature_type: str
    confidence: float | None = None
    geometry_wkt: str | None = None
    metadata: dict | None = None


class TileFeaturesResponse(BaseModel):
    """GET /v1/imagery/tiles/{tile_id}/features."""
    tile_id: str
    job_id: str | None = None
    features: list[FeatureItem] = Field(default_factory=list)
    total: int = 0
