"""app/routers/exports.py — POST /v1/exports, GET /v1/exports/{export_id}."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status

from app.core.security import get_current_user
from app.models.export import ExportFormat, ExportStatus
from app.models.user import User
from app.schemas.export import CreateExportRequest, ExportStatusResponse

router = APIRouter(prefix="/v1/exports", tags=["Exports"])

_NOW = lambda: datetime.now(timezone.utc)  # noqa: E731


@router.post(
    "",
    response_model=ExportStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create export",
    description="Enqueue a data export (GeoJSON, Shapefile, GeoPackage, CSV).",
)
async def create_export(
    body: CreateExportRequest,
    current_user: User = Depends(get_current_user),
) -> ExportStatusResponse:
    return ExportStatusResponse(
        export_id=str(uuid.uuid4()),
        export_format=body.export_format,
        status=ExportStatus.QUEUED,
        created_at=_NOW(),
    )


@router.get(
    "/{export_id}",
    response_model=ExportStatusResponse,
    summary="Get export status",
    description="Poll the status of an export job.",
)
async def get_export_status(
    export_id: str,
    current_user: User = Depends(get_current_user),
) -> ExportStatusResponse:
    return ExportStatusResponse(
        export_id=export_id,
        export_format=ExportFormat.GEOJSON,
        status=ExportStatus.QUEUED,
        created_at=_NOW(),
    )
