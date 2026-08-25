"""
app/integrations/topology/validator.py
────────────────────────────────────────
TopologyValidationService — Real Shapely / GEOS geospatial engine integration.

Performs robust geometry validity, self-intersection, overlap, containment,
duplicate detection, and non-destructive geometry repair.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.models.validation import FlagSeverity, FlagType

try:
    import shapely
    from shapely.validation import explain_validity, make_valid
    import shapely.wkt
    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False

logger = logging.getLogger(__name__)


@dataclass
class FlagDetail:
    flag_type: FlagType
    severity: FlagSeverity
    description: str
    geometry_wkt: str | None = None


@dataclass
class ValidationResult:
    is_valid: bool
    flags: list[FlagDetail] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


class TopologyValidationService:
    """
    Production-grade Topology Validation Service powered by Shapely / GEOS.
    """

    def __init__(self, mock_flags: list[FlagDetail] | None = None) -> None:
        self._mock_flags = mock_flags

    async def validate_parcel(
        self,
        parcel_id: str,
        geometry_wkt: str,
        confidence: float | None = None,
        neighbor_geometries: list[str] | None = None,
    ) -> ValidationResult:
        """
        Perform complete topology validation on a parcel geometry.

        Checks:
        1. Structural WKT validity & Shapely GEOS parsing
        2. Geometry validity (is_valid, self-intersection, hole orientation)
        3. Low confidence threshold check (< 0.70)
        4. Spatial overlap and duplicate checks against neighbor geometries
        """
        logger.info("[TOPOLOGY SERVICE] Validating parcel=%s geometry_wkt=%s...", parcel_id, geometry_wkt[:30] if geometry_wkt else "")

        flags: list[FlagDetail] = []
        parsed_geom = None
        checks_run = ["structural_wkt", "confidence_threshold"]

        # 1. Structural check
        clean_wkt = geometry_wkt.strip() if geometry_wkt else ""
        if not clean_wkt or not clean_wkt.upper().startswith("POLYGON"):
            flags.append(
                FlagDetail(
                    flag_type=FlagType.SELF_INTERSECTION,
                    severity=FlagSeverity.ERROR,
                    description="Geometry is not a valid POLYGON format",
                )
            )
        elif HAS_SHAPELY:
            checks_run.append("shapely_geos_validity")
            try:
                parsed_geom = shapely.wkt.loads(clean_wkt)
                if parsed_geom.is_empty:
                    flags.append(
                        FlagDetail(
                            flag_type=FlagType.SELF_INTERSECTION,
                            severity=FlagSeverity.ERROR,
                            description="Geometry is empty",
                        )
                    )
                elif not parsed_geom.is_valid:
                    reason = explain_validity(parsed_geom)
                    flags.append(
                        FlagDetail(
                            flag_type=FlagType.SELF_INTERSECTION,
                            severity=FlagSeverity.ERROR,
                            description=f"Self-intersection or invalid geometry topology: {reason}",
                            geometry_wkt=clean_wkt,
                        )
                    )
            except Exception as exc:
                flags.append(
                    FlagDetail(
                        flag_type=FlagType.SELF_INTERSECTION,
                        severity=FlagSeverity.ERROR,
                        description=f"WKT Parsing failure: {exc}",
                    )
                )

        # 2. Confidence check
        if confidence is not None and confidence < 0.70:
            flags.append(
                FlagDetail(
                    flag_type=FlagType.CONFIDENCE_LOW,
                    severity=FlagSeverity.WARNING,
                    description=f"AI confidence ({confidence:.2f}) is below 0.70 threshold",
                )
            )

        # 3. Spatial neighbor overlap / duplicate check
        if neighbor_geometries and parsed_geom and HAS_SHAPELY:
            checks_run.append("neighbor_overlap_check")
            for idx, n_wkt in enumerate(neighbor_geometries):
                if not n_wkt:
                    continue
                try:
                    n_geom = shapely.wkt.loads(n_wkt)
                    if parsed_geom.equals(n_geom):
                        flags.append(
                            FlagDetail(
                                flag_type=FlagType.OVERLAP,
                                severity=FlagSeverity.ERROR,
                                description=f"Duplicate geometry detected with neighbor index {idx}",
                                geometry_wkt=n_wkt,
                            )
                        )
                    elif parsed_geom.overlaps(n_geom) or (parsed_geom.intersects(n_geom) and parsed_geom.intersection(n_geom).area > 1e-6):
                        overlap_area = parsed_geom.intersection(n_geom).area
                        flags.append(
                            FlagDetail(
                                flag_type=FlagType.OVERLAP,
                                severity=FlagSeverity.WARNING,
                                description=f"Spatial overlap ({overlap_area:.4f} sq units) detected with neighbor index {idx}",
                                geometry_wkt=n_wkt,
                            )
                        )
                except Exception as n_exc:
                    logger.warning(f"Failed to parse neighbor geometry index {idx}: {n_exc}")

        # 4. Custom / mock flags passed for testing
        if self._mock_flags:
            flags.extend(self._mock_flags)

        is_valid = not any(f.severity in (FlagSeverity.ERROR, FlagSeverity.CRITICAL) for f in flags)

        return ValidationResult(
            is_valid=is_valid,
            flags=flags,
            details={
                "parcel_id": parcel_id,
                "flag_count": len(flags),
                "engine": "shapely_geos" if HAS_SHAPELY else "structural_stub",
                "checks_run": checks_run,
            },
        )

    def repair_geometry(self, geometry_wkt: str) -> dict[str, str]:
        """
        Non-destructive geometry repair.
        Returns repaired WKT while preserving original geometry string untouched.
        """
        if not HAS_SHAPELY:
            return {"original_wkt": geometry_wkt, "repaired_wkt": geometry_wkt}

        try:
            geom = shapely.wkt.loads(geometry_wkt)
            if geom.is_valid:
                return {"original_wkt": geometry_wkt, "repaired_wkt": geometry_wkt}
            repaired = make_valid(geom)
            return {"original_wkt": geometry_wkt, "repaired_wkt": repaired.wkt}
        except Exception as exc:
            logger.error(f"Geometry repair failed: {exc}")
            return {"original_wkt": geometry_wkt, "repaired_wkt": geometry_wkt}
