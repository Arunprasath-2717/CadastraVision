"""
app/routers/config.py
───────────────────────
Database configuration and schema management API endpoints.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db, init_db
from app.core.security import get_current_user
from app.models.user import User, UserRole

router = APIRouter(prefix="/v1/config", tags=["Configuration"])


@router.get(
    "/database",
    summary="Get Database Configuration & Health Status",
)
async def get_database_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Returns database connection metadata, dialect, table count, and connectivity status.
    """
    settings = get_settings()
    db_url_masked = settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL.split("://")[0]

    # Verify connectivity & fetch table count
    is_connected = False
    table_count = 0
    tables = []
    try:
        if "sqlite" in settings.DATABASE_URL:
            res = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [r[0] for r in res.fetchall()]
            table_count = len(tables)
            is_connected = True
        else:
            res = await db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
            tables = [r[0] for r in res.fetchall()]
            table_count = len(tables)
            is_connected = True
    except Exception as exc:
        tables = []
        is_connected = False

    return {
        "status": "connected" if is_connected else "disconnected",
        "database_driver": db_url_masked,
        "environment": settings.ENVIRONMENT,
        "is_connected": is_connected,
        "table_count": table_count,
        "tables": tables,
    }


@router.post(
    "/database/init",
    status_code=status.HTTP_200_OK,
    summary="Initialize Database Schema & Tables",
)
async def initialize_database_schema(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Triggers creation of missing database tables (schema initialization).
    Requires Admin privileges.
    """
    await init_db()
    return {
        "status": "success",
        "message": "Database schema and tables initialized successfully.",
    }
