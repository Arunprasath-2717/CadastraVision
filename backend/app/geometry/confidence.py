"""
Confidence calculator — geometry quality score (NOT legal or cadastral accuracy).

Score represents: how reliable is this geometry based on measurable quality signals?

Components (all configurable weights):
  - geometry_validity (0.0 or 1.0)
  - topology_quality  (deducted per flag)
  - shape_plausibility (area/perimeter ratio check)
  - source_quality    (based on known source reliability)
  - manual_verification (bonus if manually reviewed)

CRITICAL RULE:
  If topology is invalid, review_required = True regardless of score.
  A score of 0.99 + invalid topology → REVIEW_REQUIRED.

Score levels:
  HIGH   >= 0.85
  MEDIUM >= 0.60
  LOW    < 0.60
"""
from dataclasses import dataclass, field
from typing import Dict, Optional
import math
import logging

log = logging.getLogger(__name__)

SOURCE_QUALITY = {
    "overture": 0.90,
    "osm": 0.85,
    "manual": 0.95,
    "import": 0.75,
    "ai": 0.70,
    "unknown": 0.60,
}

TOPOLOGY_DEDUCTIONS = {
    "high": 0.30,
    "medium": 0.15,
    "low": 0.05,
}

WEIGHTS = {
    "geometry_validity": 0.30,
    "topology_quality": 0.25,
    "shape_plausibility": 0.15,
    "source_quality": 0.20,
    "manual_verification": 0.10,
}


@dataclass
class ConfidenceResult:
    score: float
    level: str  # HIGH | MEDIUM | LOW
    review_required: bool
    components: Dict[str, float] = field(default_factory=dict)
    topology_override: bool = False

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 4),
            "level": self.level,
            "review_required": self.review_required,
            "topology_override": self.topology_override,
            "components": {k: round(v, 4) for k, v in self.components.items()},
        }


def _level(score: float) -> str:
    if score >= 0.85:
        return "HIGH"
    if score >= 0.60:
        return "MEDIUM"
    return "LOW"


def calculate_confidence(
    topology_valid: bool,
    topology_flags: list,           # list of {"severity": "high"|"medium"|"low"}
    source: str = "unknown",
    area_m2: Optional[float] = None,
    perimeter_m: Optional[float] = None,
    is_manually_verified: bool = False,
    topology_override_on_failure: bool = True,
) -> ConfidenceResult:
    """
    Calculate geometry quality confidence.

    Parameters
    ----------
    topology_valid      : False if any topology check failed.
    topology_flags      : List of flag dicts with "severity" key.
    source              : Data source identifier.
    area_m2             : Feature area (for shape plausibility).
    perimeter_m         : Feature perimeter (for compactness check).
    is_manually_verified: True if a human has reviewed this feature.
    """
    components: Dict[str, float] = {}

    # 1. Geometry validity
    components["geometry_validity"] = 1.0 if topology_valid else 0.0

    # 2. Topology quality
    deduction = sum(TOPOLOGY_DEDUCTIONS.get(f.get("severity", "low"), 0.05) for f in topology_flags)
    components["topology_quality"] = max(0.0, 1.0 - deduction)

    # 3. Shape plausibility (isoperimetric quotient — circles are 1.0)
    if area_m2 and perimeter_m and perimeter_m > 0:
        iq = (4 * math.pi * area_m2) / (perimeter_m ** 2)
        iq = min(1.0, iq)  # Clamp
        # Very thin slivers (iq < 0.01) are suspicious
        components["shape_plausibility"] = max(0.3, iq)
    else:
        components["shape_plausibility"] = 0.7  # Unknown — moderate

    # 4. Source quality
    components["source_quality"] = SOURCE_QUALITY.get(source.lower(), SOURCE_QUALITY["unknown"])

    # 5. Manual verification bonus
    components["manual_verification"] = 1.0 if is_manually_verified else 0.5

    # Weighted sum
    score = sum(WEIGHTS[k] * v for k, v in components.items() if k in WEIGHTS)
    score = max(0.0, min(1.0, score))

    # CRITICAL: topology failure overrides
    review_required = not topology_valid or any(
        f.get("severity") == "high" for f in topology_flags
    )
    topology_override = topology_override_on_failure and not topology_valid

    return ConfidenceResult(
        score=score,
        level=_level(score),
        review_required=review_required,
        components=components,
        topology_override=topology_override,
    )
