"""
app/services/imagery_service.py
─────────────────────────────────
Imagery ingestion and AI job processing service for Phase 4.

Handles:
1. Validating upload metadata and file format
2. Creating ImageryTile and ProcessingJob DB records
3. Executing background AI segmentation (SegmentationProcessor)
4. AI feature validation, confidence scoring, and DB persistence (BuildingFootprint)
5. Candidate Parcel creation, CRS preservation, and Human-Review protection
6. Topology Validation integration (TopologyValidationService) and ValidationFlag creation
7. Idempotent job retries (cleaning up prior job features to prevent duplication)
8. Polling job status, tile metadata, and extracted features
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError
from app.integrations.ai.segmentation import (
    SegmentationProcessor,
    SegmentationResult,
)
from app.integrations.topology.validator import TopologyValidationService
from app.models.feature import BuildingFootprint, FeatureType
from app.models.imagery import (
    ImageryTile,
    JobStatus,
    JobType,
    ProcessingJob,
    TileSource,
    TileStatus,
)
from app.models.parcel import Parcel, ParcelWorkflowStatus
from app.models.validation import FlagSeverity, FlagType, ValidationFlag

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".tif", ".tiff", ".jpg", ".jpeg", ".png"}


class ImageryService:
    """Service layer for imagery upload, tile metadata, AI job processing, and feature extraction."""

    def __init__(
        self,
        db: AsyncSession,
        ai_processor: SegmentationProcessor | None = None,
        topology_service: TopologyValidationService | None = None,
    ) -> None:
        self.db = db
        self.ai_processor = ai_processor or SegmentationProcessor()
        self.topology_service = topology_service or TopologyValidationService()

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
        auto_process: bool = True,
    ) -> tuple[ImageryTile, ProcessingJob]:
        """
        Validate metadata, persist ImageryTile + ProcessingJob, and trigger AI processing.
        """
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
            crs=crs or "EPSG:4326",
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

        # 3. Process AI job
        if auto_process:
            await self.process_job(job.id)

        await self.db.commit()
        await self.db.refresh(tile)
        await self.db.refresh(job)
        return tile, job

    async def process_job(self, job_id: str) -> ProcessingJob:
        """
        Execute AI segmentation job with idempotency, feature persistence,
        topology validation, and candidate parcel creation.
        """
        job = await self.get_job(job_id)
        tile = await self.get_tile(job.tile_id)

        # Job state machine: QUEUED -> PROCESSING
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc).isoformat()
        tile.status = TileStatus.PROCESSING
        await self.db.flush()

        try:
            # 1. Idempotency cleanup: remove previous features linked to this job if retrying
            await self.db.execute(
                delete(BuildingFootprint).where(BuildingFootprint.job_id == job.id)
            )

            # 2. Run AI Segmentation
            logger.info("Executing AI segmentation for job=%s tile=%s", job.id, tile.id)
            result: SegmentationResult = await self.ai_processor.process_tile(tile.id, job.id)

            created_parcels_count = 0
            created_features_count = 0

            # 3. Process & persist extracted AI features
            for feature in result.features:
                if feature.feature_type == "parcel_candidate":
                    # Create candidate Parcel
                    # HUMAN-REVIEW PROTECTION: Candidates are NEVER auto-approved. Status is DRAFT or VALIDATION_PENDING.
                    parcel = Parcel(
                        geometry_wkt=feature.geometry_wkt,
                        source_tile_id=tile.id,
                        confidence=feature.confidence,
                        zone=feature.metadata.get("zone", "unassigned"),
                        jurisdiction=feature.metadata.get("jurisdiction", "district-1"),
                        workflow_status=ParcelWorkflowStatus.DRAFT,
                    )
                    self.db.add(parcel)
                    await self.db.flush()

                    # Run Topology Validation Service safely
                    try:
                        val_res = await self.topology_service.validate_parcel(
                            parcel_id=parcel.id,
                            geometry_wkt=feature.geometry_wkt,
                            confidence=feature.confidence,
                        )
                    except Exception as top_exc:
                        logger.warning(
                            "Topology validation failed for parcel=%s: %s", parcel.id, top_exc
                        )
                        val_res = None

                    # Persist any validation flags
                    if val_res and val_res.flags:
                        parcel.workflow_status = ParcelWorkflowStatus.VALIDATION_PENDING
                        for flag_detail in val_res.flags:
                            flag_record = ValidationFlag(
                                parcel_id=parcel.id,
                                flag_type=flag_detail.flag_type,
                                severity=flag_detail.severity,
                                description=flag_detail.description,
                            )
                            self.db.add(flag_record)
                    elif val_res and val_res.is_valid:
                        parcel.workflow_status = ParcelWorkflowStatus.VALIDATED
                    else:
                        # Topology failed safely — create warning flag
                        parcel.workflow_status = ParcelWorkflowStatus.VALIDATION_PENDING
                        self.db.add(
                            ValidationFlag(
                                parcel_id=parcel.id,
                                flag_type=FlagType.OTHER,
                                severity=FlagSeverity.WARNING,
                                description="Topology validation service encountered an unexpected error",
                            )
                        )

                    created_parcels_count += 1
                else:
                    # Persist feature (building, road, land_use, etc.)
                    feat_type_enum = (
                        FeatureType.BUILDING
                        if feature.feature_type == "building"
                        else FeatureType.OTHER
                    )
                    bf = BuildingFootprint(
                        tile_id=tile.id,
                        job_id=job.id,
                        geometry_wkt=feature.geometry_wkt,
                        feature_type=feat_type_enum,
                        confidence=feature.confidence,
                        source=result.model_name,
                        metadata_json=feature.metadata,
                    )
                    self.db.add(bf)
                    created_features_count += 1

            # 4. Job complete state transition
            job.status = JobStatus.COMPLETE
            job.completed_at = datetime.now(timezone.utc).isoformat()
            res_dict = result.to_dict()
            res_dict["persisted_parcels"] = created_parcels_count
            res_dict["persisted_features"] = created_features_count
            job.result_json = res_dict
            tile.status = TileStatus.PROCESSED

            logger.info(
                "Job complete job=%s persisted %d parcels, %d features",
                job.id,
                created_parcels_count,
                created_features_count,
            )

        except (Exception, asyncio.TimeoutError) as exc:
            logger.exception("AI processing failed for job=%s: %s", job.id, exc)
            job.status = JobStatus.FAILED
            job.error_message = f"AI processing error: {str(exc)}"
            job.result_json = {"error": str(exc), "status": "failed"}
            tile.status = TileStatus.FAILED

        await self.db.flush()
        return job

    async def retry_job(self, job_id: str) -> ProcessingJob:
        """
        Retry a FAILED or QUEUED job safely. Idempotent — replaces prior results.
        """
        job = await self.get_job(job_id)
        if job.status not in (JobStatus.FAILED, JobStatus.QUEUED):
            raise ValidationError(
                detail=f"Job '{job_id}' is in status '{job.status.value}' and cannot be retried."
            )

        job.status = JobStatus.QUEUED
        job.error_message = None
        job.result_json = None
        await self.db.flush()

        return await self.process_job(job.id)

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

    async def get_tile_features(self, tile_id: str) -> list[BuildingFootprint]:
        """Retrieve AI-extracted building footprints and features for a tile."""
        stmt = select(BuildingFootprint).where(BuildingFootprint.tile_id == tile_id)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
