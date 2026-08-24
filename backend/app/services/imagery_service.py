"""
app/services/imagery_service.py
─────────────────────────────────
Imagery ingestion and job tracking service.

Handles:
1. Validating upload metadata and file format
2. Creating ImageryTile and ProcessingJob DB records
3. Triggering background AI processing via SegmentationProcessor (Akshaya's hook)
4. Polling job status and tile metadata
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError
from app.integrations.ai.segmentation import SegmentationProcessor
from app.models.imagery import (
    ImageryTile,
    JobStatus,
    JobType,
    ProcessingJob,
    TileSource,
    TileStatus,
)

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    "image/tiff",
    "image/geotiff",
    "image/jpeg",
    "image/png",
    "application/octet-stream",
}

ALLOWED_EXTENSIONS = {".tif", ".tiff", ".jpg", ".jpeg", ".png"}


class ImageryService:
    """Service layer for imagery upload, tile metadata, and AI job processing."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.ai_processor = SegmentationProcessor()

    async def ingest_tile(
        self,
        *,
        filename: str,
        file_path: str,
        file_size_bytes: int | None = None,
        mime_type: str | None = None,
        source: TileSource = TileSource.SATELLITE,
        crs: str | None = None,
        bounds_wkt: str | None = None,
        uploaded_by_id: str | None = None,
    ) -> tuple[ImageryTile, ProcessingJob]:
        """
        Validate metadata, persist ImageryTile + ProcessingJob, and dispatch AI job.
        """
        # Validate extension
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError(
                detail=f"Unsupported file format '{ext}'. Allowed formats: {sorted(ALLOWED_EXTENSIONS)}"
            )

        # 1. Create Tile
        tile = ImageryTile(
            filename=filename,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            mime_type=mime_type,
            source=source,
            crs=crs,
            bounds_wkt=bounds_wkt,
            status=TileStatus.PROCESSING,
            uploaded_by_id=uploaded_by_id,
        )
        self.db.add(tile)
        await self.db.flush()

        # 2. Create Processing Job
        job = ProcessingJob(
            tile_id=tile.id,
            job_type=JobType.SEGMENTATION,
            status=JobStatus.QUEUED,
        )
        self.db.add(job)
        await self.db.flush()

        # 3. Dispatch AI processing hook (Akshaya's pipeline integration)
        try:
            logger.info("Dispatching AI segmentation for tile=%s job=%s", tile.id, job.id)
            # In Phase 3, this triggers the processor which populates features and parcels
            ai_result = await self.ai_processor.process_tile(tile.id, job.id)
            job.status = JobStatus.COMPLETE
            job.result_json = ai_result
            tile.status = TileStatus.PROCESSED
        except Exception as exc:
            logger.exception("AI processing failed for job=%s: %s", job.id, exc)
            job.status = JobStatus.FAILED
            job.error_message = str(exc)
            tile.status = TileStatus.FAILED

        await self.db.commit()
        await self.db.refresh(tile)
        await self.db.refresh(job)
        return tile, job

    async def get_job(self, job_id: str) -> ProcessingJob:
        """Retrieve a processing job by ID."""
        stmt = select(ProcessingJob).where(ProcessingJob.id == job_id)
        res = await self.db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise NotFoundError(detail=f"Processing job '{job_id}' not found.")
        return job

    async def get_tile(self, tile_id: str) -> ImageryTile:
        """Retrieve an imagery tile by ID."""
        stmt = select(ImageryTile).where(ImageryTile.id == tile_id)
        res = await self.db.execute(stmt)
        tile = res.scalar_one_or_none()
        if not tile:
            raise NotFoundError(detail=f"Imagery tile '{tile_id}' not found.")
        return tile
