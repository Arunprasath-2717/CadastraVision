"""app/routers/conflicts.py — GET /v1/conflicts, POST /v1/conflicts/{conflict_id}/resolve."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security import get_current_user, require_role
from app.models.conflict import ConflictStatus
from app.models.user import User, UserRole
from app.schemas.conflict import ConflictsResponse, ResolveConflictRequest, ResolveConflictResponse

router = APIRouter(prefix="/v1/conflicts", tags=["Conflicts"])


@router.get(
    "",
    response_model=ConflictsResponse,
    summary="List open conflicts",
    description="List spatial or data conflicts between parcels.",
)
async def list_conflicts(
    current_user: User = Depends(get_current_user),
) -> ConflictsResponse:
    return ConflictsResponse(items=[], next_cursor=None)


@router.post(
    "/{conflict_id}/resolve",
    response_model=ResolveConflictResponse,
    summary="Resolve conflict",
    description="Apply a resolution strategy to a detected conflict.",
)
async def resolve_conflict(
    conflict_id: str,
    body: ResolveConflictRequest,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
) -> ResolveConflictResponse:
    return ResolveConflictResponse(
        conflict_id=conflict_id,
        status=ConflictStatus.RESOLVED,
        message=f"Conflict resolved via '{body.resolution}'.",
    )
