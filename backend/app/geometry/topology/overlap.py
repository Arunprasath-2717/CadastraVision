"""
Overlap detector — STRtree-indexed, configurable threshold, exact Shapely intersection.

Algorithm:
  1. Build STRtree index from projected geometries.
  2. For each geometry, query candidate neighbours via bounding-box.
  3. For each unique pair (i < j), compute exact intersection.
  4. Measure intersection area in metric CRS.
  5. Flag if area > threshold AND intersection is not only boundary touches.

Shared/touching boundaries are NOT flagged as overlaps.
"""
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import shapely.geometry
import shapely.ops
import shapely.strtree
from shapely.geometry.base import BaseGeometry
from app.geometry.crs import to_metric, metric_geom_to_geojson
import logging

log = logging.getLogger(__name__)

DEFAULT_OVERLAP_THRESHOLD_M2 = 0.01  # ~1cm² — shared boundary tolerance


@dataclass
class OverlapFlag:
    feature_id: str
    related_feature_id: str
    flag_type: str = "overlap"
    severity: str = "high"
    area_m2: float = 0.0
    overlap_ratio: float = 0.0
    intersection_geometry: Optional[dict] = None  # GeoJSON of exact intersection

    def to_dict(self) -> dict:
        return {
            "feature_id": self.feature_id,
            "related_feature_id": self.related_feature_id,
            "flag_type": self.flag_type,
            "severity": self.severity,
            "area_m2": round(self.area_m2, 4),
            "overlap_ratio": round(self.overlap_ratio, 6),
            "intersection_geometry": self.intersection_geometry,
        }


def _severity(area_m2: float, ratio: float) -> str:
    if ratio > 0.5 or area_m2 > 100:
        return "high"
    if ratio > 0.1 or area_m2 > 10:
        return "medium"
    return "low"


def detect_overlaps(
    features: List[Dict],  # [{"feature_id": str, "geometry": geojson_dict}, ...]
    threshold_m2: float = DEFAULT_OVERLAP_THRESHOLD_M2,
) -> List[OverlapFlag]:
    """
    Detect overlapping polygon pairs using STRtree spatial indexing.
    Only polygonal geometries are compared.
    Returns list of OverlapFlag (empty = no overlaps).
    """
    flags: List[OverlapFlag] = []

    # Project all valid polygon geometries
    projected: List[Tuple[int, str, BaseGeometry]] = []  # (index, feature_id, projected_geom)
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
            projected.append((idx, fid, proj))
        except Exception as e:
            log.warning(f"Skipping {fid} for overlap detection: {e}")

    if len(projected) < 2:
        return flags

    # Build STRtree
    geoms = [p[2] for p in projected]
    tree = shapely.strtree.STRtree(geoms)

    seen_pairs = set()

    for i, (_, fid_a, geom_a) in enumerate(projected):
        # Query candidates via bounding-box
        candidate_indices = tree.query(geom_a)
        for j in candidate_indices:
            if j <= i:
                continue  # Avoid self and duplicate pairs
            pair_key = (i, j)
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            _, fid_b, geom_b = projected[j]

            try:
                if not geom_a.intersects(geom_b):
                    continue
                # Exact intersection
                inter = geom_a.intersection(geom_b)
                if inter.is_empty:
                    continue
                # A touching boundary produces a Point or LineString — not a real overlap
                if inter.geom_type in ("Point", "MultiPoint", "LineString", "MultiLineString", "GeometryCollection"):
                    # Only flag if some polygon area actually overlaps
                    if not any(
                        sub.geom_type in ("Polygon", "MultiPolygon")
                        for sub in (inter.geoms if hasattr(inter, "geoms") else [inter])
                    ):
                        continue

                area = inter.area
                if area < threshold_m2:
                    continue

                # Compute overlap ratio relative to smaller feature
                ratio = area / min(geom_a.area, geom_b.area) if min(geom_a.area, geom_b.area) > 0 else 0

                inter_geojson = metric_geom_to_geojson(inter)

                flags.append(OverlapFlag(
                    feature_id=fid_a,
                    related_feature_id=fid_b,
                    severity=_severity(area, ratio),
                    area_m2=area,
                    overlap_ratio=ratio,
                    intersection_geometry=inter_geojson,
                ))
            except Exception as e:
                log.warning(f"Error computing overlap between {fid_a} and {fid_b}: {e}")

    return flags
