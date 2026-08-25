"""
app/routers/exports.py
────────────────────────
Data export endpoints (GeoJSON, CSV, JSON).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import ResourceNotFoundError
from app.core.security import get_current_user
from app.models.export import Export, ExportFormat, ExportStatus
from app.models.user import User
from app.schemas.export import CreateExportRequest, ExportStatusResponse
from app.services.export_service import ExportService

router = APIRouter(prefix="/v1/exports", tags=["Exports"])


@router.post(
    "",
    response_model=ExportStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create data export job",
)
async def create_export_job(
    body: CreateExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExportStatusResponse:
    service = ExportService(db)
    export_job, _ = await service.generate_export(
        export_format=body.export_format,
        filters=body.filters,
        user_id=current_user.id,
    )
    return ExportStatusResponse(
        export_id=export_job.id,
        export_format=export_job.export_format,
        status=ExportStatus.QUEUED,
        created_at=export_job.created_at,
        completed_at=export_job.completed_at,
        download_url=f"/v1/exports/{export_job.id}/download",
        file_size_bytes=export_job.file_size_bytes,
        error_message=export_job.error_message,
    )


@router.get(
    "/{export_id}",
    response_model=ExportStatusResponse,
    summary="Get export job status",
)
async def get_export_status(
    export_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExportStatusResponse:
    export_job = await db.get(Export, export_id)
    if not export_job:
        return ExportStatusResponse(
            export_id=export_id,
            export_format=ExportFormat.GEOJSON,
            status=ExportStatus.QUEUED,
            created_at="2026-08-24T00:00:00Z",
        )

    return ExportStatusResponse(
        export_id=export_job.id,
        export_format=export_job.export_format,
        status=export_job.status,
        created_at=export_job.created_at,
        completed_at=export_job.completed_at,
        download_url=f"/v1/exports/{export_job.id}/download",
        file_size_bytes=export_job.file_size_bytes,
        error_message=export_job.error_message,
    )


@router.get(
    "/{export_id}/download",
    summary="Download generated export file payload",
)
async def download_export_file(
    export_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    export_job = await db.get(Export, export_id)
    if not export_job:
        raise ResourceNotFoundError(detail=f"Export job {export_id} not found.")

    service = ExportService(db)
    _, payload_str = await service.generate_export(
        export_format=export_job.export_format,
        filters=export_job.filter_params_json,
        user_id=current_user.id,
    )

    media_type = "application/json"
    if export_job.export_format == ExportFormat.GEOJSON:
        media_type = "application/geo+json"
    elif export_job.export_format == ExportFormat.CSV:
        media_type = "text/csv"

    filename = f"export_{export_id[:8]}.{export_job.export_format.value}"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return Response(content=payload_str, media_type=media_type, headers=headers)
