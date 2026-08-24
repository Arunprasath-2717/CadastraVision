"""
tests/test_app.py
──────────────────
Phase 1 test-suite covering:

1. Application startup (lifespan executes without error)
2. GET /health → 200 {"status": "ok", "service": "cadastravision-backend"}
3. GET /openapi.json → 200 with valid OpenAPI schema
4. Database initialisation (tables exist after init_db)
"""

from __future__ import annotations

import pytest
import pytest_asyncio


# ── 1. Application startup ─────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_app_startup(client):
    """
    The test client fixture triggers the lifespan context manager.
    If startup raises, this test will fail before any assertion runs.
    """
    # A simple ping confirms the app is alive.
    response = await client.get("/health")
    assert response.status_code == 200, "App failed to start cleanly"


# ── 2. Health endpoint ─────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_health_status_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_health_response_body(client):
    response = await client.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "cadastravision-backend"


@pytest.mark.anyio
async def test_health_content_type(client):
    response = await client.get("/health")
    assert "application/json" in response.headers["content-type"]


# ── 3. OpenAPI schema generation ───────────────────────────────────────────────

@pytest.mark.anyio
async def test_openapi_schema_accessible(client):
    response = await client.get("/openapi.json")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_openapi_schema_structure(client):
    response = await client.get("/openapi.json")
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema
    assert schema["info"]["title"] == "CadastraVision API"


@pytest.mark.anyio
async def test_openapi_health_path_present(client):
    response = await client.get("/openapi.json")
    paths = response.json()["paths"]
    assert "/health" in paths, "GET /health must appear in the OpenAPI schema"


# ── 4. Database initialisation ─────────────────────────────────────────────────

@pytest.mark.anyio
async def test_database_engine_connects(test_engine):
    """Verify that the test engine can execute a trivial query."""
    from sqlalchemy import text

    async with test_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.anyio
async def test_database_tables_created(test_engine):
    """
    After init, the metadata must be reflected from the engine.

    At Phase 1 there are no domain models yet, so we verify that the
    introspection itself succeeds without error.
    """
    from sqlalchemy import inspect, text
    from sqlalchemy.ext.asyncio import AsyncConnection

    async with test_engine.connect() as conn:
        # run_sync lets us use the synchronous Inspector API
        table_names = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
    # At Phase 1 there are no tables yet — just confirm the call succeeds.
    assert isinstance(table_names, list)
