"""
app/services/parcel_service.py
────────────────────────────────
Parcel CRUD, workflow state machine, edit, approve/reject, and sync service.

Handles:
1. Cursor-paginated listing with filtering
2. Full detail retrieval
3. Geometry edit with topology validation trigger (Arun)
4. Approve/Reject workflow transitions with state machine checks
5. Offline sync batch with persistent DB idempotency (SyncAction table)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.integrations.topology.validator import TopologyValidationService
from app.models.audit import AuditAction
from app.models.parcel import ALLOWED_TRANSITIONS, Parcel, ParcelWorkflowStatus
from app.models.sync import SyncAction, SyncActionStatus
from app.models.validation import FlagSeverity, FlagType, ValidationFlag
from app.schemas.parcel import (
    ParcelDetail,
    ParcelSummary,
    SyncActionItem,
    SyncResponse,
    SyncResultItem,
)
from app.services.audit_service import AuditEventService

logger = logging.getLogger(__name__)


def is_valid_transition(
    current: ParcelWorkflowStatus, target: ParcelWorkflowStatus
) -> bool:
    """Return True if the state transition from current → target is allowed."""
    return target in ALLOWED_TRANSITIONS.get(current, set())


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ParcelService:
    """Business logic for parcel lifecycle, state transitions, edits, and sync."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.topology_validator = TopologyValidationService()
        self.audit_service = AuditEventService(db)

    async def list_parcels(
        self,
        *,
        cursor: str | None = None,
        limit: int = 20,
        zone: str | None = None,
        jurisdiction: str | None = None,
        validation_status: ParcelWorkflowStatus | None = None,
        confidence_min: float | None = None,
        confidence_max: float | None = None,
    ) -> tuple[list[ParcelSummary], str | None]:
        """Cursor-paginated listing of parcels with optional filters."""
        stmt = select(Parcel).where(Parcel.deleted_at.is_(None))

        if zone:
            stmt = stmt.where(Parcel.zone == zone)
        if jurisdiction:
            stmt = stmt.where(Parcel.jurisdiction == jurisdiction)
        if validation_status:
            stmt = stmt.where(Parcel.workflow_status == validation_status)
        if confidence_min is not None:
            stmt = stmt.where(Parcel.confidence >= confidence_min)
        if confidence_max is not None:
            stmt = stmt.where(Parcel.confidence <= confidence_max)

        if cursor:
            stmt = stmt.where(Parcel.id > cursor)

        stmt = stmt.order_by(Parcel.id).limit(limit + 1)

        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())

        next_cursor = None
        if len(rows) > limit:
            next_cursor = rows[limit - 1].id
            rows = rows[:limit]

        items = [
            ParcelSummary(
                parcel_id=p.id,
                workflow_status=p.workflow_status,
                confidence=p.confidence,
                zone=p.zone,
                jurisdiction=p.jurisdiction,
                created_at=p.created_at,
            )
            for p in rows
        ]

        return items, next_cursor

    async def get_parcel(self, parcel_id: str) -> Parcel:
        """Fetch a parcel by ID or raise NotFoundError."""
        stmt = select(Parcel).where(and_(Parcel.id == parcel_id, Parcel.deleted_at.is_(None)))
        res = await self.db.execute(stmt)
        parcel = res.scalar_one_or_none()
        if not parcel:
            raise NotFoundError(detail=f"Parcel '{parcel_id}' not found.")
        return parcel

    async def apply_edit(
        self,
        parcel_id: str,
        edit_payload: dict,
        idempotency_key: str | None = None,
        user_id: str | None = None,
    ) -> Parcel:
        """
        Apply a geometry edit to a parcel and trigger topology validation.
        """
        parcel = await self.get_parcel(parcel_id)

        # Record pre-edit state for audit
        old_wkt = parcel.geometry_wkt
        old_status = parcel.workflow_status

        # Update geometry WKT if provided in payload
        new_wkt = edit_payload.get("geometry_wkt") or edit_payload.get("payload", {}).get("geometry_wkt")
        if new_wkt:
            parcel.geometry_wkt = new_wkt

        # Reset status to validation_pending after edit
        if is_valid_transition(parcel.workflow_status, ParcelWorkflowStatus.VALIDATION_PENDING):
            parcel.workflow_status = ParcelWorkflowStatus.VALIDATION_PENDING

        # Trigger Arun's topology validator integration
        val_result = await self.topology_validator.validate_parcel(
            parcel_id=parcel.id, geometry_wkt=parcel.geometry_wkt or ""
        )

        if val_result.is_valid:
            parcel.workflow_status = ParcelWorkflowStatus.VALIDATED
        else:
            # Create validation flags
            for f in val_result.flags:
                flag = ValidationFlag(
                    parcel_id=parcel.id,
                    flag_type=FlagType(f.get("flag_type", FlagType.OTHER.value)),
                    severity=FlagSeverity(f.get("severity", FlagSeverity.WARNING.value)),
                    description=f.get("description"),
                )
                self.db.add(flag)

        await self.audit_service.record(
            entity_type="parcel",
            entity_id=parcel.id,
            action=AuditAction.EDIT,
            user_id=user_id,
            diff={"geometry_wkt": {"before": old_wkt, "after": parcel.geometry_wkt}, "status": {"before": old_status.value, "after": parcel.workflow_status.value}},
        )

        await self.db.commit()
        await self.db.refresh(parcel)
        return parcel

    async def approve(
        self,
        parcel_id: str,
        reviewer_id: str | None = None,
        notes: str | None = None,
    ) -> Parcel:
        """Approve a parcel (must be in VALIDATED state)."""
        parcel = await self.get_parcel(parcel_id)

        if not is_valid_transition(parcel.workflow_status, ParcelWorkflowStatus.APPROVED):
            raise ValidationError(
                detail=f"Cannot transition parcel from '{parcel.workflow_status.value}' to 'approved'. Must be in 'validated' state."
            )

        old_status = parcel.workflow_status
        parcel.workflow_status = ParcelWorkflowStatus.APPROVED
        parcel.reviewed_by_id = reviewer_id
        parcel.reviewed_at = _now_iso()
        parcel.review_notes = notes

        await self.audit_service.record(
            entity_type="parcel",
            entity_id=parcel.id,
            action=AuditAction.APPROVE,
            user_id=reviewer_id,
            diff={"status": {"before": old_status.value, "after": ParcelWorkflowStatus.APPROVED.value}, "notes": notes},
        )

        await self.db.commit()
        await self.db.refresh(parcel)
        return parcel

    async def reject(
        self,
        parcel_id: str,
        reason: str,
        reviewer_id: str | None = None,
    ) -> Parcel:
        """Reject a parcel."""
        parcel = await self.get_parcel(parcel_id)

        if not is_valid_transition(parcel.workflow_status, ParcelWorkflowStatus.REJECTED):
            raise ValidationError(
                detail=f"Cannot transition parcel from '{parcel.workflow_status.value}' to 'rejected'."
            )

        old_status = parcel.workflow_status
        parcel.workflow_status = ParcelWorkflowStatus.REJECTED
        parcel.reviewed_by_id = reviewer_id
        parcel.reviewed_at = _now_iso()
        parcel.review_notes = f"Rejected: {reason}"

        await self.audit_service.record(
            entity_type="parcel",
            entity_id=parcel.id,
            action=AuditAction.REJECT,
            user_id=reviewer_id,
            diff={"status": {"before": old_status.value, "after": ParcelWorkflowStatus.REJECTED.value}, "reason": reason},
        )

        await self.db.commit()
        await self.db.refresh(parcel)
        return parcel

    async def sync_batch(self, actions: list[SyncActionItem]) -> SyncResponse:
        """
        Process offline action batch with DB-backed idempotency.
        """
        results: list[SyncResultItem] = []
        applied_cnt = 0
        conflict_cnt = 0
        failed_cnt = 0

        for item in actions:
            # Check idempotency record
            stmt = select(SyncAction).where(SyncAction.client_action_id == item.client_action_id)
            existing = (await self.db.execute(stmt)).scalar_one_or_none()

            if existing:
                # Replay existing result
                res_dict = existing.result_json or {}
                results.append(
                    SyncResultItem(
                        client_action_id=item.client_action_id,
                        status=existing.status.value,
                        parcel_id=existing.result_json.get("parcel_id") if existing.result_json else item.parcel_id,
                        conflict_detail=existing.conflict_detail,
                        error=existing.conflict_description,
                    )
                )
                if existing.status == SyncActionStatus.APPLIED:
                    applied_cnt += 1
                elif existing.status == SyncActionStatus.CONFLICT:
                    conflict_cnt += 1
                else:
                    failed_cnt += 1
                continue

            # Process new action
            try:
                if item.action_type == "edit" and item.parcel_id:
                    parcel = await self.apply_edit(item.parcel_id, item.payload)
                    sync_rec = SyncAction(
                        client_action_id=item.client_action_id,
                        action_type=item.action_type,
                        payload_json=item.payload,
                        status=SyncActionStatus.APPLIED,
                        result_json={"parcel_id": parcel.id, "workflow_status": parcel.workflow_status.value},
                    )
                    self.db.add(sync_rec)
                    applied_cnt += 1
                    results.append(SyncResultItem(client_action_id=item.client_action_id, status="applied", parcel_id=parcel.id))
                elif item.action_type == "approve" and item.parcel_id:
                    parcel = await self.approve(item.parcel_id, notes=item.payload.get("notes"))
                    sync_rec = SyncAction(
                        client_action_id=item.client_action_id,
                        action_type=item.action_type,
                        payload_json=item.payload,
                        status=SyncActionStatus.APPLIED,
                        result_json={"parcel_id": parcel.id, "workflow_status": parcel.workflow_status.value},
                    )
                    self.db.add(sync_rec)
                    applied_cnt += 1
                    results.append(SyncResultItem(client_action_id=item.client_action_id, status="applied", parcel_id=parcel.id))
                elif item.action_type == "reject" and item.parcel_id:
                    parcel = await self.reject(item.parcel_id, reason=item.payload.get("reason", "Sync rejection"))
                    sync_rec = SyncAction(
                        client_action_id=item.client_action_id,
                        action_type=item.action_type,
                        payload_json=item.payload,
                        status=SyncActionStatus.APPLIED,
                        result_json={"parcel_id": parcel.id, "workflow_status": parcel.workflow_status.value},
                    )
                    self.db.add(sync_rec)
                    applied_cnt += 1
                    results.append(SyncResultItem(client_action_id=item.client_action_id, status="applied", parcel_id=parcel.id))
                else:
                    # Unknown action or missing parcel_id
                    sync_rec = SyncAction(
                        client_action_id=item.client_action_id,
                        action_type=item.action_type,
                        payload_json=item.payload,
                        status=SyncActionStatus.FAILED,
                        conflict_description="Invalid action type or missing parcel_id",
                    )
                    self.db.add(sync_rec)
                    failed_cnt += 1
                    results.append(SyncResultItem(client_action_id=item.client_action_id, status="failed", error="Invalid action type or missing parcel_id"))
            except Exception as exc:
                sync_rec = SyncAction(
                    client_action_id=item.client_action_id,
                    action_type=item.action_type,
                    payload_json=item.payload,
                    status=SyncActionStatus.FAILED,
                    conflict_description=str(exc),
                )
                self.db.add(sync_rec)
                failed_cnt += 1
                results.append(SyncResultItem(client_action_id=item.client_action_id, status="failed", error=str(exc)))

        await self.db.commit()
        return SyncResponse(applied=applied_cnt, conflicts=conflict_cnt, failed=failed_cnt, results=results)
