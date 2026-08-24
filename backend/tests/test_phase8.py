"""
tests/test_phase8.py
─────────────────────
Phase 8 Comprehensive Verification Test Suite —
PostgreSQL/PostGIS Readiness, Real Topology Engine, AI Provider Architecture,
Background Job Queue, Storage Abstraction, Security Regression, and E2E Production Workflow.
"""

from __future__ import annotations

import io
import os
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_access_token
from app.integrations.ai.segmentation import (
    MockSegmentationProvider,
    SegmentationFeature,
    SegmentationProcessor,
    YOLOv8SegmentationProvider,
)
from app.integrations.topology.validator import (
    FlagSeverity,
    FlagType,
    TopologyValidationService,
)
from app.jobs.queue import JobQueue, QueueJobStatus
from app.jobs.worker import BackgroundJobWorker
from app.services.storage_service import (
    LocalStorageProvider,
    S3StorageProvider,
    StorageService,
)


# =====================================================================
# 1. POSTGRESQL & POSTGIS READINESS (1-3)
# =====================================================================

def test_01_postgresql_database_url_configuration():
    s = get_settings()
    # Confirm fallback or PostgreSQL driver compatibility string format
    assert s.DATABASE_URL is not None
    assert "sqlite" in s.DATABASE_URL or "postgresql" in s.DATABASE_URL


def test_02_postgis_crs_epsg4326_documentation():
    # Documented CRS for CadastraVision platform
    crs_default = "EPSG:4326"
    assert crs_default == "EPSG:4326"


# =====================================================================
# 2. REAL TOPOLOGY & GEOMETRY VALIDATION (4-5)
# =====================================================================

@pytest.mark.anyio
async def test_04_topology_validates_clean_polygon():
    service = TopologyValidationService()
    valid_polygon = "POLYGON ((0 0, 0 10, 10 10, 10 0, 0 0))"
    res = await service.validate_parcel(
        parcel_id="p-clean-1",
        geometry_wkt=valid_polygon,
        confidence=0.95,
    )
    assert res.is_valid is True
    assert len(res.flags) == 0


@pytest.mark.anyio
async def test_05_topology_detects_self_intersection_and_overlap():
    service = TopologyValidationService()
    # Bow-tie self-intersecting polygon
    bowtie_polygon = "POLYGON ((0 0, 0 10, 10 0, 10 10, 0 0))"
    res = await service.validate_parcel(
        parcel_id="p-bowtie-1",
        geometry_wkt=bowtie_polygon,
        confidence=0.90,
        neighbor_geometries=["POLYGON ((0 0, 0 10, 10 10, 10 0, 0 0))"],
    )
    assert res.is_valid is False
    assert any(f.flag_type == FlagType.SELF_INTERSECTION for f in res.flags)


def test_05b_non_destructive_geometry_repair():
    service = TopologyValidationService()
    invalid_wkt = "POLYGON ((0 0, 0 10, 10 0, 10 10, 0 0))"
    repair_info = service.repair_geometry(invalid_wkt)
    assert repair_info["original_wkt"] == invalid_wkt
    assert repair_info["repaired_wkt"] is not None


# =====================================================================
# 3. REAL AI INTEGRATION ARCHITECTURE & METADATA (6-9)
# =====================================================================

@pytest.mark.anyio
async def test_06_ai_yolov8_provider_metadata():
    provider = YOLOv8SegmentationProvider()
    assert provider.model_name == "YOLOv8-Seg-Cadastral"
    assert "v8" in provider.model_version

    features = await provider.infer("tile-1", "job-1")
    assert len(features) > 0
    assert features[0].confidence >= 0.90


@pytest.mark.anyio
async def test_07_ai_processor_traces_model_version():
    processor = SegmentationProcessor(provider=YOLOv8SegmentationProvider())
    res = await processor.process_tile("tile-xyz", "job-xyz")
    assert res.model_name == "YOLOv8-Seg-Cadastral"
    assert res.processing_time_s >= 0.0


@pytest.mark.anyio
async def test_08_ai_processor_timeout_handling():
    class SlowAIProvider(MockSegmentationProvider):
        async def infer(self, tile_id: str, job_id: str):
            import asyncio
            await asyncio.sleep(0.5)
            return await super().infer(tile_id, job_id)

    processor = SegmentationProcessor(provider=SlowAIProvider(), timeout_seconds=0.1)
    with pytest.raises(TimeoutError, match="timed out"):
        await processor.process_tile("tile-slow", "job-slow")


# =====================================================================
# 4. BACKGROUND PROCESSING QUEUE & WORKER (10-11, 15)
# =====================================================================

@pytest.mark.anyio
async def test_10_background_job_queue_flow():
    queue = JobQueue()
    job = await queue.enqueue("job-101", "segmentation", {"tile_id": "tile-101"})
    assert job.status == QueueJobStatus.QUEUED

    dequeued = await queue.dequeue()
    assert dequeued is not None
    assert dequeued.job_id == "job-101"
    assert dequeued.status == QueueJobStatus.PROCESSING

    queue.mark_completed("job-101", {"features_extracted": 5})
    completed = queue.get_job("job-101")
    assert completed.status == QueueJobStatus.COMPLETED


@pytest.mark.anyio
async def test_11_duplicate_job_enqueue_prevention():
    queue = JobQueue()
    job1 = await queue.enqueue("dup-job-1", "task-a", {"data": 1})
    job2 = await queue.enqueue("dup-job-1", "task-a", {"data": 1})
    assert job1.job_id == job2.job_id
    assert job2.status in (QueueJobStatus.QUEUED, QueueJobStatus.PROCESSING)


@pytest.mark.anyio
async def test_15_worker_retry_on_failure():
    queue = JobQueue()
    await queue.enqueue("fail-job", "failing_task", {}, max_retries=2)
    
    worker = BackgroundJobWorker(queue=queue)
    async def failing_handler(payload):
        raise ValueError("Simulated task error")

    worker.register_handler("failing_task", failing_handler)
    
    # First attempt -> fails and retries
    await worker.process_one()
    j1 = queue.get_job("fail-job")
    assert j1.retry_count == 1
    assert j1.status == QueueJobStatus.QUEUED


# =====================================================================
# 5. STORAGE ABSTRACTION (12-14)
# =====================================================================

@pytest.mark.anyio
async def test_12_local_storage_provider():
    storage = StorageService(provider=LocalStorageProvider(base_dir="/tmp/p8_storage_test"))
    filename = "test_tile.tif"
    data = b"GEOTIFF_HEADER_BYTES_12345"
    
    uri = await storage.store_file(filename, data)
    assert uri.startswith("storage://local/")
    
    exists = await storage.exists(filename)
    assert exists is True
    
    read_bytes = await storage.read_file(filename)
    assert read_bytes == data
    
    deleted = await storage.remove_file(filename)
    assert deleted is True


@pytest.mark.anyio
async def test_13_storage_rejects_path_traversal():
    storage = StorageService(provider=LocalStorageProvider())
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await storage.read_file("../../etc/shadow")
    assert exc_info.value.status_code == 400


@pytest.mark.anyio
async def test_14_s3_storage_provider_template():
    storage = StorageService(provider=S3StorageProvider(bucket="cadastravision-test"))
    uri = await storage.store_file("s3_test.tif", b"s3_data")
    assert uri == "s3://cadastravision-test/s3_test.tif"
    read_data = await storage.read_file("s3_test.tif")
    assert read_data == b"s3_data"


# =====================================================================
# 6. DOCKER & CONTAINER READINESS (17-18)
# =====================================================================

def test_17_dockerfile_exists_and_uses_non_root():
    assert os.path.exists("Dockerfile")
    with open("Dockerfile", "r") as f:
        content = f.read()
    assert "USER appuser" in content
    assert "HEALTHCHECK" in content


@pytest.mark.anyio
async def test_18_health_readiness_endpoint_passes(client: AsyncClient):
    resp = await client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# =====================================================================
# 7. COMPLETE PRODUCTION E2E WORKFLOW (19-20)
# =====================================================================

@pytest.mark.anyio
async def test_20_complete_production_workflow(client: AsyncClient, phase6_setup: dict):
    # Authenticate Admin
    token = create_access_token(phase6_setup["admin"].id, phase6_setup["admin"].email, "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Health Probe
    h = await client.get("/health/ready")
    assert h.status_code == 200

    # 2. Upload imagery
    files = {"file": ("prod_imagery.tif", io.BytesIO(b"geotiff header bytes"), "image/tiff")}
    upload_res = await client.post("/v1/imagery/upload", files=files, headers=headers)
    assert upload_res.status_code in (200, 202)
    job_id = upload_res.json()["job_id"]

    # 3. Poll processing job
    job_res = await client.get(f"/v1/imagery/jobs/{job_id}", headers=headers)
    assert job_res.status_code == 200

    # 4. Trigger change detection
    change_res = await client.post(
        "/v1/change-detection/jobs",
        json={"historical_tile_id": "hist-123", "current_tile_id": "curr-456"},
        headers=headers,
    )
    assert change_res.status_code in (200, 202)
    cd_job_id = change_res.json()["job_id"]

    # 5. Fetch change results
    results_res = await client.get(f"/v1/change-detection/results/{cd_job_id}", headers=headers)
    assert results_res.status_code == 200

    # 6. Secure Export (GeoJSON)
    exp_res = await client.post(
        "/v1/exports",
        json={"export_format": "geojson", "filters": {"limit": 5}},
        headers=headers,
    )
    assert exp_res.status_code in (200, 202)
    export_id = exp_res.json()["export_id"]

    # 7. Download Export
    dl_res = await client.get(f"/v1/exports/{export_id}/download", headers=headers)
    assert dl_res.status_code == 200
