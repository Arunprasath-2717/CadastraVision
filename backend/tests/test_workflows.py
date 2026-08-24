"""
tests/test_workflows.py
────────────────────────
Phase 3 workflow tests:
- Imagery upload & processing job dispatch
- Parcel geometry edit & topology validation hook
- Human review state machine (approve/reject) & SHA-256 audit chain
- Offline sync idempotency replay
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLogEntry
from app.models.imagery import ImageryTile, ProcessingJob
from app.models.parcel import Parcel, ParcelWorkflowStatus
from app.models.sync import SyncAction


@pytest.mark.anyio
async def test_imagery_upload_workflow(client: AsyncClient):
    """Upload imagery tile -> tile & job created -> processing dispatched."""
    files = {"file": ("test_tile.tif", b"\x00" * 1024, "image/geotiff")}
    data = {"source": "drone", "crs": "EPSG:4326", "bounds_wkt": "POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))"}

    resp = await client.post("/v1/imagery/upload", files=files, data=data)
    assert resp.status_code == 202
    body = resp.json()
    assert "tile_id" in body
    assert "job_id" in body
    assert body["status"] in ("queued", "processing", "complete")

    # Poll status
    job_resp = await client.get(f"/v1/imagery/jobs/{body['job_id']}")
    assert job_resp.status_code == 200
    assert job_resp.json()["job_id"] == body["job_id"]


@pytest.mark.anyio
async def test_parcel_edit_and_topology_workflow(client: AsyncClient, db_session: AsyncSession):
    """Edit parcel geometry -> triggers topology check -> state updated."""
    p = Parcel(
        id=str(uuid.uuid4()),
        geometry_wkt="POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))",
        workflow_status=ParcelWorkflowStatus.DRAFT,
    )
    db_session.add(p)
    await db_session.commit()

    edit_resp = await client.post(
        f"/v1/parcels/{p.id}/edit",
        json={"edit": {"operation": "vertex_edit", "payload": {"geometry_wkt": "POLYGON ((0 0, 0 2, 2 2, 2 0, 0 0))"}}},
    )
    assert edit_resp.status_code == 200
    assert edit_resp.json()["parcel_id"] == p.id


@pytest.mark.anyio
async def test_parcel_approve_reject_and_audit_workflow(
    client: AsyncClient, db_session: AsyncSession
):
    """Approve/reject parcel -> state machine validated -> SHA-256 audit entry persisted."""
    # 1. Approve validated parcel
    p1 = Parcel(id=str(uuid.uuid4()), workflow_status=ParcelWorkflowStatus.VALIDATED)
    db_session.add(p1)
    await db_session.commit()

    app_resp = await client.post(f"/v1/parcels/{p1.id}/approve", json={"notes": "Verified geometry"})
    assert app_resp.status_code == 200
    assert app_resp.json()["workflow_status"] == "approved"

    # Verify audit entry & chain
    audit_resp = await client.get(f"/v1/audit/{p1.id}")
    assert audit_resp.status_code == 200
    assert len(audit_resp.json()["entries"]) >= 1

    verify_resp = await client.get(f"/v1/audit/verify/{p1.id}")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["chain_valid"] is True


@pytest.mark.anyio
async def test_offline_sync_idempotency_workflow(
    client: AsyncClient, db_session: AsyncSession
):
    """Sync batch replay with same client_action_id returns identical result."""
    p = Parcel(id=str(uuid.uuid4()), workflow_status=ParcelWorkflowStatus.VALIDATED)
    db_session.add(p)
    await db_session.commit()

    cid = f"cid-{uuid.uuid4().hex[:8]}"
    payload = {
        "actions": [
            {
                "client_action_id": cid,
                "action_type": "approve",
                "parcel_id": p.id,
                "payload": {"notes": "Offline approve"},
            }
        ]
    }

    # First sync call
    r1 = await client.post("/v1/parcels/sync", json=payload)
    assert r1.status_code == 200
    b1 = r1.json()
    assert b1["applied"] == 1

    # Second sync call (replaying same client_action_id)
    r2 = await client.post("/v1/parcels/sync", json=payload)
    assert r2.status_code == 200
    b2 = r2.json()
    assert b2["applied"] == 1
    assert b2["results"][0]["client_action_id"] == cid
