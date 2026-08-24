"""
app/core/database.py
─────────────────────
Async SQLAlchemy 2.x database layer.

Architecture
────────────
* ``AsyncEngine``  — created from ``settings.DATABASE_URL``.
* ``AsyncSessionLocal`` — factory produced by ``async_sessionmaker``.
* ``Base``  — shared ``DeclarativeBase`` imported by all ORM models.
* ``get_db`` — FastAPI dependency that yields an ``AsyncSession`` and
  commits/rolls-back automatically.
* ``init_db`` — creates all tables at startup (development) or is left
  to Alembic for production.

PostgreSQL compatibility
────────────────────────
Switch DATABASE_URL to ``postgresql+asyncpg://...`` — everything else
stays identical. The only SQLite-specific option is ``check_same_thread``
which is filtered out automatically.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# NOTE: ``Base`` lives in ``app.models.base`` — the canonical single source.
# We do NOT define another DeclarativeBase here to avoid duplicate metadata.


# ── Engine / session factory (module-level singletons) ────────────────────────

def _build_engine() -> AsyncEngine:
    settings = get_settings()
    url = settings.DATABASE_URL

    # SQLite requires ``check_same_thread=False`` to work with asyncio.
    connect_args: dict[str, Any] = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_async_engine(
        url,
        echo=settings.DEBUG,        # Logs every SQL statement in DEBUG mode.
        future=True,                # SA 2.x style.
        connect_args=connect_args,
    )
    logger.debug("AsyncEngine created for %s", url.split("://")[0])
    return engine


engine: AsyncEngine = _build_engine()

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,     # Avoids lazy-load errors after commit.
    autocommit=False,
    autoflush=False,
)


# ── FastAPI dependency ─────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a database session scoped to a single HTTP request.

    Automatically commits on success and rolls back on exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Startup / teardown helpers ─────────────────────────────────────────────────

async def init_db() -> None:
    """
    Create all tables defined in ORM models.

    In production, prefer Alembic migrations (``alembic upgrade head``)
    over this function.
    """
    # Import the models package — this triggers all model module imports,
    # registering every table on Base.metadata before create_all runs.
    import app.models  # noqa: F401
    from app.models.base import Base  # noqa: PLC0415

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialised.")


async def close_db() -> None:
    """Dispose of the engine connection pool on application shutdown."""
    await engine.dispose()
    logger.info("Database engine disposed.")
