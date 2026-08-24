"""
tests/conftest.py
──────────────────
Shared pytest fixtures for the CadastraVision backend test-suite.

Key design decisions
────────────────────
* Uses an in-memory SQLite database for complete test isolation.
* Overrides FastAPI's ``get_db`` dependency so every test gets its own
  clean session without polluting the real dev database.
* ``anyio_backend`` is pinned to "asyncio" so pytest-asyncio works with
  FastAPI's ASGI lifespan.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.models  # noqa: F401 — registers all tables on Base.metadata
from app.core.database import get_db
from app.main import create_app
from app.models.base import Base

# ── In-memory test database ────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create schema on an in-memory SQLite engine once per test session."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """Provide an isolated AsyncSession per test, rolled back on completion."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


# ── FastAPI test client ────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """
    Return an ``httpx.AsyncClient`` backed by the test app.

    The ``get_db`` dependency is overridden to use the isolated test session.
    """
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
