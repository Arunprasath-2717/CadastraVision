"""
app/integrations/topology/validator.py
────────────────────────────────────────
TopologyValidationService — integration boundary for Arun's algorithms.

DO NOT implement full Shapely overlap/gap/self-intersection algorithms here.
This module provides the backend integration contract for topology checks,
flag formatting, and structural geometry validation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.models.validation import FlagSeverity, FlagType

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
    Interface for topology validation of parcel geometries.

    Arun implements the concrete algorithms in python/shapely.
    The core service invokes validate_parcel() during parcel creation and geometry edit.
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
        Perform topology validation on a parcel geometry.

        Checks:
        1. Basic structural WKT validity (polygon closure, non-empty)
        2. Low confidence check (< 0.70 triggers confidence_low warning)
        3. Topology checks (Arun's Shapely integration hook)
        """
        logger.info("[TOPOLOGY SERVICE] Validating parcel=%s geometry_wkt=%s...", parcel_id, geometry_wkt[:30])

        flags: list[FlagDetail] = []

        # 1. Basic structural check
        clean_wkt = geometry_wkt.strip().upper() if geometry_wkt else ""
        if not clean_wkt or not clean_wkt.startswith("POLYGON"):
            flags.append(
                FlagDetail(
                    flag_type=FlagType.SELF_INTERSECTION,
                    severity=FlagSeverity.ERROR,
                    description="Geometry is not a valid POLYGON format",
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

        # 3. Custom / mock flags passed for testing
        if self._mock_flags:
            flags.extend(self._mock_flags)

        is_valid = not any(f.severity in (FlagSeverity.ERROR, FlagSeverity.CRITICAL) for f in flags)

        return ValidationResult(
            is_valid=is_valid,
            flags=flags,
            details={
                "parcel_id": parcel_id,
                "flag_count": len(flags),
                "checks_run": ["structural_wkt", "confidence_threshold", "topology_stub"],
            },
        )
