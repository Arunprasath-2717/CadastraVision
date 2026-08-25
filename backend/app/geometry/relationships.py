"""
Spatial relationships engine — STRtree-indexed, all distances in metric CRS.

Computes: contains, contained_by, adjacent, overlaps, intersects, near, disjoint
between building ↔ field, building ↔ road, road ↔ field, field ↔ field.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
import shapely.geometry
import shapely.ops
import shapely.strtree
from shapely.geometry.base import BaseGeometry
from app.geometry.crs import to_metric
import logging

log = logging.getLogger(__name__)

NEAR_DISTANCE_M = 50.0  # Distance threshold for "near" relationship


@dataclass
class SpatialRelationship:
    source_id: str
    target_id: str
    relationship_type: str   # contains|contained_by|adjacent|overlaps|intersects|near|disjoint
    distance_m: Optional[float] = None
    intersection_area_m2: Optional[float] = None
    weight: float = 1.0

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type,
            "distance_m": round(self.distance_m, 3) if self.distance_m is not None else None,
            "intersection_area_m2": round(self.intersection_area_m2, 4) if self.intersection_area_m2 is not None else None,
            "weight": self.weight,
        }


def _classify(geom_a: BaseGeometry, geom_b: BaseGeometry) -> tuple:
    """Return (relationship_type, distance_m, intersection_area_m2)."""
    try:
        if geom_a.contains(geom_b):
            return "contains", 0.0, geom_b.area
        if geom_b.contains(geom_a):
            return "contained_by", 0.0, geom_a.area
        if geom_a.overlaps(geom_b):
            inter = geom_a.intersection(geom_b)
            return "overlaps", 0.0, inter.area
        if geom_a.intersects(geom_b):
            return "adjacent", 0.0, 0.0
        dist = geom_a.distance(geom_b)
        if dist <= NEAR_DISTANCE_M:
            return "near", dist, None
        return "disjoint", dist, None
    except Exception as e:
        log.warning(f"Relationship classification error: {e}")
        return "unknown", None, None


def compute_relationships(
    features_a: List[Dict],   # Source features
    features_b: List[Dict],   # Target features (can be same list)
    near_distance_m: float = NEAR_DISTANCE_M,
) -> List[SpatialRelationship]:
    """
    Compute spatial relationships between two feature sets using STRtree.
    features_a and features_b are lists of {"feature_id": str, "geometry": geojson_dict}.
    """
    relationships: List[SpatialRelationship] = []

    # Project geometries
    def project_features(feats):
        result = []
        for feat in feats:
            fid = feat.get("feature_id", "unknown")
            raw = feat.get("geometry")
            if not raw:
                continue
            try:
                shp = shapely.geometry.shape(raw)
                proj = to_metric(shp)
                result.append((fid, proj))
            except Exception as e:
                log.warning(f"Skipping {fid} in relationship computation: {e}")
        return result

    proj_a = project_features(features_a)
    proj_b = project_features(features_b)

    if not proj_a or not proj_b:
        return relationships

    geoms_b = [p[1] for p in proj_b]
    tree_b = shapely.strtree.STRtree(geoms_b)

    for fid_a, geom_a in proj_a:
        # Query candidates within near_distance_m bounding box expansion
        expanded = geom_a.buffer(near_distance_m)
        candidate_indices = tree_b.query(expanded)

        for j in candidate_indices:
            fid_b, geom_b = proj_b[j]
            if fid_a == fid_b:
                continue  # Skip self

            rel_type, dist, inter_area = _classify(geom_a, geom_b)
            if rel_type in ("unknown", "disjoint"):
                continue  # Don't record completely disjoint pairs

            relationships.append(SpatialRelationship(
                source_id=fid_a,
                target_id=fid_b,
                relationship_type=rel_type,
                distance_m=dist,
                intersection_area_m2=inter_area,
            ))

    return relationships
