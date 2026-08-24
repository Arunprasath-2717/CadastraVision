"""
app/main.py
────────────
FastAPI application factory for CadastraVision backend (PRD-CM-03).

Router registration
───────────────────
All domain routes live under /v1 prefix per PRD.
Health endpoint has no version prefix (infrastructure concern).

Error handling
──────────────
RFC 9457 Problem Details via app.core.errors.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import close_db, init_db
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN001
    logger.info(
        "Starting CadastraVision backend [env=%s debug=%s]",
        settings.ENVIRONMENT, settings.DEBUG,
    )
    await init_db()
    yield
    logger.info("Shutting down CadastraVision backend …")
    await close_db()


# ── Application factory ───────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="CadastraVision API",
        description=(
            "AI-enabled automated cadastral mapping platform. "
            "Programme: CadastralMap — SIH 2026, PS 26012. "
            "Backend owner: Shiva."
        ),
        version="0.2.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── RFC 9457 error handlers ───────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Infrastructure routes (no /v1 prefix) ─────────────────────────────────
    from app.routers.health import router as health_router
    app.include_router(health_router)

    # ── /v1 domain routes ─────────────────────────────────────────────────────
    from app.routers.auth import router as auth_router
    from app.routers.imagery import router as imagery_router
    from app.routers.parcels import router as parcels_router
    from app.routers.validations import validations_router, flags_router
    from app.routers.conflicts import router as conflicts_router
    from app.routers.change_detection import router as change_detection_router
    from app.routers.geo import router as geo_router
    from app.routers.exports import router as exports_router
    from app.routers.audit import router as audit_router
    from app.routers.metrics import router as metrics_router

    for r in (
        auth_router,
        imagery_router,
        parcels_router,
        validations_router,
        flags_router,
        conflicts_router,
        change_detection_router,
        geo_router,
        exports_router,
        audit_router,
        metrics_router,
    ):
        app.include_router(r)

    logger.debug("All routers registered.")

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = FastAPI.openapi(app)
        openapi_schema["components"] = openapi_schema.get("components", {})
        openapi_schema["components"]["securitySchemes"] = {
            "HTTPBearer": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter JWT access token to authenticate requests.",
            }
        }
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
    return app


app = create_app()
