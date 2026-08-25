"""
app/services/export_service.py
───────────────────────────────
ExportService — Secure data export engine (GeoJSON, CSV, JSON) with CSV formula
injection prevention, bounded query pagination, and audit integration.
"""

from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import CadastraVisionError, ResourceNotFoundError, ValidationError
from app.models.audit import AuditAction
from app.models.export import Export, ExportFormat, ExportStatus
from app.models.parcel import Parcel
from app.services.audit_service import AuditService


class ExportService:
    """Service generating secure data exports (GeoJSON, CSV, JSON)."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_service = AuditService(db)

    @staticmethod
    def sanitize_csv_value(val: Any) -> Any:
        """Prevent CSV/Formula Injection by prepending ' to values starting with =, +, -, @, \\t, \\r."""
        if isinstance(val, str):
            if val.startswith(("=", "+", "-", "@", "\t", "\r")):
                return f"'{val}"
        return val

    @staticmethod
    def parse_wkt_to_geojson_geometry(wkt: str | None) -> Dict[str, Any]:
        """Convert standard WKT geometry string (e.g. POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))) to GeoJSON geometry dict."""
        if not wkt:
            return {"type": "Polygon", "coordinates": []}
        clean = wkt.strip()
        if clean.upper().startswith("POLYGON"):
            try:
                coords_str = clean[clean.index("((") + 2 : clean.rindex("))")]
                ring = []
                for pt in coords_str.split(","):
                    parts = pt.strip().split()
                    if len(parts) >= 2:
                        ring.append([float(parts[0]), float(parts[1])])
                return {"type": "Polygon", "coordinates": [ring]}
            except Exception:
                pass
        return {"type": "GeometryCollection", "geometries": []}

    async def generate_export(
        self,
        export_format: ExportFormat,
        filters: Dict[str, Any] | None = None,
        user_id: str | None = None,
    ) -> Tuple[Export, str]:
        """
        Creates an export job and returns the completed export metadata record + formatted data payload string.
        """
        filters = filters or {}
        limit = min(int(filters.get("limit", 1000)), 5000)

        # Build query for Parcels
        stmt = select(Parcel).where(Parcel.deleted_at.is_(None))
        if "zone" in filters and filters["zone"]:
            stmt = stmt.where(Parcel.zone == filters["zone"])
        if "jurisdiction" in filters and filters["jurisdiction"]:
            stmt = stmt.where(Parcel.jurisdiction == filters["jurisdiction"])
        if "workflow_status" in filters and filters["workflow_status"]:
            stmt = stmt.where(Parcel.workflow_status == filters["workflow_status"])

        stmt = stmt.limit(limit)
        parcels = (await self.db.execute(stmt)).scalars().all()

        export_job = Export(
            id=str(uuid.uuid4()),
            export_format=export_format,
            status=ExportStatus.PROCESSING,
            filter_params_json=filters,
            created_by_id=user_id,
        )
        self.db.add(export_job)
        await self.db.flush()

        content_str = ""

        if export_format == ExportFormat.GEOJSON:
            features = []
            for p in parcels:
                geom = self.parse_wkt_to_geojson_geometry(p.geometry_wkt)
                props = {
                    "id": p.id,
                    "confidence": p.confidence,
                    "zone": p.zone,
                    "jurisdiction": p.jurisdiction,
                    "workflow_status": p.workflow_status.value if p.workflow_status else None,
                    "created_at": str(p.created_at) if p.created_at else None,
                }
                features.append({"type": "Feature", "geometry": geom, "properties": props})

            geojson_obj = {
                "type": "FeatureCollection",
                "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
                "features": features,
            }
            content_str = json.dumps(geojson_obj, indent=2)

        elif export_format == ExportFormat.CSV:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["id", "confidence", "zone", "jurisdiction", "workflow_status", "geometry_wkt", "created_at"])

            for p in parcels:
                writer.writerow([
                    self.sanitize_csv_value(p.id),
                    self.sanitize_csv_value(p.confidence),
                    self.sanitize_csv_value(p.zone),
                    self.sanitize_csv_value(p.jurisdiction),
                    self.sanitize_csv_value(p.workflow_status.value if p.workflow_status else None),
                    self.sanitize_csv_value(p.geometry_wkt),
                    self.sanitize_csv_value(str(p.created_at) if p.created_at else ""),
                ])
            content_str = output.getvalue()

        else:
            # Default JSON format
            items = []
            for p in parcels:
                items.append({
                    "id": p.id,
                    "confidence": p.confidence,
                    "zone": p.zone,
                    "jurisdiction": p.jurisdiction,
                    "workflow_status": p.workflow_status.value if p.workflow_status else None,
                    "geometry_wkt": p.geometry_wkt,
                    "created_at": str(p.created_at) if p.created_at else None,
                })
            content_str = json.dumps({"parcels": items, "total": len(items)}, indent=2)

        export_job.status = ExportStatus.COMPLETE
        export_job.completed_at = datetime.now(timezone.utc).isoformat()
        export_job.file_size_bytes = len(content_str.encode("utf-8"))
        export_job.file_path = f"/exports/{export_job.id}.{export_format.value}"
        await self.db.flush()

        # Audit event without storing payload in audit trail
        await self.audit_service.record_entry(
            user_id=user_id,
            entity_type="export",
            entity_id=export_job.id,
            action=AuditAction.EXPORT_GENERATED,
            diff={
                "format": export_format.value,
                "record_count": len(parcels),
                "file_size_bytes": export_job.file_size_bytes,
            },
        )

        return export_job, content_str
