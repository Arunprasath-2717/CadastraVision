"""
app/routers/validations.py
───────────────────────────
GET  /v1/validations/queue
POST /v1/validations/run
GET  /v1/parcels/{parcel_id}/flags   ← belongs to validation domain
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.integrations.topology.validator import TopologyValidationService
from app.models.parcel import Parcel, ParcelWorkflowStatus
from app.models.user import User, UserRole
from app.models.validation import ValidationFlag
from app.schemas.validation import (
    FlagResponse,
    ParcelFlagsResponse,
    ValidationQueueItem,
    ValidationQueueResponse,
    ValidationRunRequest,
    ValidationRunResponse,
)

router = APIRouter(tags=["Validation"])

# /v1/validations/* routes
validations_router = APIRouter(prefix="/v1/validations")


@validations_router.get(
    "/queue",
    response_model=ValidationQueueResponse,
    summary="Validation queue",
    description="List parcels awaiting topology or confidence validation.",
)
async def get_validation_queue(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ValidationQueueResponse:
    stmt = (
        select(Parcel)
        .where(
            Parcel.deleted_at.is_(None),
            Parcel.workflow_status.in_(
                [ParcelWorkflowStatus.DRAFT, ParcelWorkflowStatus.VALIDATION_PENDING]
            ),
        )
        .order_by(Parcel.created_at.desc())
    )
    res = await db.execute(stmt)
    parcels = res.scalars().all()

    items = []
    for p in parcels:
        flags_stmt = select(ValidationFlag).where(ValidationFlag.parcel_id == p.id)
        flags_res = await db.execute(flags_stmt)
        p_flags = flags_res.scalars().all()

        items.append(
            ValidationQueueItem(
                parcel_id=p.id,
                workflow_status=p.workflow_status.value,
                flag_count=len(p_flags),
                oldest_flag_at=p_flags[0].created_at if p_flags else None,
            )
        )

    return ValidationQueueResponse(items=items, next_cursor=None)


@validations_router.post(
    "/run",
    response_model=ValidationRunResponse,
    summary="Trigger validation run",
    description="Trigger topology and confidence validation for a set of parcels.",
)
async def run_validation(
    body: ValidationRunRequest,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ValidationRunResponse:
    topology_service = TopologyValidationService()
    job_id = str(uuid.uuid4())

    for pid in body.parcel_ids:
        p_stmt = select(Parcel).where(Parcel.id == pid)
        res = await db.execute(p_stmt)
        p = res.scalar_one_or_none()
        if p:
            val_res = await topology_service.validate_parcel(
                parcel_id=p.id, geometry_wkt=p.geometry_wkt, confidence=p.confidence
            )
            if val_res.flags:
                p.workflow_status = ParcelWorkflowStatus.VALIDATION_PENDING
                for f in val_res.flags:
                    flag_rec = ValidationFlag(
                        parcel_id=p.id,
                        flag_type=f.flag_type,
                        severity=f.severity,
                        description=f.description,
                    )
                    db.add(flag_rec)
            else:
                p.workflow_status = ParcelWorkflowStatus.VALIDATED

    await db.commit()
    return ValidationRunResponse(
        job_id=job_id,
        status="complete",
        parcel_count=len(body.parcel_ids),
    )


# /v1/parcels/{parcel_id}/flags — mounted separately in main.py
flags_router = APIRouter(prefix="/v1/parcels")


@flags_router.get(
    "/{parcel_id}/flags",
    response_model=ParcelFlagsResponse,
    summary="Get validation flags for a parcel",
    description="List all validation flags on a specific parcel.",
    tags=["Validation"],
)
async def get_parcel_flags(
    parcel_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ParcelFlagsResponse:
    stmt = select(ValidationFlag).where(ValidationFlag.parcel_id == parcel_id)
    res = await db.execute(stmt)
    flags = res.scalars().all()

    items = [
        FlagResponse(
            flag_id=f.id,
            parcel_id=f.parcel_id,
            flag_type=f.flag_type,
            severity=f.severity,
            description=f.description,
            resolved=f.resolved,
            created_at=f.created_at,
            resolved_at=f.resolved_at,
        )
        for f in flags
    ]
    return ParcelFlagsResponse(parcel_id=parcel_id, flags=items, total=len(items))
