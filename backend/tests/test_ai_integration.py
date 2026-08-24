"""
tests/test_ai_integration.py
───────────────────────────────
Comprehensive Phase 4 test suite: AI Integration, Feature Persistence,
Topology Validation, Job Lifecycle, Retry Idempotency, and Human-Review Protection.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ValidationError
from app.integrations.ai.segmentation import (
    SegmentationFeature,
    SegmentationProcessor,
    SegmentationResult,
)
from app.integrations.topology.validator import FlagDetail, TopologyValidationService
from app.models.feature import BuildingFootprint
from app.models.imagery import JobStatus, TileStatus
from app.models.parcel import Parcel, ParcelWorkflowStatus
from app.models.validation import FlagSeverity, FlagType
from app.services.imagery_service import ImageryService

# ─── 1. AI PROCESSOR INTERFACE & SCHEMA VALIDATION TESTS ──────────────────


def test_segmentation_feature_validation():
    """Verify confidence range and geometry validations on SegmentationFeature."""
    # Valid feature
    feat = SegmentationFeature(
        feature_type="building",
        geometry_wkt="POLYGON ((0 0, 0 10, 10 10, 10 0, 0 0))",
        confidence=0.95,
    )
    assert feat.confidence == 0.95
    assert feat.feature_type == "building"

    # Invalid confidence > 1.0
    with pytest.raises(ValidationError, match="Invalid confidence score"):
        SegmentationFeature(
            feature_type="building",
            geometry_wkt="POLYGON ((0 0, 0 10, 10 10, 10 0, 0 0))",
            confidence=1.5,
        )

    # Invalid confidence < 0.0
    with pytest.raises(ValidationError, match="Invalid confidence score"):
        SegmentationFeature(
            feature_type="building",
            geometry_wkt="POLYGON ((0 0, 0 10, 10 10, 10 0, 0 0))",
            confidence=-0.1,
        )

    # Empty geometry
    with pytest.raises(ValidationError, match="geometry_wkt cannot be empty"):
        SegmentationFeature(
            feature_type="building",
            geometry_wkt="",
            confidence=0.8,
        )

    # Unsupported feature type
    with pytest.raises(ValidationError, match="Unsupported feature type"):
        SegmentationFeature(
            feature_type="alien_structure",
            geometry_wkt="POLYGON ((0 0, 0 10, 10 10, 10 0, 0 0))",
            confidence=0.8,
        )


@pytest.mark.asyncio
async def test_segmentation_processor_mock_execution():
    """Verify SegmentationProcessor returns a validated SegmentationResult."""
    processor = SegmentationProcessor()
    res = await processor.process_tile(tile_id="tile-123", job_id="job-456")

    assert isinstance(res, SegmentationResult)
    assert res.tile_id == "tile-123"
    assert res.processing_job_id == "job-456"
    assert len(res.features) >= 2
    assert len(res.building_footprints) >= 1
    assert len(res.parcel_candidates) >= 1


# ─── 2. TOPOLOGY VALIDATION INTERFACE TESTS ─────────────────────────────


@pytest.mark.asyncio
async def test_topology_validation_service():
    """Verify TopologyValidationService performs structural and confidence checks."""
    service = TopologyValidationService()

    # Valid polygon with high confidence
    val_res = await service.validate_parcel(
        parcel_id="p-1",
        geometry_wkt="POLYGON ((0 0, 0 10, 10 10, 10 0, 0 0))",
        confidence=0.85,
    )
    assert val_res.is_valid is True
    assert len(val_res.flags) == 0

    # Low confidence warning flag
    val_res_low = await service.validate_parcel(
        parcel_id="p-2",
        geometry_wkt="POLYGON ((0 0, 0 10, 10 10, 10 0, 0 0))",
        confidence=0.55,
    )
    assert len(val_res_low.flags) == 1
    assert val_res_low.flags[0].flag_type == FlagType.CONFIDENCE_LOW
    assert val_res_low.flags[0].severity == FlagSeverity.WARNING

    # Invalid geometry WKT
    val_res_invalid = await service.validate_parcel(
        parcel_id="p-3",
        geometry_wkt="POINT (0 0)",
        confidence=0.90,
    )
    assert val_res_invalid.is_valid is False
    assert any(f.flag_type == FlagType.SELF_INTERSECTION for f in val_res_invalid.flags)


# ─── 3. ASYNC WORKFLOW & FEATURE PERSISTENCE TESTS ──────────────────────


@pytest.mark.asyncio
async def test_imagery_service_ai_processing_workflow(db_session: AsyncSession):
    """Test ingest_tile -> AI segmentation -> feature & candidate parcel persistence."""
    service = ImageryService(db_session)

    tile, job = await service.ingest_tile(
        filename="test_ortho.tif",
        file_path="/tmp/test_ortho.tif",
        file_size_bytes=2048,
        mime_type="image/tiff",
        crs="EPSG:4326",
        bounds_wkt="POLYGON ((0 0, 0 100, 100 100, 100 0, 0 0))",
    )

    assert tile.status == TileStatus.PROCESSED
    assert job.status == JobStatus.COMPLETE
    assert job.result_json is not None
    assert job.result_json["persisted_features"] >= 1
    assert job.result_json["persisted_parcels"] >= 1

    # Verify building footprint was persisted
    bf_stmt = select(BuildingFootprint).where(BuildingFootprint.tile_id == tile.id)
    bf_res = await db_session.execute(bf_stmt)
    buildings = bf_res.scalars().all()
    assert len(buildings) >= 1
    assert buildings[0].confidence == 0.92

    # Verify candidate parcel was persisted
    p_stmt = select(Parcel).where(Parcel.source_tile_id == tile.id)
    p_res = await db_session.execute(p_stmt)
    parcels = p_res.scalars().all()
    assert len(parcels) >= 1
    candidate = parcels[0]
    assert candidate.confidence == 0.88
    # HUMAN REVIEW PROTECTION CHECK: Parcel must NOT be approved
    assert candidate.workflow_status in (
        ParcelWorkflowStatus.DRAFT,
        ParcelWorkflowStatus.VALIDATED,
        ParcelWorkflowStatus.VALIDATION_PENDING,
    )
    assert candidate.workflow_status != ParcelWorkflowStatus.APPROVED


# ─── 4. JOB FAILURE HANDLING & RETRY IDEMPOTENCY TESTS ─────────────────


class FailingProcessor(SegmentationProcessor):
    """Failing processor to test error handling."""

    async def process_tile(self, tile_id: str, job_id: str) -> SegmentationResult:
        raise RuntimeError("GPU OOM error during SAM inference")


@pytest.mark.asyncio
async def test_job_failure_and_retry_handling(db_session: AsyncSession):
    """Test AI job failure state transition and safe idempotent retry."""
    failing_proc = FailingProcessor()
    service = ImageryService(db_session, ai_processor=failing_proc)

    # Ingest with failing processor
    tile, job = await service.ingest_tile(
        filename="failing_tile.tif",
        file_path="/tmp/failing_tile.tif",
        auto_process=True,
    )

    assert job.status == JobStatus.FAILED
    assert "GPU OOM error" in job.error_message
    assert tile.status == TileStatus.FAILED

    # Retry job with working processor
    working_proc = SegmentationProcessor()
    service.ai_processor = working_proc

    retried_job = await service.retry_job(job.id)

    assert retried_job.status == JobStatus.COMPLETE
    assert retried_job.error_message is None
    assert retried_job.result_json["persisted_features"] >= 1

    # Verify retry did not create duplicate features for the same job
    bf_stmt = select(BuildingFootprint).where(BuildingFootprint.job_id == job.id)
    bf_res = await db_session.execute(bf_stmt)
    features = bf_res.scalars().all()
    assert len(features) == retried_job.result_json["persisted_features"]


# ─── 5. TOPOLOGY FLAG PERSISTENCE & QUEUE ROUTE TESTS ──────────────────


@pytest.mark.asyncio
async def test_validation_flags_and_queue_routes(
    db_session: AsyncSession, client: AsyncClient
):
    """Test topology flags creation on parcel and API router queries."""
    # Custom topology service returning a flag
    custom_top = TopologyValidationService(
        mock_flags=[
            FlagDetail(
                flag_type=FlagType.OVERLAP,
                severity=FlagSeverity.ERROR,
                description="Overlap detected with adjacent parcel P-99",
            )
        ]
    )
    service = ImageryService(db_session, topology_service=custom_top)

    tile, job = await service.ingest_tile(
        filename="flag_test.tif",
        file_path="/tmp/flag_test.tif",
        auto_process=True,
    )

    # Get created candidate parcel
    p_stmt = select(Parcel).where(Parcel.source_tile_id == tile.id)
    p_res = await db_session.execute(p_stmt)
    parcel = p_res.scalars().first()

    assert parcel is not None
    assert parcel.workflow_status == ParcelWorkflowStatus.VALIDATION_PENDING

    # GET /v1/parcels/{id}/flags
    flags_resp = await client.get(f"/v1/parcels/{parcel.id}/flags")
    assert flags_resp.status_code == 200
    flags_data = flags_resp.json()
    assert flags_data["total"] >= 1
    assert flags_data["flags"][0]["flag_type"] == "overlap"

    # GET /v1/validations/queue
    queue_resp = await client.get("/v1/validations/queue")
    assert queue_resp.status_code == 200
    queue_data = queue_resp.json()
    assert len(queue_data["items"]) >= 1

    # GET /v1/imagery/tiles/{id}/features
    features_resp = await client.get(f"/v1/imagery/tiles/{tile.id}/features")
    assert features_resp.status_code == 200
    feat_data = features_resp.json()
    assert feat_data["total"] >= 1


# ─── 6. HUMAN REVIEW PROTECTION TEST ────────────────────────────────────


@pytest.mark.asyncio
async def test_human_review_protection_enforcement(
    db_session: AsyncSession, client: AsyncClient
):
    """Verify that candidate parcels cannot skip human review or auto-approve."""
    service = ImageryService(db_session)
    tile, job = await service.ingest_tile(
        filename="review_guard.tif",
        file_path="/tmp/review_guard.tif",
        auto_process=True,
    )

    p_stmt = select(Parcel).where(Parcel.source_tile_id == tile.id)
    p_res = await db_session.execute(p_stmt)
    parcel = p_res.scalars().first()

    # AI pipeline generated the parcel, but status is DRAFT / VALIDATED, NOT APPROVED
    assert parcel.workflow_status != ParcelWorkflowStatus.APPROVED

    # Set status to VALIDATED so human sign-off succeeds
    parcel.workflow_status = ParcelWorkflowStatus.VALIDATED
    await db_session.flush()

    # Approve parcel via human review route
    approve_resp = await client.post(
        f"/v1/parcels/{parcel.id}/approve",
        json={"notes": "Reviewed and verified by senior surveyor."},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["workflow_status"] == "approved"
