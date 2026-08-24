"""
app/routers/imagery.py
───────────────────────
POST /v1/imagery/upload
GET  /v1/imagery/jobs/{job_id}
POST /v1/imagery/jobs/{job_id}/retry
GET  /v1/imagery/tiles/{tile_id}
GET  /v1/imagery/tiles/{tile_id}/features
"""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.feature import BuildingFootprint
from app.models.imagery import TileSource
from app.models.user import User, UserRole
from app.schemas.imagery import (
    FeatureItem,
    JobStatusResponse,
    TileFeaturesResponse,
    TileResponse,
    UploadResponse,
)
from app.services.imagery_service import ImageryService

router = APIRouter(prefix="/v1/imagery", tags=["Imagery"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload imagery tile",
    description=(
        "Upload a satellite or drone imagery tile for AI processing. "
        "Returns tile_id and job_id immediately — processing is dispatched."
    ),
)
async def upload_imagery(
    file: UploadFile = File(..., description="GeoTIFF or supported imagery file"),
    source: TileSource = Form(default=TileSource.SATELLITE),
    crs: str | None = Form(default=None, description="CRS e.g. EPSG:4326"),
    bounds_wkt: str | None = Form(default=None, description="Bounding box WKT"),
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    upload_dir = "/tmp/cadastravision_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename or "tile.tif")

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    service = ImageryService(db)
    tile, job = await service.ingest_tile(
        filename=file.filename or "tile.tif",
        file_path=file_path,
        file_size_bytes=len(contents),
        mime_type=file.content_type,
        source=source,
        crs=crs,
        bounds_wkt=bounds_wkt,
        uploaded_by_id=current_user.id,
    )

    return UploadResponse(
        tile_id=tile.id,
        job_id=job.id,
        status=job.status,
        message="Imagery accepted. AI processing initiated.",
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get processing job status",
    description="Poll the status of an imagery processing job.",
)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobStatusResponse:
    service = ImageryService(db)
    job = await service.get_job(job_id)
    return JobStatusResponse(
        job_id=job.id,
        tile_id=job.tile_id,
        job_type=job.job_type,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        result_summary=job.result_json,
    )


@router.post(
    "/jobs/{job_id}/retry",
    response_model=JobStatusResponse,
    summary="Retry a processing job",
    description="Safely retry a failed or queued imagery processing job. Idempotent.",
)
async def retry_job(
    job_id: str,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> JobStatusResponse:
    service = ImageryService(db)
    job = await service.retry_job(job_id)
    await db.commit()
    await db.refresh(job)
    return JobStatusResponse(
        job_id=job.id,
        tile_id=job.tile_id,
        job_type=job.job_type,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        result_summary=job.result_json,
    )


@router.get(
    "/tiles/{tile_id}",
    response_model=TileResponse,
    summary="Get imagery tile metadata",
    description="Retrieve metadata for an uploaded imagery tile.",
)
async def get_tile(
    tile_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TileResponse:
    service = ImageryService(db)
    tile = await service.get_tile(tile_id)
    return TileResponse(
        tile_id=tile.id,
        filename=tile.filename,
        source=tile.source,
        status=tile.status,
        crs=tile.crs,
        bounds_wkt=tile.bounds_wkt,
        resolution_m=tile.resolution_m,
        file_size_bytes=tile.file_size_bytes,
        created_at=tile.created_at,
    )


@router.get(
    "/tiles/{tile_id}/features",
    response_model=TileFeaturesResponse,
    summary="Get AI-extracted features for a tile",
    description="List building footprints and other features extracted from a tile.",
)
async def get_tile_features(
    tile_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TileFeaturesResponse:
    stmt = select(BuildingFootprint).where(BuildingFootprint.tile_id == tile_id)
    res = await db.execute(stmt)
    features = list(res.scalars().all())

    items = [
        FeatureItem(
            feature_id=f.id,
            feature_type=f.feature_type.value,
            confidence=f.confidence,
            geometry_wkt=f.geometry_wkt,
            metadata=f.metadata_json,
        )
        for f in features
    ]
    return TileFeaturesResponse(tile_id=tile_id, features=items, total=len(items))
