"""
tests/test_models.py
─────────────────────
Phase 2 model tests — PRD-CM-03 aligned.

Tests cover all 10 PRD domain models:
User, ImageryTile, ProcessingJob, Parcel, BuildingFootprint,
ValidationFlag, SyncAction, AuditLogEntry, Conflict, Export.
"""

from __future__ import annotations

import uuid

import pytest

from app.models import (
    AuditAction,
    AuditLogEntry,
    BuildingFootprint,
    Conflict,
    ConflictStatus,
    ConflictType,
    Export,
    ExportFormat,
    ExportStatus,
    FeatureType,
    FlagSeverity,
    FlagType,
    ImageryTile,
    JobStatus,
    JobType,
    Parcel,
    ParcelWorkflowStatus,
    ProcessingJob,
    SyncAction,
    SyncActionStatus,
    TileSource,
    TileStatus,
    User,
    UserRole,
    ValidationFlag,
)
from app.models.parcel import ALLOWED_TRANSITIONS, ParcelWorkflowStatus
from app.services.parcel_service import is_valid_transition


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def uid() -> str:
    return str(uuid.uuid4())


def make_user(**kw) -> User:
    return User(id=uid(), email=f"u_{uid()[:8]}@test.com",
                hashed_password="hash", full_name="Test", role=UserRole.ANALYST, is_active=True, **kw)


def make_tile(uploaded_by_id=None, **kw) -> ImageryTile:
    return ImageryTile(id=uid(), filename="test.tif", file_path="/tmp/test.tif",
                       source=TileSource.SATELLITE, status=TileStatus.UPLOADED,
                       uploaded_by_id=uploaded_by_id, **kw)


def make_job(tile_id: str, **kw) -> ProcessingJob:
    return ProcessingJob(id=uid(), tile_id=tile_id, job_type=JobType.SEGMENTATION,
                         status=JobStatus.QUEUED, **kw)


def make_parcel(tile_id=None, **kw) -> Parcel:
    return Parcel(id=uid(), source_tile_id=tile_id,
                  workflow_status=ParcelWorkflowStatus.DRAFT, confidence=0.85, **kw)


def make_feature(tile_id: str, job_id=None, parcel_id=None, **kw) -> BuildingFootprint:
    return BuildingFootprint(id=uid(), tile_id=tile_id, job_id=job_id, parcel_id=parcel_id,
                             feature_type=FeatureType.BUILDING, confidence=0.9, **kw)


def make_flag(parcel_id: str, **kw) -> ValidationFlag:
    return ValidationFlag(id=uid(), parcel_id=parcel_id,
                          flag_type=FlagType.OVERLAP, severity=FlagSeverity.WARNING, **kw)


def make_sync(**kw) -> SyncAction:
    client_action_id = kw.pop("client_action_id", f"client-{uid()[:8]}")
    return SyncAction(id=uid(), client_action_id=client_action_id,
                      action_type="edit", status=SyncActionStatus.APPLIED, **kw)


def make_audit(entity_id: str, **kw) -> AuditLogEntry:
    return AuditLogEntry(id=uid(), entity_type="parcel", entity_id=entity_id,
                         action=AuditAction.CREATE, **kw)


def make_conflict(parcel_a_id: str, parcel_b_id: str, **kw) -> Conflict:
    return Conflict(id=uid(), parcel_a_id=parcel_a_id, parcel_b_id=parcel_b_id,
                    conflict_type=ConflictType.OVERLAP, status=ConflictStatus.OPEN, **kw)


def make_export(**kw) -> Export:
    return Export(id=uid(), export_format=ExportFormat.GEOJSON,
                  status=ExportStatus.QUEUED, **kw)


# ─────────────────────────────────────────────────────────────────────────────
# Enum correctness
# ─────────────────────────────────────────────────────────────────────────────

def test_parcel_workflow_statuses():
    assert ParcelWorkflowStatus.DRAFT == "draft"
    assert ParcelWorkflowStatus.APPROVED == "approved"
    assert ParcelWorkflowStatus.REJECTED == "rejected"


def test_job_statuses():
    assert JobStatus.QUEUED == "queued"
    assert JobStatus.COMPLETE == "complete"
    assert JobStatus.FAILED == "failed"


def test_flag_types():
    assert FlagType.OVERLAP == "overlap"
    assert FlagType.GAP == "gap"
    assert FlagType.SELF_INTERSECTION == "self_intersection"


def test_audit_actions():
    assert AuditAction.EDIT == "edit"
    assert AuditAction.APPROVE == "approve"
    assert AuditAction.REJECT == "reject"


# ─────────────────────────────────────────────────────────────────────────────
# State machine
# ─────────────────────────────────────────────────────────────────────────────

def test_valid_transitions():
    assert is_valid_transition(ParcelWorkflowStatus.DRAFT, ParcelWorkflowStatus.VALIDATION_PENDING)
    assert is_valid_transition(ParcelWorkflowStatus.VALIDATED, ParcelWorkflowStatus.APPROVED)
    assert is_valid_transition(ParcelWorkflowStatus.VALIDATED, ParcelWorkflowStatus.REJECTED)


def test_invalid_transitions():
    # Cannot go backwards from approved
    assert not is_valid_transition(ParcelWorkflowStatus.APPROVED, ParcelWorkflowStatus.DRAFT)
    # Cannot skip validation
    assert not is_valid_transition(ParcelWorkflowStatus.DRAFT, ParcelWorkflowStatus.APPROVED)


# ─────────────────────────────────────────────────────────────────────────────
# DB round-trips
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_user_roundtrip(db_session):
    u = make_user()
    db_session.add(u)
    await db_session.flush()
    from sqlalchemy import select
    fetched = (await db_session.execute(select(User).where(User.id == u.id))).scalar_one()
    assert fetched.email == u.email
    assert fetched.role == UserRole.ANALYST


@pytest.mark.anyio
async def test_imagery_tile_roundtrip(db_session):
    tile = make_tile()
    db_session.add(tile)
    await db_session.flush()
    from sqlalchemy import select
    fetched = (await db_session.execute(select(ImageryTile).where(ImageryTile.id == tile.id))).scalar_one()
    assert fetched.filename == "test.tif"
    assert fetched.status == TileStatus.UPLOADED


@pytest.mark.anyio
async def test_processing_job_roundtrip(db_session):
    tile = make_tile()
    db_session.add(tile)
    await db_session.flush()
    job = make_job(tile.id)
    db_session.add(job)
    await db_session.flush()
    from sqlalchemy import select
    fetched = (await db_session.execute(select(ProcessingJob).where(ProcessingJob.id == job.id))).scalar_one()
    assert fetched.job_type == JobType.SEGMENTATION
    assert fetched.status == JobStatus.QUEUED


@pytest.mark.anyio
async def test_parcel_roundtrip(db_session):
    tile = make_tile()
    db_session.add(tile)
    await db_session.flush()
    parcel = make_parcel(tile_id=tile.id, geometry_wkt="POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))")
    db_session.add(parcel)
    await db_session.flush()
    from sqlalchemy import select
    fetched = (await db_session.execute(select(Parcel).where(Parcel.id == parcel.id))).scalar_one()
    assert fetched.confidence == 0.85
    assert fetched.workflow_status == ParcelWorkflowStatus.DRAFT
    assert fetched.geometry_wkt is not None


@pytest.mark.anyio
async def test_building_footprint_roundtrip(db_session):
    tile = make_tile()
    parcel = make_parcel()
    db_session.add_all([tile, parcel])
    await db_session.flush()
    feature = make_feature(tile.id, parcel_id=parcel.id)
    db_session.add(feature)
    await db_session.flush()
    from sqlalchemy import select
    fetched = (await db_session.execute(select(BuildingFootprint).where(BuildingFootprint.id == feature.id))).scalar_one()
    assert fetched.feature_type == FeatureType.BUILDING


@pytest.mark.anyio
async def test_validation_flag_roundtrip(db_session):
    parcel = make_parcel()
    db_session.add(parcel)
    await db_session.flush()
    flag = make_flag(parcel.id)
    db_session.add(flag)
    await db_session.flush()
    from sqlalchemy import select
    fetched = (await db_session.execute(select(ValidationFlag).where(ValidationFlag.id == flag.id))).scalar_one()
    assert fetched.flag_type == FlagType.OVERLAP
    assert fetched.resolved is False


@pytest.mark.anyio
async def test_sync_action_idempotency_key_unique(db_session):
    import sqlalchemy.exc
    key = f"cid-{uid()[:8]}"
    db_session.add(make_sync(client_action_id=key))
    await db_session.flush()
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db_session.add(make_sync(client_action_id=key))
        await db_session.flush()


@pytest.mark.anyio
async def test_audit_log_entry_roundtrip(db_session):
    parcel = make_parcel()
    db_session.add(parcel)
    await db_session.flush()
    entry = make_audit(parcel.id)
    db_session.add(entry)
    await db_session.flush()
    from sqlalchemy import select
    fetched = (await db_session.execute(select(AuditLogEntry).where(AuditLogEntry.id == entry.id))).scalar_one()
    assert fetched.action == AuditAction.CREATE
    assert fetched.entity_type == "parcel"


@pytest.mark.anyio
async def test_all_prd_tables_exist(test_engine):
    from sqlalchemy import inspect
    async with test_engine.connect() as conn:
        tables = await conn.run_sync(lambda c: inspect(c).get_table_names())
    expected = {
        "users", "imagery_tiles", "processing_jobs", "parcels",
        "building_footprints", "validation_flags", "sync_actions",
        "audit_log_entries", "conflicts", "exports",
    }
    for t in expected:
        assert t in tables, f"PRD table '{t}' missing from schema"
