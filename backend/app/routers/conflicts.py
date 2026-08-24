"""app/routers/conflicts.py — GET /v1/conflicts, POST /v1/conflicts/{conflict_id}/resolve."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.conflict import ConflictStatus
from app.schemas.conflict import ConflictsResponse, ResolveConflictRequest, ResolveConflictResponse

router = APIRouter(prefix="/v1/conflicts", tags=["Conflicts"])


@router.get(
    "",
    response_model=ConflictsResponse,
    summary="List open conflicts",
    description="List spatial or data conflicts between parcels. **STUB** — Phase 3.",
)
async def list_conflicts() -> ConflictsResponse:
    return ConflictsResponse(items=[], next_cursor=None)


@router.post(
    "/{conflict_id}/resolve",
    response_model=ResolveConflictResponse,
    summary="Resolve conflict",
    description="Apply a resolution strategy to a detected conflict. **STUB** — Phase 3.",
)
async def resolve_conflict(
    conflict_id: str, body: ResolveConflictRequest
) -> ResolveConflictResponse:
    return ResolveConflictResponse(
        conflict_id=conflict_id,
        status=ConflictStatus.RESOLVED,
        message=f"Conflict resolved via '{body.resolution}'. [STUB]",
    )
