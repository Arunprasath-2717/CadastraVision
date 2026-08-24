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

    Overriding ``get_db`` and ``get_current_user`` so Phase 1-4 regression tests pass with an admin identity.
    """
    from app.core.security import get_current_user, hash_password
    from app.models.user import User, UserRole
    from sqlalchemy import select

    # Ensure default test admin user exists in db
    stmt = select(User).where(User.email == "test_admin@cadastravision.org")
    admin_user = (await db_session.execute(stmt)).scalars().first()
    if not admin_user:
        admin_user = User(
            id="test-admin-uuid-1234",
            email="test_admin@cadastravision.org",
            hashed_password=hash_password("AdminPass123!"),
            full_name="Test Admin",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin_user)
        await db_session.flush()

    app = create_app()

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return admin_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def unauth_client(db_session: AsyncSession):
    """Client with NO authentication overrides (tests real auth/401/403 logic)."""
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def phase6_setup(db_session: AsyncSession):
    """Seed imagery tiles and feature footprints for historical vs current comparison."""
    import uuid
    from sqlalchemy import select
    from app.core.security import hash_password
    from app.models.feature import BuildingFootprint, FeatureType
    from app.models.imagery import ImageryTile, TileSource, TileStatus
    from app.models.parcel import Parcel, ParcelWorkflowStatus
    from app.models.user import User, UserRole

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

    parcel = Parcel(
        id=str(uuid.uuid4()),
        geometry_wkt="POLYGON((0 0, 0 10, 10 10, 10 0, 0 0))",
        zone="Zone A",
        jurisdiction="District 1",
        workflow_status=ParcelWorkflowStatus.VALIDATED,
    )
    db_session.add(parcel)
    await db_session.flush()

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

