"""
Metric calculator — area, perimeter, distance calculations.

ALL calculations use the project processing CRS (metric units).
Results are in square metres and metres respectively.
Never calculate area/distance in EPSG:4326 degree units.
"""
from shapely.geometry.base import BaseGeometry
from typing import Optional
from app.geometry.crs import to_metric, to_wgs84, geojson_geom_to_metric
import logging

log = logging.getLogger(__name__)


def area_m2(geom_4326: BaseGeometry) -> float:
    """Return area in square metres using configured processing CRS."""
    projected = to_metric(geom_4326)
    return projected.area


def perimeter_m(geom_4326: BaseGeometry) -> float:
    """Return perimeter/length in metres using configured processing CRS."""
    projected = to_metric(geom_4326)
    return projected.length


def distance_m(geom_a_4326: BaseGeometry, geom_b_4326: BaseGeometry) -> float:
    """Return minimum distance in metres between two geometries."""
    proj_a = to_metric(geom_a_4326)
    proj_b = to_metric(geom_b_4326)
    return proj_a.distance(proj_b)


def centroid_wgs84(geom_4326: BaseGeometry) -> dict:
    """Return GeoJSON Point of the centroid in EPSG:4326."""
    import shapely.geometry
    centroid_proj = to_metric(geom_4326).centroid
    centroid_wgs = to_wgs84(centroid_proj)
    return shapely.geometry.mapping(centroid_wgs)


def geojson_area_m2(geojson_geom: dict) -> Optional[float]:
    """Convenience: area from a GeoJSON geometry dict."""
    try:
        projected, _ = geojson_geom_to_metric(geojson_geom)
        return projected.area
    except Exception as e:
        log.warning(f"Could not calculate area: {e}")
        return None


def geojson_perimeter_m(geojson_geom: dict) -> Optional[float]:
    """Convenience: perimeter/length from a GeoJSON geometry dict."""
    try:
        projected, _ = geojson_geom_to_metric(geojson_geom)
        return projected.length
    except Exception as e:
        log.warning(f"Could not calculate perimeter: {e}")
        return None
