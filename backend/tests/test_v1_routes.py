"""
tests/test_v1_routes.py
────────────────────────
Phase 2 & Phase 3 — verify all PRD-CM-03 endpoint catalogue routes exist
in the generated OpenAPI schema and return real DB responses.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.imagery import ImageryTile, JobStatus, JobType, ProcessingJob, TileSource, TileStatus
from app.models.parcel import Parcel, ParcelWorkflowStatus

PRD_ENDPOINTS = [
    # Auth
    ("POST", "/v1/auth/token"),
    ("POST", "/v1/auth/refresh"),
    # Imagery
    ("POST", "/v1/imagery/upload"),
    ("GET",  "/v1/imagery/jobs/{job_id}"),
    ("GET",  "/v1/imagery/tiles/{tile_id}"),
    ("GET",  "/v1/imagery/tiles/{tile_id}/features"),
    # Parcels
    ("GET",  "/v1/parcels"),
    ("GET",  "/v1/parcels/{parcel_id}"),
    ("POST", "/v1/parcels/{parcel_id}/edit"),
    ("POST", "/v1/parcels/{parcel_id}/approve"),
    ("POST", "/v1/parcels/{parcel_id}/reject"),
    ("POST", "/v1/parcels/sync"),
    # Validation
    ("GET",  "/v1/validations/queue"),
    ("POST", "/v1/validations/run"),
    ("GET",  "/v1/parcels/{parcel_id}/flags"),
    # Conflicts
    ("GET",  "/v1/conflicts"),
    ("POST", "/v1/conflicts/{conflict_id}/resolve"),
    # Change Detection
    ("POST", "/v1/change-detection/run"),
    ("GET",  "/v1/change-detection/{job_id}"),
    # Geo
    ("GET",  "/v1/geo/parcels"),
    # Exports
    ("POST", "/v1/exports"),
    ("GET",  "/v1/exports/{export_id}"),
    # Audit
    ("GET",  "/v1/audit/{parcel_id}"),
    ("GET",  "/v1/audit/verify/{parcel_id}"),
    ("GET",  "/v1/audit/export/{batch_id}"),
    # Metrics
    ("GET",  "/v1/models/metrics"),
]


@pytest.mark.anyio
async def test_openapi_all_prd_routes(client: AsyncClient):
    """Every PRD endpoint must appear in /openapi.json."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    paths = spec.get("paths", {})

    missing = []
    for method, path in PRD_ENDPOINTS:
        if path not in paths:
            missing.append(f"{method} {path} — path missing")
        elif method.lower() not in paths[path]:
            missing.append(f"{method} {path} — method missing (available: {list(paths[path].keys())})")

    assert not missing, "PRD endpoints missing from OpenAPI:\n" + "\n".join(missing)


@pytest.mark.anyio
async def test_openapi_v1_prefix(client: AsyncClient):
    """All domain routes must use /v1 prefix."""
    response = await client.get("/openapi.json")
    spec = response.json()
    domain_paths = [p for p in spec["paths"] if p != "/health"]
    non_v1 = [p for p in domain_paths if not p.startswith("/v1/")]
    assert not non_v1, f"Non-/v1 domain paths found: {non_v1}"


@pytest.mark.anyio
async def test_auth_token_stub(client: AsyncClient):
    resp = await client.post("/v1/auth/token", json={"username": "test_admin@cadastravision.org", "password": "AdminPass123!"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.anyio
async def test_auth_refresh_stub(client: AsyncClient):
    login_resp = await client.post("/v1/auth/token", json={"username": "test_admin@cadastravision.org", "password": "AdminPass123!"})
    refresh_tok = login_resp.json()["refresh_token"]
    resp = await client.post("/v1/auth/refresh", json={"refresh_token": refresh_tok})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.anyio
async def test_imagery_job_status(client: AsyncClient, db_session: AsyncSession):
    tile = ImageryTile(id=str(uuid.uuid4()), filename="test.tif", file_path="/tmp/test.tif")
    db_session.add(tile)
    await db_session.flush()
    job = ProcessingJob(id=str(uuid.uuid4()), tile_id=tile.id, job_type=JobType.SEGMENTATION, status=JobStatus.QUEUED)
    db_session.add(job)
    await db_session.commit()

    resp = await client.get(f"/v1/imagery/jobs/{job.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == job.id
    assert body["status"] in ("queued", "processing", "complete", "failed")


@pytest.mark.anyio
async def test_imagery_tile(client: AsyncClient, db_session: AsyncSession):
    tile = ImageryTile(id=str(uuid.uuid4()), filename="test.tif", file_path="/tmp/test.tif")
    db_session.add(tile)
    await db_session.commit()

    resp = await client.get(f"/v1/imagery/tiles/{tile.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["tile_id"] == tile.id


@pytest.mark.anyio
async def test_imagery_tile_features(client: AsyncClient):
    resp = await client.get("/v1/imagery/tiles/test-tile-id/features")
    assert resp.status_code == 200
    body = resp.json()
    assert "features" in body
    assert "total" in body


@pytest.mark.anyio
async def test_parcel_list(client: AsyncClient, db_session: AsyncSession):
    p = Parcel(id=str(uuid.uuid4()), zone="urban", confidence=0.9, workflow_status=ParcelWorkflowStatus.DRAFT)
    db_session.add(p)
    await db_session.commit()

    resp = await client.get("/v1/parcels")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert len(body["items"]) >= 1


@pytest.mark.anyio
async def test_parcel_list_with_filters(client: AsyncClient, db_session: AsyncSession):
    p = Parcel(id=str(uuid.uuid4()), zone="urban", confidence=0.85, workflow_status=ParcelWorkflowStatus.DRAFT)
    db_session.add(p)
    await db_session.commit()

    resp = await client.get("/v1/parcels?limit=5&zone=urban&confidence_min=0.7")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) >= 1


@pytest.mark.anyio
async def test_parcel_detail(client: AsyncClient, db_session: AsyncSession):
    p = Parcel(id=str(uuid.uuid4()), zone="rural", confidence=0.95, workflow_status=ParcelWorkflowStatus.DRAFT)
    db_session.add(p)
    await db_session.commit()

    resp = await client.get(f"/v1/parcels/{p.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["parcel_id"] == p.id


@pytest.mark.anyio
async def test_parcel_edit(client: AsyncClient, db_session: AsyncSession):
    p = Parcel(id=str(uuid.uuid4()), geometry_wkt="POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))", workflow_status=ParcelWorkflowStatus.DRAFT)
    db_session.add(p)
    await db_session.commit()

    resp = await client.post(
        f"/v1/parcels/{p.id}/edit",
        json={"edit": {"operation": "vertex_edit", "payload": {"geometry_wkt": "POLYGON ((0 0, 0 2, 2 2, 2 0, 0 0))"}}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["parcel_id"] == p.id


@pytest.mark.anyio
async def test_parcel_approve(client: AsyncClient, db_session: AsyncSession):
    p = Parcel(id=str(uuid.uuid4()), workflow_status=ParcelWorkflowStatus.VALIDATED)
    db_session.add(p)
    await db_session.commit()

    resp = await client.post(f"/v1/parcels/{p.id}/approve", json={"notes": "LGTM"})
    assert resp.status_code == 200
    assert resp.json()["workflow_status"] == "approved"


@pytest.mark.anyio
async def test_parcel_reject(client: AsyncClient, db_session: AsyncSession):
    p = Parcel(id=str(uuid.uuid4()), workflow_status=ParcelWorkflowStatus.VALIDATED)
    db_session.add(p)
    await db_session.commit()

    resp = await client.post(f"/v1/parcels/{p.id}/reject", json={"reason": "Low confidence geometry"})
    assert resp.status_code == 200
    assert resp.json()["workflow_status"] == "rejected"


@pytest.mark.anyio
async def test_parcel_sync(client: AsyncClient, db_session: AsyncSession):
    p = Parcel(id=str(uuid.uuid4()), workflow_status=ParcelWorkflowStatus.VALIDATED)
    db_session.add(p)
    await db_session.commit()

    resp = await client.post(
        "/v1/parcels/sync",
        json={"actions": [{"client_action_id": f"cid-{uuid.uuid4().hex[:6]}", "action_type": "approve", "parcel_id": p.id, "payload": {"notes": "Batch approve"}}]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["applied"] == 1
    assert body["conflicts"] == 0


@pytest.mark.anyio
async def test_validations_queue_stub(client: AsyncClient):
    resp = await client.get("/v1/validations/queue")
    assert resp.status_code == 200
    assert "items" in resp.json()


@pytest.mark.anyio
async def test_validations_run_stub(client: AsyncClient):
    resp = await client.post("/v1/validations/run", json={"parcel_ids": ["p1", "p2"]})
    assert resp.status_code == 200
    assert "job_id" in resp.json()


@pytest.mark.anyio
async def test_parcel_flags_stub(client: AsyncClient):
    resp = await client.get("/v1/parcels/parcel-abc/flags")
    assert resp.status_code == 200
    body = resp.json()
    assert "flags" in body
    assert "total" in body


@pytest.mark.anyio
async def test_conflicts_list_stub(client: AsyncClient):
    resp = await client.get("/v1/conflicts")
    assert resp.status_code == 200
    assert "items" in resp.json()


@pytest.mark.anyio
async def test_conflict_resolve_stub(client: AsyncClient):
    resp = await client.post(
        "/v1/conflicts/conflict-123/resolve",
        json={"resolution": "keep_a", "notes": "parcel A is correct"},
    )
    assert resp.status_code == 200
    assert "conflict_id" in resp.json()


@pytest.mark.anyio
async def test_change_detection_run_stub(client: AsyncClient):
    resp = await client.post(
        "/v1/change-detection/run",
        json={"tile_id_before": "t1", "tile_id_after": "t2"},
    )
    assert resp.status_code in (200, 202)
    assert "job_id" in resp.json()


@pytest.mark.anyio
async def test_change_detection_status_stub(client: AsyncClient):
    resp = await client.get("/v1/change-detection/job-abc")
    assert resp.status_code == 200
    assert resp.json()["job_id"] == "job-abc"


@pytest.mark.anyio
async def test_geo_parcels_stub(client: AsyncClient):
    resp = await client.get("/v1/geo/parcels")
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "FeatureCollection"


@pytest.mark.anyio
async def test_exports_create_stub(client: AsyncClient):
    resp = await client.post("/v1/exports", json={"export_format": "geojson"})
    assert resp.status_code == 202
    assert resp.json()["status"] == "queued"


@pytest.mark.anyio
async def test_exports_status_stub(client: AsyncClient):
    resp = await client.get("/v1/exports/export-123")
    assert resp.status_code == 200
    assert resp.json()["export_id"] == "export-123"


@pytest.mark.anyio
async def test_audit_trail_stub(client: AsyncClient):
    resp = await client.get("/v1/audit/parcel-abc")
    assert resp.status_code == 200
    body = resp.json()
    assert "entries" in body
    assert body["parcel_id"] == "parcel-abc"


@pytest.mark.anyio
async def test_audit_verify_stub(client: AsyncClient):
    resp = await client.get("/v1/audit/verify/parcel-abc")
    assert resp.status_code == 200
    assert "chain_valid" in resp.json()


@pytest.mark.anyio
async def test_audit_export_stub(client: AsyncClient):
    resp = await client.get("/v1/audit/export/batch-001")
    assert resp.status_code == 200
    assert resp.json()["batch_id"] == "batch-001"


@pytest.mark.anyio
async def test_metrics_stub(client: AsyncClient):
    resp = await client.get("/v1/models/metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert "model_name" in body
    assert "model_version" in body
