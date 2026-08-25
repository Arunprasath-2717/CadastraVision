"""
app/services/change_service.py
───────────────────────────────
ChangeDetectionService — Core service for geospatial feature change detection,
historical versioning comparison, idempotency, review workflow, and audit logging.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import CadastraVisionError, ResourceNotFoundError, ValidationError
from app.models.audit import AuditAction
from app.models.change import ChangeRecord, ChangeStatus, ChangeType
from app.models.feature import BuildingFootprint
from app.models.imagery import ImageryTile, ProcessingJob, JobStatus, JobType, TileStatus
from app.models.parcel import Parcel
from app.services.audit_service import AuditService


class ChangeDetectionService:
    """Service handling feature version comparison, change classification, and review workflow."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_service = AuditService(db)

    def _compute_idempotency_hash(self, historical_tile_id: str, current_tile_id: str, algo_version: str) -> str:
        raw = f"{historical_tile_id}:{current_tile_id}:{algo_version}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def run_change_detection_job(
        self,
        historical_tile_id: str,
        current_tile_id: str,
        parcel_id: Optional[str] = None,
        algo_version: str = "v1.0",
        confidence_threshold: float = 0.5,
        user_id: Optional[str] = None,
    ) -> Tuple[ProcessingJob, List[ChangeRecord]]:
        """
        Executes or retrieves idempotent change detection between two imagery tile datasets.
        """
        # Validate tiles exist (or provision placeholders if stubs)
        hist_tile = await self.db.get(ImageryTile, historical_tile_id)
        if not hist_tile:
            hist_tile = ImageryTile(
                id=historical_tile_id,
                filename=f"{historical_tile_id}.tif",
                file_path=f"/tmp/{historical_tile_id}.tif",
                is_historical=True,
                status=TileStatus.PROCESSED,
            )
            self.db.add(hist_tile)

        curr_tile = await self.db.get(ImageryTile, current_tile_id)
        if not curr_tile:
            curr_tile = ImageryTile(
                id=current_tile_id,
                filename=f"{current_tile_id}.tif",
                file_path=f"/tmp/{current_tile_id}.tif",
                is_historical=False,
                status=TileStatus.PROCESSED,
            )
            self.db.add(curr_tile)
        await self.db.flush()

        # Check idempotency
        idempotency_hash = self._compute_idempotency_hash(historical_tile_id, current_tile_id, algo_version)
        stmt_existing = select(ChangeRecord).where(ChangeRecord.idempotency_hash == idempotency_hash)
        existing_records = (await self.db.execute(stmt_existing)).scalars().all()

        if existing_records:
            # Idempotent replay: return existing job if present or construct synthetic response
            job_id = existing_records[0].job_id
            job = await self.db.get(ProcessingJob, job_id) if job_id else None
            if not job:
                job = ProcessingJob(
                    id=str(uuid.uuid4()),
                    tile_id=current_tile_id,
                    job_type=JobType.CHANGE_DETECTION,
                    status=JobStatus.COMPLETE,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    result_json={"changes_detected": len(existing_records), "idempotent_replay": True},
                )
                self.db.add(job)
                await self.db.flush()
            return job, list(existing_records)

        # Create new processing job
        job = ProcessingJob(
            id=str(uuid.uuid4()),
            tile_id=current_tile_id,
            job_type=JobType.CHANGE_DETECTION,
            status=JobStatus.QUEUED,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self.db.add(job)
        await self.db.flush()

        # Fetch features for historical and current tiles
        hist_features_stmt = select(BuildingFootprint).where(BuildingFootprint.tile_id == historical_tile_id)
        curr_features_stmt = select(BuildingFootprint).where(BuildingFootprint.tile_id == current_tile_id)

        if parcel_id:
            hist_features_stmt = hist_features_stmt.where(BuildingFootprint.parcel_id == parcel_id)
            curr_features_stmt = curr_features_stmt.where(BuildingFootprint.parcel_id == parcel_id)

        hist_features = (await self.db.execute(hist_features_stmt)).scalars().all()
        curr_features = (await self.db.execute(curr_features_stmt)).scalars().all()

        change_records: List[ChangeRecord] = []
        matched_curr_ids = set()

        # Match historical features against current features
        for h_feat in hist_features:
            match_found = False
            for c_feat in curr_features:
                if c_feat.id in matched_curr_ids:
                    continue

                # Compare geometry WKT & feature type
                h_wkt = (h_feat.geometry_wkt or "").strip()
                c_wkt = (c_feat.geometry_wkt or "").strip()

                if h_wkt == c_wkt and h_feat.feature_type == c_feat.feature_type:
                    match_found = True
                    matched_curr_ids.add(c_feat.id)
                    rec = ChangeRecord(
                        id=str(uuid.uuid4()),
                        historical_tile_id=historical_tile_id,
                        current_tile_id=current_tile_id,
                        job_id=job.id,
                        parcel_id=parcel_id or h_feat.parcel_id or c_feat.parcel_id,
                        previous_feature_id=h_feat.id,
                        current_feature_id=c_feat.id,
                        change_type=ChangeType.UNCHANGED,
                        status=ChangeStatus.DETECTED,
                        confidence=1.0,
                        geometry_diff_wkt=None,
                        attribute_diff_json={"feature_type": h_feat.feature_type.value},
                        idempotency_hash=idempotency_hash,
                    )
                    change_records.append(rec)
                    break
                elif h_feat.feature_type == c_feat.feature_type or (h_wkt and c_wkt and h_wkt[:15] == c_wkt[:15]):
                    # Partial match / geometry modification
                    match_found = True
                    matched_curr_ids.add(c_feat.id)
                    conf = min(max(float((c_feat.confidence or 0.8) * 0.95), 0.0), 1.0)
                    rec = ChangeRecord(
                        id=str(uuid.uuid4()),
                        historical_tile_id=historical_tile_id,
                        current_tile_id=current_tile_id,
                        job_id=job.id,
                        parcel_id=parcel_id or h_feat.parcel_id or c_feat.parcel_id,
                        previous_feature_id=h_feat.id,
                        current_feature_id=c_feat.id,
                        change_type=ChangeType.MODIFIED,
                        status=ChangeStatus.PENDING_REVIEW,
                        confidence=conf,
                        geometry_diff_wkt=f"PREV: {h_wkt} | CURR: {c_wkt}",
                        attribute_diff_json={
                            "previous_wkt": h_wkt,
                            "current_wkt": c_wkt,
                            "feature_type": c_feat.feature_type.value,
                        },
                        idempotency_hash=idempotency_hash,
                    )
                    change_records.append(rec)
                    break

            if not match_found:
                # Removed feature
                rec = ChangeRecord(
                    id=str(uuid.uuid4()),
                    historical_tile_id=historical_tile_id,
                    current_tile_id=current_tile_id,
                    job_id=job.id,
                    parcel_id=parcel_id or h_feat.parcel_id,
                    previous_feature_id=h_feat.id,
                    current_feature_id=None,
                    change_type=ChangeType.REMOVED,
                    status=ChangeStatus.PENDING_REVIEW,
                    confidence=0.9,
                    geometry_diff_wkt=h_feat.geometry_wkt,
                    attribute_diff_json={"removed_feature_id": h_feat.id},
                    idempotency_hash=idempotency_hash,
                )
                change_records.append(rec)

        # Remaining current features are NEW
        for c_feat in curr_features:
            if c_feat.id not in matched_curr_ids:
                rec = ChangeRecord(
                    id=str(uuid.uuid4()),
                    historical_tile_id=historical_tile_id,
                    current_tile_id=current_tile_id,
                    job_id=job.id,
                    parcel_id=parcel_id or c_feat.parcel_id,
                    previous_feature_id=None,
                    current_feature_id=c_feat.id,
                    change_type=ChangeType.NEW,
                    status=ChangeStatus.PENDING_REVIEW,
                    confidence=min(max(float(c_feat.confidence or 0.85), 0.0), 1.0),
                    geometry_diff_wkt=c_feat.geometry_wkt,
                    attribute_diff_json={"new_feature_id": c_feat.id},
                    idempotency_hash=idempotency_hash,
                )
                change_records.append(rec)

        for rec in change_records:
            self.db.add(rec)

        # Complete job
        job.status = JobStatus.COMPLETE
        job.completed_at = datetime.now(timezone.utc).isoformat()
        job.result_json = {"changes_detected": len(change_records), "idempotency_hash": idempotency_hash}
        await self.db.flush()

        # Record Audit Event
        await self.audit_service.record_entry(
            user_id=user_id,
            entity_type="change_detection",
            entity_id=job.id,
            action=AuditAction.CHANGE_DETECTED,
            diff={"changes_count": len(change_records), "historical_tile": historical_tile_id, "current_tile": current_tile_id},
        )

        return job, change_records

    async def approve_change(self, change_id: str, user_id: str, review_notes: Optional[str] = None) -> ChangeRecord:
        record = await self.db.get(ChangeRecord, change_id)
        if not record:
            raise ResourceNotFoundError(detail=f"Change record {change_id} not found.")

        if record.status in (ChangeStatus.APPROVED, ChangeStatus.REJECTED):
            raise ValidationError(detail=f"Change record {change_id} is already in terminal state {record.status.value}.")

        record.status = ChangeStatus.APPROVED
        record.reviewed_by_id = user_id
        record.reviewed_at = datetime.now(timezone.utc).isoformat()
        record.review_notes = review_notes
        await self.db.flush()

        # Audit Event
        await self.audit_service.record_entry(
            user_id=user_id,
            entity_type="change_record",
            entity_id=record.id,
            action=AuditAction.CHANGE_APPROVED,
            diff={"status": "APPROVED", "notes": review_notes},
        )
        return record

    async def reject_change(self, change_id: str, user_id: str, review_notes: Optional[str] = None) -> ChangeRecord:
        record = await self.db.get(ChangeRecord, change_id)
        if not record:
            raise ResourceNotFoundError(detail=f"Change record {change_id} not found.")

        if record.status in (ChangeStatus.APPROVED, ChangeStatus.REJECTED):
            raise ValidationError(detail=f"Change record {change_id} is already in terminal state {record.status.value}.")

        record.status = ChangeStatus.REJECTED
        record.reviewed_by_id = user_id
        record.reviewed_at = datetime.now(timezone.utc).isoformat()
        record.review_notes = review_notes
        await self.db.flush()

        # Audit Event
        await self.audit_service.record_entry(
            user_id=user_id,
            entity_type="change_record",
            entity_id=record.id,
            action=AuditAction.CHANGE_REJECTED,
            diff={"status": "REJECTED", "notes": review_notes},
        )
        return record
