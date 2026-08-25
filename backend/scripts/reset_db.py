#!/usr/bin/env python3
"""
scripts/reset_db.py
────────────────────
Drop and recreate all database tables (development only).

WARNING: This is destructive. Never run in staging or production.

Usage (from backend/ directory):
    python scripts/reset_db.py
"""

import asyncio
import sys

from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def reset() -> None:
    settings = get_settings()
    if settings.is_production:
        logger.error("reset_db REFUSED: ENVIRONMENT=production")
        sys.exit(1)

    logger.warning("Dropping all tables …")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    logger.warning("Creating all tables …")
    import app.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database reset complete.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset())
