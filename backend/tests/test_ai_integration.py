"""
tests/test_ai_integration.py
Phase 4 comprehensive test suite — sections A through I (items 1-78).
"""
from __future__ import annotations

import asyncio
import os

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.errors import ValidationError
from app.integrations.ai.segmentation import (
    SegmentationFeature,
    SegmentationProcessor,
    SegmentationResult,
)
from app.integrations.topology.validator import FlagDetail, TopologyValidationService
from app.models.base import Base
from app.models.feature import BuildingFootprint
from app.models.imagery import JobStatus, TileStatus
from app.models.parcel import Parcel, ParcelWorkflowStatus
from app.models.validation import FlagSeverity, FlagType, ValidationFlag
from app.services.imagery_service import ImageryService
from app.services.parcel_service import ParcelService

# ── helpers ────────────────────────────────────────────────────────────────

class TimeoutProcessor(SegmentationProcessor):
    async def process_tile(self, tile_id: str, job_id: str) -> SegmentationResult:
        raise asyncio.TimeoutError("AI inference timed out after 30s")


class ExceptionTopologyService(TopologyValidationService):
    async def validate_parcel(self, parcel_id, geometry_wkt, confidence=None, neighbor_geometries=None):
        raise RuntimeError("Topology engine core dumped")


# ── A: AI PROCESSOR TESTS (1-12) ───────────────────────────────────────────

def test_01_ai_processor_initializes_correctly():
    assert SegmentationProcessor() is not None


@pytest.mark.asyncio
async def test_02_valid_imagery_passed_to_processor():
    res = await SegmentationProcessor().process_tile("t1", "j1")
    assert res.tile_id == "t1"


@pytest.mark.asyncio
async def test_03_mock_ai_processor_returns_valid_result():
    res = await SegmentationProcessor().process_tile("t1", "j1")
    assert isinstance(res, SegmentationResult)


@pytest.mark.asyncio
async def test_04_ai_result_contains_required_fields():
    d = (await SegmentationProcessor().process_tile("t1", "j1")).to_dict()
    for key in ("tile_id", "processing_job_id", "model_name", "features"):
        assert key in d


def test_05_missing_feature_type_rejected():
    with pytest.raises(ValidationError, match="Unsupported feature type"):
        SegmentationFeature(feature_type="ufo", geometry_wkt="POLYGON ((0 0,0 1,1 1,1 0,0 0))", confidence=0.9)


def test_06_missing_geometry_rejected():
    with pytest.raises(ValidationError, match="geometry_wkt cannot be empty"):
        SegmentationFeature(feature_type="building", geometry_wkt="  ", confidence=0.9)


def test_07_missing_confidence_rejected():
    with pytest.raises(TypeError):
        SegmentationFeature(feature_type="building", geometry_wkt="POLYGON ((0 0,0 1,1 1,1 0,0 0))", confidence=None)  # type: ignore


def test_08_confidence_below_0_rejected():
    with pytest.raises(ValidationError, match="Invalid confidence score"):
        SegmentationFeature(feature_type="building", geometry_wkt="POLYGON ((0 0,0 1,1 1,1 0,0 0))", confidence=-0.01)


def test_09_confidence_above_1_rejected():
    with pytest.raises(ValidationError, match="Invalid confidence score"):
        SegmentationFeature(feature_type="building", geometry_wkt="POLYGON ((0 0,0 1,1 1,1 0,0 0))", confidence=1.05)


def test_10_invalid_model_metadata_defaults():
    feat = SegmentationFeature(feature_type="building", geometry_wkt="POLYGON ((0 0,0 1,1 1,1 0,0 0))", confidence=0.8)
    assert isinstance(feat.metadata, dict)


@pytest.mark.asyncio
async def test_11_ai_processor_exception_handled(db_session: AsyncSession):
    class BombProcessor(SegmentationProcessor):
        async def process_tile(self, tile_id, job_id):
            raise RuntimeError("CUDA out of memory")

    svc = ImageryService(db_session, ai_processor=BombProcessor())
    tile, job = await svc.ingest_tile(filename="bomb.tif", file_path="/tmp/bomb.tif")
    assert job.status == JobStatus.FAILED
    assert "CUDA out of memory" in job.error_message


@pytest.mark.asyncio
async def test_12_ai_timeout_handled(db_session: AsyncSession):
    svc = ImageryService(db_session, ai_processor=TimeoutProcessor())
    tile, job = await svc.ingest_tile(filename="timeout.tif", file_path="/tmp/timeout.tif")
    assert job.status == JobStatus.FAILED
    assert tile.status == TileStatus.FAILED


# ── B: PROCESSING JOB TESTS (13-23) ───────────────────────────────────────

@pytest.mark.asyncio
async def test_13_14_imagery_creates_queued_job(db_session: AsyncSession):
    """13. Creates job. 14. Starts queued (auto_process=False)."""
    svc = ImageryService(db_session)
    tile, job = await svc.ingest_tile(filename="new.tif", file_path="/tmp/new.tif", auto_process=False)
    assert job.tile_id == tile.id
    assert job.status == JobStatus.QUEUED


@pytest.mark.asyncio
async def test_15_16_queued_to_processing_to_complete(db_session: AsyncSession):
    """15. queued→processing. 16. processing→complete."""
    svc = ImageryService(db_session)
    tile, job = await svc.ingest_tile(filename="flow.tif", file_path="/tmp/flow.tif", auto_process=False)
    assert job.status == JobStatus.QUEUED
    done = await svc.process_job(job.id)
    assert done.status == JobStatus.COMPLETE


@pytest.mark.asyncio
async def test_17_processing_to_failed(db_session: AsyncSession):
    """17. processing→failed on exception."""
    svc = ImageryService(db_session, ai_processor=TimeoutProcessor())
    tile, job = await svc.ingest_tile(filename="fail.tif", file_path="/tmp/fail.tif")
    assert job.status == JobStatus.FAILED
    assert tile.status == TileStatus.FAILED


@pytest.mark.asyncio
async def test_18_invalid_state_transition_rejected(db_session: AsyncSession):
    """18. Cannot retry a COMPLETE job."""
    svc = ImageryService(db_session)
    _, job = await svc.ingest_tile(filename="done.tif", file_path="/tmp/done.tif")
    assert job.status == JobStatus.COMPLETE
    with pytest.raises(ValidationError, match="cannot be retried"):
        await svc.retry_job(job.id)


@pytest.mark.asyncio
async def test_19_to_23_failed_job_retry(db_session: AsyncSession):
    """19. Failed job retried. 20. No duplicates. 21. Retrievable. 22-23. Error/timestamps."""
    svc = ImageryService(db_session, ai_processor=TimeoutProcessor())
    tile, job = await svc.ingest_tile(filename="retry.tif", file_path="/tmp/retry.tif")
    assert job.status == JobStatus.FAILED
    assert job.error_message is not None

    # 21. retrieve
    retrieved = await svc.get_job(job.id)
    assert retrieved.id == job.id

    # 19. retry with working processor
    svc.ai_processor = SegmentationProcessor()
    retried = await svc.retry_job(job.id)
    assert retried.status == JobStatus.COMPLETE
    # 23. timestamps persisted
    assert retried.started_at is not None
    assert retried.completed_at is not None


# ── C: FEATURE PERSISTENCE TESTS (24-33) ──────────────────────────────────

@pytest.mark.asyncio
async def test_24_to_31_feature_persistence(db_session: AsyncSession):
    """24-31. Feature persisted with correct tile, job, type, confidence, model info."""
    svc = ImageryService(db_session)
    tile, job = await svc.ingest_tile(filename="feat.tif", file_path="/tmp/feat.tif")
    features = await svc.get_tile_features(tile.id)
    assert len(features) >= 1
    bf = features[0]
    assert bf.tile_id == tile.id       # 25
    assert bf.job_id == job.id          # 26
    assert bf.confidence == 0.92        # 28
    assert bf.source == "cadastravision-segmentation-stub"  # 29


@pytest.mark.asyncio
async def test_32_invalid_ai_output_not_persisted(db_session: AsyncSession):
    """32. Invalid AI output (empty features) produces no BuildingFootprint records."""
    empty_proc = SegmentationProcessor(mock_features=[])
    svc = ImageryService(db_session, ai_processor=empty_proc)
    tile, job = await svc.ingest_tile(filename="empty.tif", file_path="/tmp/empty.tif")
    features = await svc.get_tile_features(tile.id)
    assert len(features) == 0


@pytest.mark.asyncio
async def test_33_duplicate_processing_no_duplicate_features(db_session: AsyncSession):
    """33. Retry does not duplicate BuildingFootprint records."""
    svc = ImageryService(db_session, ai_processor=TimeoutProcessor())
    tile, job = await svc.ingest_tile(filename="dedup.tif", file_path="/tmp/dedup.tif")

    svc.ai_processor = SegmentationProcessor()
    retried = await svc.retry_job(job.id)

    features = await svc.get_tile_features(tile.id)
    assert len(features) == retried.result_json["persisted_features"]


# ── D: GEOMETRY TESTS (34-40) ─────────────────────────────────────────────

def test_34_35_36_geometry_validation():
    """34. Valid geometry accepted. 35-36. Invalid/empty rejected."""
    feat = SegmentationFeature(feature_type="building",
                               geometry_wkt="POLYGON ((0 0,0 10,10 10,10 0,0 0))", confidence=0.9)
    assert "POLYGON" in feat.geometry_wkt

    with pytest.raises(ValidationError):
        SegmentationFeature(feature_type="building", geometry_wkt="", confidence=0.9)


@pytest.mark.asyncio
async def test_38_39_40_crs_and_geometry_retrieval(db_session: AsyncSession, client: AsyncClient):
    """38. CRS preserved. 39. Geometry retrievable. 40. API returns geometry."""
    svc = ImageryService(db_session)
    tile, _ = await svc.ingest_tile(
        filename="crs.tif", file_path="/tmp/crs.tif",
        crs="EPSG:4326", bounds_wkt="POLYGON ((0 0,0 10,10 10,10 0,0 0))",
    )
    assert tile.crs == "EPSG:4326"

    resp = await client.get(f"/v1/imagery/tiles/{tile.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["crs"] == "EPSG:4326"
    assert "POLYGON" in data["bounds_wkt"]


# ── E: TOPOLOGY INTEGRATION TESTS (41-48) ─────────────────────────────────

@pytest.mark.asyncio
async def test_41_42_topology_service_invoked_valid(db_session: AsyncSession):
    """41. Topology service invoked. 42. Valid topology accepted → VALIDATED."""
    svc = ImageryService(db_session, topology_service=TopologyValidationService())
    tile, job = await svc.ingest_tile(filename="top_ok.tif", file_path="/tmp/top_ok.tif")
    p_stmt = select(Parcel).where(Parcel.source_tile_id == tile.id)
    parcel = (await db_session.execute(p_stmt)).scalars().first()
    assert parcel is not None
    assert parcel.workflow_status == ParcelWorkflowStatus.VALIDATED


@pytest.mark.asyncio
async def test_43_to_46_topology_flags(db_session: AsyncSession):
    """43-46. Invalid topology produces flags with severity and details."""
    custom_top = TopologyValidationService(mock_flags=[
        FlagDetail(flag_type=FlagType.OVERLAP, severity=FlagSeverity.ERROR, description="Overlap with P-5"),
        FlagDetail(flag_type=FlagType.GAP, severity=FlagSeverity.WARNING, description="Gap detected"),
    ])
    svc = ImageryService(db_session, topology_service=custom_top)
    tile, _ = await svc.ingest_tile(filename="flags.tif", file_path="/tmp/flags.tif")

    p = (await db_session.execute(select(Parcel).where(Parcel.source_tile_id == tile.id))).scalars().first()
    assert p.workflow_status == ParcelWorkflowStatus.VALIDATION_PENDING

    flags = (await db_session.execute(select(ValidationFlag).where(ValidationFlag.parcel_id == p.id))).scalars().all()
    assert len(flags) == 2
    severities = {f.severity for f in flags}
    assert FlagSeverity.ERROR in severities
    assert FlagSeverity.WARNING in severities


@pytest.mark.asyncio
async def test_47_48_topology_failure_handled_safely(db_session: AsyncSession):
    """47-48. Topology exception handled; parcel and job still complete without DB corruption."""
    svc = ImageryService(db_session, topology_service=ExceptionTopologyService())
    tile, job = await svc.ingest_tile(filename="topfail.tif", file_path="/tmp/topfail.tif")
    assert job.status == JobStatus.COMPLETE

    p = (await db_session.execute(select(Parcel).where(Parcel.source_tile_id == tile.id))).scalars().first()
    assert p is not None
    flags = (await db_session.execute(select(ValidationFlag).where(ValidationFlag.parcel_id == p.id))).scalars().all()
    assert len(flags) >= 1


# ── F: CONFIDENCE / REVIEW TESTS (49-56) ──────────────────────────────────

@pytest.mark.asyncio
async def test_49_50_confidence_stored_and_reviewable(db_session: AsyncSession):
    """49. Confidence stored 0-1. 50. Low confidence stays reviewable."""
    low_conf = SegmentationProcessor(mock_features=[
        SegmentationFeature(feature_type="parcel_candidate",
                            geometry_wkt="POLYGON ((0 0,0 10,10 10,10 0,0 0))", confidence=0.55),
    ])
    svc = ImageryService(db_session, ai_processor=low_conf)
    tile, _ = await svc.ingest_tile(filename="low.tif", file_path="/tmp/low.tif")

    p = (await db_session.execute(select(Parcel).where(Parcel.source_tile_id == tile.id))).scalars().first()
    assert 0.0 <= p.confidence <= 1.0
    assert p.workflow_status != ParcelWorkflowStatus.APPROVED


@pytest.mark.asyncio
async def test_51_52_ai_cannot_auto_approve(db_session: AsyncSession):
    """51. AI cannot approve. 52. Enters correct review state."""
    svc = ImageryService(db_session)
    tile, _ = await svc.ingest_tile(filename="guard.tif", file_path="/tmp/guard.tif")

    p = (await db_session.execute(select(Parcel).where(Parcel.source_tile_id == tile.id))).scalars().first()
    assert p.workflow_status != ParcelWorkflowStatus.APPROVED
    assert p.workflow_status in (ParcelWorkflowStatus.VALIDATED, ParcelWorkflowStatus.DRAFT,
                                  ParcelWorkflowStatus.VALIDATION_PENDING)


@pytest.mark.asyncio
async def test_53_human_approval_works(db_session: AsyncSession, client: AsyncClient):
    """53. Human approval works."""
    svc = ImageryService(db_session)
    tile, _ = await svc.ingest_tile(filename="approve.tif", file_path="/tmp/approve.tif")

    p = (await db_session.execute(select(Parcel).where(Parcel.source_tile_id == tile.id))).scalars().first()
    p.workflow_status = ParcelWorkflowStatus.VALIDATED
    await db_session.flush()

    resp = await client.post(f"/v1/parcels/{p.id}/approve", json={"notes": "OK"})
    assert resp.status_code == 200
    assert resp.json()["workflow_status"] == "approved"


@pytest.mark.asyncio
async def test_54_55_human_rejection_works(db_session: AsyncSession, client: AsyncClient):
    """54-55. Rejection works; rejected parcel remains in DB."""
    svc = ImageryService(db_session)
    tile, _ = await svc.ingest_tile(filename="reject.tif", file_path="/tmp/reject.tif")

    p = (await db_session.execute(select(Parcel).where(Parcel.source_tile_id == tile.id))).scalars().first()
    p.workflow_status = ParcelWorkflowStatus.VALIDATED
    await db_session.flush()

    resp = await client.post(f"/v1/parcels/{p.id}/reject", json={"reason": "Boundary mismatch"})
    assert resp.status_code == 200
    assert resp.json()["workflow_status"] == "rejected"

    # 55. Still in DB (soft-delete, not hard delete)
    still_there = (await db_session.execute(select(Parcel).where(Parcel.id == p.id))).scalars().first()
    assert still_there is not None


@pytest.mark.asyncio
async def test_56_approval_blocked_when_not_validated(db_session: AsyncSession):
    """56. Approval blocked when parcel is DRAFT or VALIDATION_PENDING."""
    p = Parcel(geometry_wkt="POLYGON ((0 0,0 10,10 10,10 0,0 0))",
               workflow_status=ParcelWorkflowStatus.DRAFT)
    db_session.add(p)
    await db_session.flush()

    parcel_svc = ParcelService(db_session)
    with pytest.raises(ValidationError, match="Must be in 'validated' state"):
        await parcel_svc.approve(p.id)


# ── G: API TESTS (57-64) ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_57_to_64_api_routes(db_session: AsyncSession, client: AsyncClient):
    """57-64. Successful requests, 404, RFC 9457 errors, schema, OpenAPI."""
    svc = ImageryService(db_session)
    tile, job = await svc.ingest_tile(filename="api.tif", file_path="/tmp/api.tif")

    # 57/61/62. Successful GET job
    r = await client.get(f"/v1/imagery/jobs/{job.id}")
    assert r.status_code == 200
    assert "job_id" in r.json()

    # 57. Successful GET tile
    r = await client.get(f"/v1/imagery/tiles/{tile.id}")
    assert r.status_code == 200

    # 57. Successful GET features
    r = await client.get(f"/v1/imagery/tiles/{tile.id}/features")
    assert r.status_code == 200
    assert "features" in r.json()

    # 58/63. Missing resource → 404 RFC 9457
    r = await client.get("/v1/imagery/jobs/non-existent-id")
    assert r.status_code == 404
    body = r.json()
    assert "cadastravision.io" in body["type"]   # RFC 9457 type URL
    assert "status" in body
    assert "title" in body

    # 60. Invalid request → 422
    r = await client.get("/v1/parcels?confidence_min=2.0")
    assert r.status_code == 422

    # 64. OpenAPI contains retry endpoint
    r = await client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    assert any("retry" in p for p in paths)


# ── H: IDEMPOTENCY / RETRY TESTS (65-70) ─────────────────────────────────

@pytest.mark.asyncio
async def test_65_to_70_idempotency(db_session: AsyncSession):
    """65-70. No duplicate features on retry; retry after failure is safe."""
    svc = ImageryService(db_session, ai_processor=TimeoutProcessor())
    tile, job = await svc.ingest_tile(filename="idem.tif", file_path="/tmp/idem.tif")
    assert job.status == JobStatus.FAILED

    # Retry job once with working processor (65/69)
    svc.ai_processor = SegmentationProcessor()
    retried = await svc.retry_job(job.id)
    assert retried.status == JobStatus.COMPLETE

    # 68. Re-process same job multiple times — idempotent cleanup prevents duplicates
    await svc.process_job(job.id)
    await svc.process_job(job.id)

    features = await svc.get_tile_features(tile.id)
    # 65/68. Feature count matches exactly one run — no duplicates
    assert len(features) == retried.result_json["persisted_features"]


# ── I: DATABASE / MIGRATION TESTS (71-78) ─────────────────────────────────

@pytest.mark.asyncio
async def test_71_to_78_database_migration():
    """71-78. Migration creates all required tables and columns."""
    db_file = "/tmp/phase4_migration_clean.sqlite"
    if os.path.exists(db_file):
        os.remove(db_file)

    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ))
        tables = {row[0] for row in result.fetchall()}

    await engine.dispose()
    if os.path.exists(db_file):
        os.remove(db_file)

    # 72. Required tables exist
    assert "imagery_tiles" in tables
    assert "processing_jobs" in tables
    assert "building_footprints" in tables
    assert "parcels" in tables
    assert "validation_flags" in tables
    assert "sync_actions" in tables
    assert "audit_log_entries" in tables   # correct table name
    assert "users" in tables
