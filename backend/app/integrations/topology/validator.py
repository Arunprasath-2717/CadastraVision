"""
app/integrations/topology/validator.py
────────────────────────────────────────
TopologyValidationService — integration boundary for Arun's algorithms.

DO NOT implement Shapely overlap/gap/self-intersection here.
This file defines the interface that Arun's module will implement.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    is_valid: bool
    flags: list[dict]   # list of {flag_type, severity, description}


class TopologyValidationService:
    """
    Interface for topology validation of parcel geometry.

    Arun implements the concrete algorithms using Shapely.
    The ParcelService calls validate_parcel() after every edit.

    INTEGRATION STUB — Arun replaces the body with real algorithms.
    """

    async def validate_parcel(self, parcel_id: str, geometry_wkt: str) -> ValidationResult:
        """
        Run topology checks (overlap, gap, self-intersection).

        STUB — always returns valid with no flags.
        Replace with Arun's Shapely implementation.
        """
        logger.info("[TOPOLOGY STUB] validate_parcel parcel=%s", parcel_id)
        return ValidationResult(is_valid=True, flags=[])
