"""
Gap detector — configurable tolerance, STRtree-indexed, returns exact gap geometries.

Gap = a small space between two neighbouring polygons that share a plausible
boundary but are not adjacent (there is an unintended void between them).

Algorithm:
  1. STRtree on projected polygons.
  2. For each polygon, find neighbours within gap_tolerance_m (ST_DWithin equivalent).
  3. For close neighbours: compute the gap region via difference/buffer operations.
  4. If gap area > min_gap_area_m2, create a GapFlag with the exact gap geometry.

Does NOT flag:
  - Legitimate open land / roads / rivers (no context layer currently = conservative flagging).
  - Large open areas (> max_gap_area_m2).
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
import shapely.geometry
import shapely.ops
import shapely.strtree
from shapely.geometry.base import BaseGeometry
from app.geometry.crs import to_metric, metric_geom_to_geojson
import logging

log = logging.getLogger(__name__)

DEFAULT_GAP_TOLERANCE_M = 2.0       # Max distance between neighbours to inspect
DEFAULT_MIN_GAP_AREA_M2 = 0.5      # Minimum gap area to report (avoid sliver noise)
DEFAULT_MAX_GAP_AREA_M2 = 10000.0  # Upper limit — large voids are likely intentional


@dataclass
class GapFlag:
    feature_id: str
    related_feature_id: str
    flag_type: str = "gap"
    severity: str = "medium"
    area_m2: float = 0.0
    estimated_width_m: Optional[float] = None
    gap_geometry: Optional[dict] = None  # GeoJSON of the actual gap polygon

    def to_dict(self) -> dict:
        return {
            "feature_id": self.feature_id,
            "related_feature_id": self.related_feature_id,
            "flag_type": self.flag_type,
            "severity": self.severity,
            "area_m2": round(self.area_m2, 4),
            "estimated_width_m": round(self.estimated_width_m, 3) if self.estimated_width_m else None,
            "gap_geometry": self.gap_geometry,
        }


def detect_gaps(
    features: List[Dict],
    gap_tolerance_m: float = DEFAULT_GAP_TOLERANCE_M,
    min_gap_area_m2: float = DEFAULT_MIN_GAP_AREA_M2,
    max_gap_area_m2: float = DEFAULT_MAX_GAP_AREA_M2,
) -> List[GapFlag]:
    """
    Detect gaps between polygon pairs within gap_tolerance_m distance.
    """
    flags: List[GapFlag] = []

    # Project all valid polygon geometries
    projected = []
    for idx, feat in enumerate(features):
        fid = feat.get("feature_id", str(idx))
        raw_geom = feat.get("geometry")
        if not raw_geom:
            continue
        try:
            shp = shapely.geometry.shape(raw_geom)
            if shp.geom_type not in ("Polygon", "MultiPolygon"):
                continue
            proj = to_metric(shp)
            if proj.is_valid and not proj.is_empty:
                projected.append((fid, proj))
        except Exception as e:
            log.warning(f"Skipping {fid} for gap detection: {e}")

    if len(projected) < 2:
        return flags

    geoms = [p[1] for p in projected]
    tree = shapely.strtree.STRtree(geoms)
    seen_pairs = set()

    for i, (fid_a, geom_a) in enumerate(projected):
        # Buffer by tolerance to find nearby neighbours
        expanded = geom_a.buffer(gap_tolerance_m)
        candidate_indices = tree.query(expanded)

        for j in candidate_indices:
            if j <= i:
                continue
            pair_key = (i, j)
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            fid_b, geom_b = projected[j]

            try:
                # Only process genuinely non-overlapping neighbours
                if geom_a.intersects(geom_b):
                    continue  # They overlap — handled by overlap detector
                dist = geom_a.distance(geom_b)
                if dist > gap_tolerance_m or dist <= 0:
                    continue

                # Compute gap geometry: convex hull of the gap zone - the two polygons
                combined_hull = geom_a.union(geom_b).convex_hull
                gap_region = combined_hull.difference(geom_a.union(geom_b))

                if gap_region.is_empty:
                    continue

                area = gap_region.area
                if area < min_gap_area_m2 or area > max_gap_area_m2:
                    continue

                # Estimate width from area / length approximation
                estimated_width = area / (gap_region.length + 1e-9)

                severity = "high" if dist < 0.5 else "medium"
                gap_geojson = metric_geom_to_geojson(gap_region)

                flags.append(GapFlag(
                    feature_id=fid_a,
                    related_feature_id=fid_b,
                    severity=severity,
                    area_m2=area,
                    estimated_width_m=estimated_width,
                    gap_geometry=gap_geojson,
                ))
            except Exception as e:
                log.warning(f"Gap detection error between {fid_a} and {fid_b}: {e}")

    return flags
