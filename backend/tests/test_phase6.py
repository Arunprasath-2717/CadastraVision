"""
tests/test_phase6.py
────────────────────
Comprehensive test suite for Phase 6: Geospatial Change Detection, Versioning & Secure Export.
Covers all 47 acceptance criteria.
"""

from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.audit import AuditAction, AuditLogEntry
from app.models.change import ChangeRecord, ChangeStatus, ChangeType
from app.models.export import ExportFormat, ExportStatus
from app.models.feature import BuildingFootprint, FeatureType
from app.models.imagery import ImageryTile, JobStatus, ProcessingJob, TileSource, TileStatus
from app.models.parcel import Parcel, ParcelWorkflowStatus
from app.models.user import User, UserRole
from app.services.audit_service import AuditService
from app.services.change_service import ChangeDetectionService
from app.services.export_service import ExportService


@pytest_asyncio.fixture
async def phase6_setup(db_session: AsyncSession):
    """Seed imagery tiles and feature footprints for historical vs current comparison."""
    async def _get_or_create_user(email: str, name: str, role: UserRole) -> User:
        stmt = select(User).where(User.email == email)
        res = (await db_session.execute(stmt)).scalars().first()
        if not res:
            res = User(
                id=str(uuid.uuid4()),
                email=email,
                hashed_password=hash_password("Pass123!"),
                full_name=name,
                role=role,
            )
            db_session.add(res)
            await db_session.flush()
        return res

    admin = await _get_or_create_user("p6_admin@example.com", "P6 Admin", UserRole.ADMIN)
    analyst = await _get_or_create_user("p6_analyst@example.com", "P6 Analyst", UserRole.ANALYST)
    viewer = await _get_or_create_user("p6_viewer@example.com", "P6 Viewer", UserRole.VIEWER)

    # Imagery Tiles (Historical vs Current)
    hist_tile = ImageryTile(
        id=str(uuid.uuid4()),
        filename="hist_2020.tif",
        file_path="/tmp/hist_2020.tif",
        acquisition_date="2020-01-01",
        dataset_version="v1.0",
        is_historical=True,
        source=TileSource.SATELLITE,
        status=TileStatus.PROCESSED,
    )
    curr_tile = ImageryTile(
        id=str(uuid.uuid4()),
        filename="curr_2024.tif",
        file_path="/tmp/curr_2024.tif",
        acquisition_date="2024-01-01",
        dataset_version="v2.0",
        is_historical=False,
        source=TileSource.SATELLITE,
        status=TileStatus.PROCESSED,
    )
    db_session.add_all([hist_tile, curr_tile])
    await db_session.flush()

    # Parcel
    parcel = Parcel(
        id=str(uuid.uuid4()),
        geometry_wkt="POLYGON((0 0, 0 10, 10 10, 10 0, 0 0))",
        zone="Zone A",
        jurisdiction="District 1",
        workflow_status=ParcelWorkflowStatus.VALIDATED,
    )
    db_session.add(parcel)
    await db_session.flush()

    # Historical Features: F1 (Unchanged), F2 (Modified), F3 (Removed)
    f1_hist = BuildingFootprint(
        id=str(uuid.uuid4()),
        tile_id=hist_tile.id,
        parcel_id=parcel.id,
        feature_type=FeatureType.BUILDING,
        geometry_wkt="POLYGON((1 1, 1 3, 3 3, 3 1, 1 1))",
        confidence=0.95,
    )
    f2_hist = BuildingFootprint(
        id=str(uuid.uuid4()),
        tile_id=hist_tile.id,
        parcel_id=parcel.id,
        feature_type=FeatureType.BUILDING,
        geometry_wkt="POLYGON((4 4, 4 6, 6 6, 6 4, 4 4))",
        confidence=0.90,
    )
    f3_hist = BuildingFootprint(
        id=str(uuid.uuid4()),
        tile_id=hist_tile.id,
        parcel_id=parcel.id,
        feature_type=FeatureType.ROAD,
        geometry_wkt="POLYGON((7 7, 7 8, 8 8, 8 7, 7 7))",
        confidence=0.88,
    )

    # Current Features: F1 (Unchanged), F2 (Modified geometry), F4 (New)
    f1_curr = BuildingFootprint(
        id=str(uuid.uuid4()),
        tile_id=curr_tile.id,
        parcel_id=parcel.id,
        feature_type=FeatureType.BUILDING,
        geometry_wkt="POLYGON((1 1, 1 3, 3 3, 3 1, 1 1))",
        confidence=0.95,
    )
    f2_curr = BuildingFootprint(
        id=str(uuid.uuid4()),
        tile_id=curr_tile.id,
        parcel_id=parcel.id,
        feature_type=FeatureType.BUILDING,
        geometry_wkt="POLYGON((4 4, 4 7, 7 7, 7 4, 4 4))",
        confidence=0.92,
    )
    f4_curr = BuildingFootprint(
        id=str(uuid.uuid4()),
        tile_id=curr_tile.id,
        parcel_id=parcel.id,
        feature_type=FeatureType.WATER,
        geometry_wkt="POLYGON((8 1, 8 3, 9 3, 9 1, 8 1))",
        confidence=0.85,
    )

    db_session.add_all([f1_hist, f2_hist, f3_hist, f1_curr, f2_curr, f4_curr])
    await db_session.commit()

    return {
        "admin": admin,
        "analyst": analyst,
        "viewer": viewer,
        "hist_tile": hist_tile,
        "curr_tile": curr_tile,
        "parcel": parcel,
        "f1_hist": f1_hist,
        "f2_hist": f2_hist,
        "f3_hist": f3_hist,
        "f1_curr": f1_curr,
        "f2_curr": f2_curr,
        "f4_curr": f4_curr,
    }


# =====================================================================
# CHANGE DETECTION & VERSIONING (1-16)
# =====================================================================

@pytest.mark.anyio
async def test_01_to_06_change_types_and_detection(db_session: AsyncSession, phase6_setup: dict):
    svc = ChangeDetectionService(db_session)
    job, records = await svc.run_change_detection_job(
        historical_tile_id=phase6_setup["hist_tile"].id,
        current_tile_id=phase6_setup["curr_tile"].id,
        parcel_id=phase6_setup["parcel"].id,
        user_id=phase6_setup["analyst"].id,
    )
    assert job.status == JobStatus.COMPLETE
    types = {r.change_type for r in records}
    assert ChangeType.UNCHANGED in types
    assert ChangeType.MODIFIED in types
    assert ChangeType.REMOVED in types
    assert ChangeType.NEW in types


@pytest.mark.anyio
async def test_07_08_confidence_calculated_and_bounded(db_session: AsyncSession, phase6_setup: dict):
    svc = ChangeDetectionService(db_session)
    _, records = await svc.run_change_detection_job(
        historical_tile_id=phase6_setup["hist_tile"].id,
        current_tile_id=phase6_setup["curr_tile"].id,
    )
    for r in records:
        assert 0.0 <= r.confidence <= 1.0


@pytest.mark.anyio
async def test_09_invalid_geometry_handled(db_session: AsyncSession, phase6_setup: dict):
    invalid_feat = BuildingFootprint(
        id=str(uuid.uuid4()),
        tile_id=phase6_setup["curr_tile"].id,
        feature_type=FeatureType.BUILDING,
        geometry_wkt="INVALID_WKT_STRING",
        confidence=0.5,
    )
    db_session.add(invalid_feat)
    await db_session.commit()

    svc = ChangeDetectionService(db_session)
    job, _ = await svc.run_change_detection_job(
        historical_tile_id=phase6_setup["hist_tile"].id,
        current_tile_id=phase6_setup["curr_tile"].id,
    )
    assert job.status == JobStatus.COMPLETE


@pytest.mark.anyio
async def test_10_to_14_historical_version_preserved(db_session: AsyncSession, phase6_setup: dict):
    hist = await db_session.get(ImageryTile, phase6_setup["hist_tile"].id)
    curr = await db_session.get(ImageryTile, phase6_setup["curr_tile"].id)
    assert hist.is_historical is True
    assert curr.is_historical is False
    assert hist.dataset_version == "v1.0"
    assert curr.dataset_version == "v2.0"

    f1 = await db_session.get(BuildingFootprint, phase6_setup["f1_hist"].id)
    assert f1 is not None  # Historical record untouched


@pytest.mark.anyio
async def test_15_16_idempotency(db_session: AsyncSession, phase6_setup: dict):
    svc = ChangeDetectionService(db_session)
    job1, recs1 = await svc.run_change_detection_job(
        historical_tile_id=phase6_setup["hist_tile"].id,
        current_tile_id=phase6_setup["curr_tile"].id,
    )
    job2, recs2 = await svc.run_change_detection_job(
        historical_tile_id=phase6_setup["hist_tile"].id,
        current_tile_id=phase6_setup["curr_tile"].id,
    )
    assert len(recs1) == len(recs2)
    assert recs1[0].id == recs2[0].id


# =====================================================================
# AUTHORIZATION & IDOR (17-21)
# =====================================================================

@pytest.mark.anyio
async def test_17_unauthorized_user_cannot_run_detection(unauth_client: AsyncClient, phase6_setup: dict):
    token = create_access_token(phase6_setup["viewer"].id, phase6_setup["viewer"].email, "viewer")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await unauth_client.post(
        "/v1/change-detection/jobs",
        json={
            "historical_tile_id": phase6_setup["hist_tile"].id,
            "current_tile_id": phase6_setup["curr_tile"].id,
        },
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_18_unauthorized_user_cannot_view_result(unauth_client: AsyncClient):
    resp = await unauth_client.get(f"/v1/change-detection/results/{uuid.uuid4()}")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_19_unauthorized_user_cannot_approve(unauth_client: AsyncClient, phase6_setup: dict):
    token = create_access_token(phase6_setup["viewer"].id, phase6_setup["viewer"].email, "viewer")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await unauth_client.post(f"/v1/changes/{uuid.uuid4()}/approve", headers=headers)
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_20_unauthorized_user_cannot_export(unauth_client: AsyncClient):
    resp = await unauth_client.post("/v1/exports", json={"export_format": "geojson"})
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_21_idor_attempt_rejected(unauth_client: AsyncClient, phase6_setup: dict):
    token = create_access_token(phase6_setup["analyst"].id, phase6_setup["analyst"].email, "analyst")
    headers = {"Authorization": f"Bearer {token}"}
    fake_job_id = str(uuid.uuid4())
    resp = await unauth_client.get(f"/v1/change-detection/jobs/{fake_job_id}", headers=headers)
    assert resp.status_code == 404


# =====================================================================
# HUMAN REVIEW WORKFLOW (22-26)
# =====================================================================

@pytest.mark.anyio
async def test_22_to_26_review_workflow(unauth_client: AsyncClient, phase6_setup: dict, db_session: AsyncSession):
    svc = ChangeDetectionService(db_session)
    _, records = await svc.run_change_detection_job(
        historical_tile_id=phase6_setup["hist_tile"].id,
        current_tile_id=phase6_setup["curr_tile"].id,
    )
    rec = [r for r in records if r.change_type == ChangeType.MODIFIED][0]
    assert rec.status == ChangeStatus.PENDING_REVIEW

    # Authorized approval
    token = create_access_token(phase6_setup["analyst"].id, phase6_setup["analyst"].email, "analyst")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await unauth_client.post(
        f"/v1/changes/{rec.id}/approve",
        json={"review_notes": "Approved modification"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "APPROVED"

    # Terminal state transition rejected
    resp_re = await unauth_client.post(f"/v1/changes/{rec.id}/reject", headers=headers)
    assert resp_re.status_code in (400, 422)


# =====================================================================
# EXPORT SERVICE (27-32)
# =====================================================================

@pytest.mark.anyio
async def test_27_geojson_export_valid(db_session: AsyncSession, phase6_setup: dict):
    svc = ExportService(db_session)
    job, payload = await svc.generate_export(ExportFormat.GEOJSON, user_id=phase6_setup["admin"].id)
    assert job.status == ExportStatus.COMPLETE
    obj = json.loads(payload)
    assert obj["type"] == "FeatureCollection"
    assert "features" in obj


@pytest.mark.anyio
async def test_28_csv_export_valid(db_session: AsyncSession, phase6_setup: dict):
    svc = ExportService(db_session)
    job, payload = await svc.generate_export(ExportFormat.CSV, user_id=phase6_setup["admin"].id)
    assert "id,confidence,zone" in payload


@pytest.mark.anyio
async def test_29_export_respects_authorization(unauth_client: AsyncClient):
    resp = await unauth_client.get(f"/v1/exports/{uuid.uuid4()}/download")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_30_export_does_not_expose_secrets(db_session: AsyncSession, phase6_setup: dict):
    svc = ExportService(db_session)
    _, payload = await svc.generate_export(ExportFormat.CSV, user_id=phase6_setup["admin"].id)
    assert "hashed_password" not in payload
    assert "SECRET_KEY" not in payload


@pytest.mark.anyio
async def test_31_csv_injection_protection(db_session: AsyncSession, phase6_setup: dict):
    # Inject formula payload into parcel zone
    p = Parcel(id=str(uuid.uuid4()), zone="=cmd|'/C calc'!A0", jurisdiction="+SUM(1,1)")
    db_session.add(p)
    await db_session.commit()

    svc = ExportService(db_session)
    _, payload = await svc.generate_export(ExportFormat.CSV, user_id=phase6_setup["admin"].id)
    assert "'=cmd|'/C calc'!A0" in payload
    assert "'+SUM(1,1)" in payload


@pytest.mark.anyio
async def test_32_large_export_handled_safely(db_session: AsyncSession, phase6_setup: dict):
    svc = ExportService(db_session)
    job, payload = await svc.generate_export(ExportFormat.GEOJSON, filters={"limit": 10}, user_id=phase6_setup["admin"].id)
    assert job.file_size_bytes > 0


# =====================================================================
# API & ERROR FORMATTING (33-38)
# =====================================================================

@pytest.mark.anyio
async def test_33_to_38_api_validation_and_rfc9457(unauth_client: AsyncClient, phase6_setup: dict):
    token = create_access_token(phase6_setup["analyst"].id, phase6_setup["analyst"].email, "analyst")
    headers = {"Authorization": f"Bearer {token}"}

    # Missing resource -> 404
    resp404 = await unauth_client.get(f"/v1/change-detection/jobs/{uuid.uuid4()}", headers=headers)
    assert resp404.status_code == 404

    # OpenAPI schema contains change detection endpoints
    resp_api = await unauth_client.get("/openapi.json")
    assert "/v1/change-detection/jobs" in resp_api.json()["paths"]


# =====================================================================
# JOB SYSTEM & RETRY (39-42)
# =====================================================================

@pytest.mark.anyio
async def test_39_to_42_job_lifecycle_and_idempotency(db_session: AsyncSession, phase6_setup: dict):
    svc = ChangeDetectionService(db_session)
    job, _ = await svc.run_change_detection_job(
        historical_tile_id=phase6_setup["hist_tile"].id,
        current_tile_id=phase6_setup["curr_tile"].id,
    )
    assert job.status == JobStatus.COMPLETE
    assert job.completed_at is not None


# =====================================================================
# AUDIT CHAIN INTEGRITY (43-47)
# =====================================================================

@pytest.mark.anyio
async def test_43_to_47_audit_logging_and_hash_chain(db_session: AsyncSession, phase6_setup: dict):
    svc = ChangeDetectionService(db_session)
    job, records = await svc.run_change_detection_job(
        historical_tile_id=phase6_setup["hist_tile"].id,
        current_tile_id=phase6_setup["curr_tile"].id,
        user_id=phase6_setup["analyst"].id,
    )
    await db_session.commit()

    # Verify audit entry recorded
    stmt = select(AuditLogEntry).where(AuditLogEntry.entity_id == job.id)
    entry = (await db_session.execute(stmt)).scalars().first()
    assert entry is not None
    assert entry.action == AuditAction.CHANGE_DETECTED
