"""
Self-intersection detector.

Detects bow-tie polygons, crossing rings, invalid holes, degenerate geometries.
Returns structured flags — never raises into the API layer.
"""
from dataclasses import dataclass
from typing import List, Optional
import shapely.geometry
import shapely.validation
from shapely.geometry.base import BaseGeometry
from app.geometry.crs import to_metric, metric_geom_to_geojson
import logging

log = logging.getLogger(__name__)


@dataclass
class SelfIntersectionFlag:
    feature_id: str
    flag_type: str = "self_intersection"
    severity: str = "high"
    reason: str = ""
    diagnostic_geometry: Optional[dict] = None  # GeoJSON point/geometry of the offending location

    def to_dict(self) -> dict:
        return {
            "feature_id": self.feature_id,
            "flag_type": self.flag_type,
            "severity": self.severity,
            "reason": self.reason,
            "diagnostic_geometry": self.diagnostic_geometry,
        }


def detect_self_intersections(feature_id: str, geom_4326: BaseGeometry) -> List[SelfIntersectionFlag]:
    """
    Run self-intersection diagnostics on a single geometry.
    Projects to metric CRS before analysis.
    Returns a list of flags (empty = no issues found).
    """
    flags: List[SelfIntersectionFlag] = []

    try:
        projected = to_metric(geom_4326)
    except Exception as e:
        flags.append(SelfIntersectionFlag(
            feature_id=feature_id,
            flag_type="crs_error",
            severity="high",
            reason=f"CRS transformation failed: {e}",
        ))
        return flags

    if not projected.is_valid:
        reason = shapely.validation.explain_validity(projected)

        # Try to locate the issue point
        diag_geom = None
        try:
            invalid_pt = shapely.validation.make_valid(projected).difference(projected)
            if not invalid_pt.is_empty:
                diag_geom = metric_geom_to_geojson(invalid_pt.centroid)
        except Exception:
            pass

        flags.append(SelfIntersectionFlag(
            feature_id=feature_id,
            flag_type="self_intersection",
            severity="high",
            reason=reason,
            diagnostic_geometry=diag_geom,
        ))

    # Additional: check for bow-tie (exterior ring self-intersection)
    if hasattr(projected, "geoms"):
        polys = list(projected.geoms)
    elif projected.geom_type == "Polygon":
        polys = [projected]
    else:
        polys = []

    for poly in polys:
        if poly.geom_type != "Polygon":
            continue
        ext = poly.exterior
        if not ext.is_simple:
            flags.append(SelfIntersectionFlag(
                feature_id=feature_id,
                flag_type="bow_tie",
                severity="high",
                reason="Exterior ring is not simple (bow-tie / crossing ring detected).",
            ))
        for hole in poly.interiors:
            if not hole.is_simple:
                flags.append(SelfIntersectionFlag(
                    feature_id=feature_id,
                    flag_type="invalid_hole",
                    severity="high",
                    reason="Interior ring (hole) is not simple.",
                ))

    return flags
