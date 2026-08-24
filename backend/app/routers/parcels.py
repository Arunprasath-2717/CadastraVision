"""
app/routers/parcels.py
───────────────────────
GET  /v1/parcels
GET  /v1/parcels/{parcel_id}
POST /v1/parcels/{parcel_id}/edit
POST /v1/parcels/{parcel_id}/approve
POST /v1/parcels/{parcel_id}/reject
POST /v1/parcels/sync

IMPORTANT: /v1/parcels/sync MUST be defined BEFORE /v1/parcels/{parcel_id}
to avoid FastAPI matching "sync" as a parcel_id path parameter.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.parcel import ParcelWorkflowStatus
from app.models.user import User, UserRole
from app.schemas.common import PaginatedResponse
from app.schemas.parcel import (
    ApproveRequest,
    ParcelActionResponse,
    ParcelDetail,
    ParcelEditRequest,
    ParcelEditResponse,
    ParcelSummary,
    RejectRequest,
    SyncRequest,
    SyncResponse,
)
from app.services.parcel_service import ParcelService

router = APIRouter(prefix="/v1/parcels", tags=["Parcels"])


@router.post(
    "/sync",
    response_model=SyncResponse,
    summary="Offline sync batch",
    description=(
        "Submit a batch of offline actions. Each action requires a "
        "``client_action_id`` for idempotent replay. Conflicts are surfaced "
        "explicitly — no silent last-write-wins."
    ),
)
async def sync_parcels(
    body: SyncRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> SyncResponse:
    service = ParcelService(db)
    return await service.sync_batch(body.actions)


@router.get(
    "",
    response_model=PaginatedResponse[ParcelSummary],
    summary="List parcels",
    description=(
        "Cursor-paginated list of parcels with optional filters. "
        "Filters: zone, jurisdiction, validation_status, confidence_min/max."
    ),
)
async def list_parcels(
    cursor: str | None = Query(default=None, description="Pagination cursor"),
    limit: int = Query(default=20, ge=1, le=100),
    zone: str | None = Query(default=None),
    jurisdiction: str | None = Query(default=None),
    validation_status: ParcelWorkflowStatus | None = Query(default=None),
    confidence_min: float | None = Query(default=None, ge=0.0, le=1.0),
    confidence_max: float | None = Query(default=None, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ParcelSummary]:
    service = ParcelService(db)
    items, next_cursor = await service.list_parcels(
        cursor=cursor,
        limit=limit,
        zone=zone,
        jurisdiction=jurisdiction,
        validation_status=validation_status,
        confidence_min=confidence_min,
        confidence_max=confidence_max,
    )
    return PaginatedResponse(items=items, next_cursor=next_cursor)


@router.get(
    "/{parcel_id}",
    response_model=ParcelDetail,
    summary="Get parcel detail",
    description="Retrieve full parcel representation including geometry.",
)
async def get_parcel(
    parcel_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ParcelDetail:
    service = ParcelService(db)
    p = await service.get_parcel(parcel_id)
    return ParcelDetail(
        parcel_id=p.id,
        geometry_wkt=p.geometry_wkt,
        source_tile_id=p.source_tile_id,
        confidence=p.confidence,
        zone=p.zone,
        jurisdiction=p.jurisdiction,
        workflow_status=p.workflow_status,
        reviewed_by_id=p.reviewed_by_id,
        reviewed_at=p.reviewed_at,
        review_notes=p.review_notes,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.post(
    "/{parcel_id}/edit",
    response_model=ParcelEditResponse,
    summary="Edit parcel geometry",
    description=(
        "Apply a vertex edit, split, or merge operation to a parcel. "
        "Triggers topology validation hook (Arun). "
        "``idempotency_key`` prevents duplicate edits on retry."
    ),
)
async def edit_parcel(
    parcel_id: str,
    body: ParcelEditRequest,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ParcelEditResponse:
    service = ParcelService(db)
    edited = await service.apply_edit(
        parcel_id, body.model_dump(), idempotency_key=body.idempotency_key
    )
    return ParcelEditResponse(
        parcel_id=edited.id,
        workflow_status=edited.workflow_status,
        message="Edit accepted. Topology validation executed.",
    )


@router.post(
    "/{parcel_id}/approve",
    response_model=ParcelActionResponse,
    summary="Approve parcel",
    description=(
        "Human sign-off — marks the parcel as approved and eligible for export. "
        "Requires the parcel to be in 'validated' status."
    ),
)
async def approve_parcel(
    parcel_id: str,
    body: ApproveRequest,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ParcelActionResponse:
    service = ParcelService(db)
    p = await service.approve(parcel_id, notes=body.notes, reviewer_id=current_user.id)
    return ParcelActionResponse(
        parcel_id=p.id,
        workflow_status=p.workflow_status,
        message="Parcel approved successfully.",
        reviewed_at=p.reviewed_at,
    )


@router.post(
    "/{parcel_id}/reject",
    response_model=ParcelActionResponse,
    summary="Reject parcel",
    description="Mark a parcel as rejected. Record is preserved for audit history.",
)
async def reject_parcel(
    parcel_id: str,
    body: RejectRequest,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ParcelActionResponse:
    service = ParcelService(db)
    p = await service.reject(parcel_id, reason=body.reason, reviewer_id=current_user.id)
    return ParcelActionResponse(
        parcel_id=p.id,
        workflow_status=p.workflow_status,
        message=f"Parcel rejected: {body.reason}",
        reviewed_at=p.reviewed_at,
    )
