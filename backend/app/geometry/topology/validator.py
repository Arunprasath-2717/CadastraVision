"""
Topology orchestrator — runs all topology checks and returns a unified result.

Topology failure ALWAYS overrides confidence. A feature with confidence=0.99
and any topology error must have review_required=True.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import shapely.geometry
from app.geometry.validator import validate_geojson_geometry, ValidationResult
from app.geometry.topology.self_intersection import detect_self_intersections
from app.geometry.topology.overlap import detect_overlaps, OverlapFlag
from app.geometry.topology.gaps import detect_gaps, GapFlag
from app.geometry.crs import to_metric
import logging

log = logging.getLogger(__name__)


@dataclass
class TopologyResult:
    feature_id: str
    valid: bool = True
    self_intersections: List[dict] = field(default_factory=list)
    total_flags: int = 0
    severity: str = "none"   # none | low | medium | high
    overlaps: List[dict] = field(default_factory=list)
    gaps: List[dict] = field(default_factory=list)
    flags: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "total_flags": self.total_flags,
            "severity": self.severity,
            "overlap_count": len(self.overlaps),
            "gap_count": len(self.gaps),
            "self_intersection_count": len(self.self_intersections),
            "flags": self.flags,
        }


def validate_single(feature_id: str, geojson_geom: dict) -> TopologyResult:
    """
    Validate a single feature's geometry (validity + self-intersection only).
    No cross-feature checks (overlap/gap) since we only have one feature.
    """
    result = TopologyResult(feature_id=feature_id)

    # 1. Basic validity
    val = validate_geojson_geometry(geojson_geom)
    if not val.valid:
        result.valid = False
        for issue in val.issues:
            if issue.severity == "error":
                result.flags.append({
                    "type": issue.code,
                    "severity": "high",
                    "message": issue.message,
                })

    # 2. Self-intersection
    try:
        shp = shapely.geometry.shape(geojson_geom)
        si_flags = detect_self_intersections(feature_id, shp)
        for si in si_flags:
            result.valid = False
            d = si.to_dict()
            result.self_intersections.append(d)
            result.flags.append({"type": d["flag_type"], "severity": d["severity"], "message": d["reason"]})
    except Exception as e:
        log.warning(f"Self-intersection check failed for {feature_id}: {e}")

    result.total_flags = len(result.flags)
    result.severity = _compute_severity(result.flags)
    return result


def validate_collection(
    features: List[Dict],
    overlap_threshold_m2: float = 0.01,
    gap_tolerance_m: float = 2.0,
) -> Dict[str, TopologyResult]:
    """
    Run full topology on a collection of features.
    Returns a dict keyed by feature_id.
    """
    results: Dict[str, TopologyResult] = {}

    # Per-feature validity
    for feat in features:
        fid = feat.get("feature_id", "unknown")
        geom = feat.get("geometry")
        if not geom:
            results[fid] = TopologyResult(feature_id=fid, valid=False,
                                          flags=[{"type": "MISSING_GEOMETRY", "severity": "high", "message": "No geometry."}])
            continue
        results[fid] = validate_single(fid, geom)

    # Cross-feature: overlaps
    overlap_flags = detect_overlaps(features, threshold_m2=overlap_threshold_m2)
    for ovf in overlap_flags:
        d = ovf.to_dict()
        for fid in (ovf.feature_id, ovf.related_feature_id):
            if fid in results:
                results[fid].valid = False
                results[fid].overlaps.append(d)
                results[fid].flags.append({
                    "type": "overlap", "severity": d["severity"],
                    "related_feature_id": ovf.related_feature_id if fid == ovf.feature_id else ovf.feature_id,
                    "area_m2": d["area_m2"],
                })

    # Cross-feature: gaps
    gap_flags = detect_gaps(features, gap_tolerance_m=gap_tolerance_m)
    for gf in gap_flags:
        d = gf.to_dict()
        for fid in (gf.feature_id, gf.related_feature_id):
            if fid in results:
                results[fid].gaps.append(d)
                results[fid].flags.append({
                    "type": "gap", "severity": d["severity"],
                    "related_feature_id": gf.related_feature_id if fid == gf.feature_id else gf.feature_id,
                    "area_m2": d["area_m2"],
                })

    # Recompute totals
    for r in results.values():
        r.total_flags = len(r.flags)
        r.severity = _compute_severity(r.flags)

    return results


def _compute_severity(flags: List[dict]) -> str:
    if not flags:
        return "none"
    severities = [f.get("severity", "low") for f in flags]
    if "high" in severities:
        return "high"
    if "medium" in severities:
        return "medium"
    return "low"
