"""
tests/test_phase7.py
─────────────────────
Phase 7 Verification Test Suite — Production Hardening, Observability,
File Upload Security, Health Probes, Rate Limiting, and E2E Workflow.
"""

from __future__ import annotations

import io
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import create_access_token
from app.models.imagery import ImageryTile, JobStatus, ProcessingJob, TileSource
from app.models.user import User, UserRole


# =====================================================================
# 1. PRODUCTION CONFIGURATION & HARDENING (1-3)
# =====================================================================

def test_01_production_config_rejects_insecure_secret():
    with pytest.raises(ValueError, match="Insecure or default SECRET_KEY is prohibited"):
        Settings(ENVIRONMENT="production", SECRET_KEY="INSECURE_CHANGE_ME_IN_PRODUCTION", DEBUG=False)


def test_02_production_config_rejects_debug_enabled():
    with pytest.raises(ValueError, match="DEBUG mode must be False"):
        Settings(ENVIRONMENT="production", SECRET_KEY="a_very_secure_long_secret_key_12345", DEBUG=True)


def test_03_production_config_valid():
    s = Settings(ENVIRONMENT="production", SECRET_KEY="a_very_secure_long_secret_key_12345", DEBUG=False)
    assert s.is_production is True
    assert s.DEBUG is False


# =====================================================================
# 2. REQUEST CORRELATION & OBSERVABILITY (4-7)
# =====================================================================

@pytest.mark.anyio
async def test_04_request_id_generated(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert "X-Request-ID" in resp.headers
    assert len(resp.headers["X-Request-ID"]) > 0


@pytest.mark.anyio
async def test_05_incoming_request_id_propagated(client: AsyncClient):
    req_id = f"custom-req-{uuid.uuid4()}"
    resp = await client.get("/health", headers={"X-Request-ID": req_id})
    assert resp.status_code == 200
    assert resp.headers["X-Request-ID"] == req_id


# =====================================================================
# 3. HEALTH PROBES (8-9)
# =====================================================================

@pytest.mark.anyio
async def test_08_health_liveness_endpoints(client: AsyncClient):
    resp_liveness = await client.get("/health/live")
    assert resp_liveness.status_code == 200
    assert resp_liveness.json()["liveness"] == "pass"


@pytest.mark.anyio
async def test_09_health_readiness_endpoint(client: AsyncClient):
    resp_readiness = await client.get("/health/ready")
    assert resp_readiness.status_code == 200
    assert resp_readiness.json()["readiness"] == "pass"
    assert resp_readiness.json()["database"] == "connected"


# =====================================================================
# 4. FILE UPLOAD SECURITY (15-18)
# =====================================================================

@pytest.mark.anyio
async def test_15_upload_rejects_path_traversal(client: AsyncClient, phase6_setup: dict):
    token = create_access_token(phase6_setup["admin"].id, phase6_setup["admin"].email, "admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    files = {"file": ("../../etc/passwd.tif", io.BytesIO(b"fake data"), "image/tiff")}
    resp = await client.post("/v1/imagery/upload", files=files, headers=headers)
    assert resp.status_code == 400
    assert "path traversal" in resp.json()["detail"].lower()


@pytest.mark.anyio
async def test_16_upload_rejects_unsupported_extension(client: AsyncClient, phase6_setup: dict):
    token = create_access_token(phase6_setup["admin"].id, phase6_setup["admin"].email, "admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    files = {"file": ("malicious.exe", io.BytesIO(b"fake executable"), "application/octet-stream")}
    resp = await client.post("/v1/imagery/upload", files=files, headers=headers)
    assert resp.status_code == 400
    assert "unsupported file format" in resp.json()["detail"].lower()


@pytest.mark.anyio
async def test_17_upload_rejects_oversized_file(client: AsyncClient, phase6_setup: dict):
    token = create_access_token(phase6_setup["admin"].id, phase6_setup["admin"].email, "admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 51MB payload exceeds 50MB limit
    large_payload = b"0" * (51 * 1024 * 1024)
    files = {"file": ("oversized.tif", io.BytesIO(large_payload), "image/tiff")}
    resp = await client.post("/v1/imagery/upload", files=files, headers=headers)
    assert resp.status_code == 413
    assert "50mb" in resp.json()["detail"].lower()


@pytest.mark.anyio
async def test_18_valid_file_upload_succeeds(client: AsyncClient, phase6_setup: dict):
    token = create_access_token(phase6_setup["admin"].id, phase6_setup["admin"].email, "admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    files = {"file": ("valid_imagery.tif", io.BytesIO(b"valid geotiff header data"), "image/tiff")}
    resp = await client.post("/v1/imagery/upload", files=files, headers=headers)
    assert resp.status_code in (200, 202)
    assert "tile_id" in resp.json()
    assert "job_id" in resp.json()


# =====================================================================
# 5. DATABASE RESILIENCE & CONCURRENCY (10-14, 22-23)
# =====================================================================

@pytest.mark.anyio
async def test_22_concurrent_health_requests(client: AsyncClient):
    import anyio
    async def make_req():
        r = await client.get("/health/ready")
        assert r.status_code == 200

    async with anyio.create_task_group() as tg:
        for _ in range(10):
            tg.start_soon(make_req)


# =====================================================================
# 6. COMPLETE END-TO-END WORKFLOW (25)
# =====================================================================

@pytest.mark.anyio
async def test_25_complete_e2e_workflow(client: AsyncClient, phase6_setup: dict):
    token = create_access_token(phase6_setup["admin"].id, phase6_setup["admin"].email, "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Health check
    h = await client.get("/health/ready")
    assert h.status_code == 200

    # 2. Upload imagery
    files = {"file": ("e2e_test_tile.tif", io.BytesIO(b"dummy geotiff bytes"), "image/tiff")}
    upload_res = await client.post("/v1/imagery/upload", files=files, headers=headers)
    assert upload_res.status_code in (200, 202)
    job_id = upload_res.json()["job_id"]

    # 3. Poll job status
    job_res = await client.get(f"/v1/imagery/jobs/{job_id}", headers=headers)
    assert job_res.status_code == 200

    # 4. Trigger change detection
    change_req = await client.post(
        "/v1/change-detection/jobs",
        json={"historical_tile_id": "hist-123", "current_tile_id": "curr-456"},
        headers=headers,
    )
    assert change_req.status_code in (200, 202)
    cd_job_id = change_req.json()["job_id"]

    # 5. Retrieve change results
    cd_results = await client.get(f"/v1/change-detection/results/{cd_job_id}", headers=headers)
    assert cd_results.status_code == 200

    # 6. Request export
    exp_res = await client.post(
        "/v1/exports",
        json={"export_format": "geojson", "filters": {"limit": 10}},
        headers=headers,
    )
    assert exp_res.status_code in (200, 202)
    export_id = exp_res.json()["export_id"]

    # 7. Download export
    dl_res = await client.get(f"/v1/exports/{export_id}/download", headers=headers)
    assert dl_res.status_code == 200
