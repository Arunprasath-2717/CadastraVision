"""
app/routers/validations.py
───────────────────────────
GET  /v1/validations/queue
POST /v1/validations/run
GET  /v1/parcels/{parcel_id}/flags   ← belongs to validation domain

STUB — Arun's topology algorithms connect here in Phase 3.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.validation import (
    ParcelFlagsResponse,
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
    description=(
        "List parcels awaiting topology or confidence validation. "
        "**STUB** — populated by Arun's topology pipeline (Phase 3)."
    ),
)
async def get_validation_queue() -> ValidationQueueResponse:
    return ValidationQueueResponse(items=[], next_cursor=None)


@validations_router.post(
    "/run",
    response_model=ValidationRunResponse,
    summary="Trigger validation run",
    description=(
        "Trigger topology and confidence validation for a set of parcels. "
        "**STUB** — invokes Arun's TopologyValidationService (Phase 3)."
    ),
)
async def run_validation(body: ValidationRunRequest) -> ValidationRunResponse:
    import uuid
    return ValidationRunResponse(
        job_id=str(uuid.uuid4()),
        status="queued",
        parcel_count=len(body.parcel_ids),
    )


# /v1/parcels/{parcel_id}/flags — mounted separately in main.py
flags_router = APIRouter(prefix="/v1/parcels")

@flags_router.get(
    "/{parcel_id}/flags",
    response_model=ParcelFlagsResponse,
    summary="Get validation flags for a parcel",
    description=(
        "List all validation flags on a specific parcel. "
        "**STUB** — Phase 3."
    ),
    tags=["Validation"],
)
async def get_parcel_flags(parcel_id: str) -> ParcelFlagsResponse:
    return ParcelFlagsResponse(parcel_id=parcel_id, flags=[], total=0)
