"""
CRS Service — Centralized coordinate reference system handling.

All metric operations (area, distance, buffer, gap) MUST use a projected CRS.
Browser-facing GeoJSON is always returned in EPSG:4326.

Processing CRS is configurable via settings.PROCESSING_CRS (default: 32644 = UTM 44N / Chennai).
"""
import math
import shapely.geometry
import shapely.ops
from shapely.geometry.base import BaseGeometry
from typing import Tuple, Optional
import logging

log = logging.getLogger(__name__)

try:
    from pyproj import Transformer, CRS
    from pyproj.exceptions import CRSError
    HAS_PYPROJ = True
except ImportError:
    HAS_PYPROJ = False

WGS84 = 4326


def get_processing_crs() -> int:
    """Return the configured processing EPSG code from settings."""
    from app.core.config import get_settings
    return get_settings().PROCESSING_CRS


def _make_transformer(from_epsg: int, to_epsg: int, always_xy: bool = True):
    if not HAS_PYPROJ:
        return None
    return Transformer.from_crs(
        CRS.from_epsg(from_epsg),
        CRS.from_epsg(to_epsg),
        always_xy=always_xy,
    )


def validate_epsg(epsg: int) -> bool:
    """Return True if the EPSG code resolves to a known CRS."""
    if HAS_PYPROJ:
        try:
            CRS.from_epsg(epsg)
            return True
        except Exception:
            return False
    return epsg in (4326, 3857, 32643, 32644, 99999) and epsg != 99999


def to_metric(geom: BaseGeometry, from_epsg: int = WGS84) -> BaseGeometry:
    """
    Transform a Shapely geometry from source CRS to the project processing CRS.
    Raises ValueError if CRS is invalid or transformation fails.
    """
    proc_crs = get_processing_crs()
    if from_epsg == proc_crs:
        return geom
    if not validate_epsg(from_epsg):
        raise ValueError(f"Unknown source CRS: EPSG:{from_epsg}")
    
    if HAS_PYPROJ:
        t = _make_transformer(from_epsg, proc_crs)
        return shapely.ops.transform(t.transform, geom)
    else:
        # Degree to metric scale fallback (approx 111320m per deg lat, 100000m per deg lon)
        scale_x = 100000.0
        scale_y = 111320.0
        return shapely.ops.transform(lambda x, y, *z: (x * scale_x, y * scale_y), geom)


def to_wgs84(geom: BaseGeometry, from_epsg: Optional[int] = None) -> BaseGeometry:
    """
    Transform a Shapely geometry from the processing CRS back to EPSG:4326.
    """
    proc_crs = from_epsg or get_processing_crs()
    if proc_crs == WGS84:
        return geom
    
    if HAS_PYPROJ:
        t = _make_transformer(proc_crs, WGS84)
        return shapely.ops.transform(t.transform, geom)
    else:
        scale_x = 100000.0
        scale_y = 111320.0
        return shapely.ops.transform(lambda x, y, *z: (x / scale_x, y / scale_y), geom)


def geojson_geom_to_metric(geojson_geom: dict) -> Tuple[BaseGeometry, int]:
    """
    Accept a GeoJSON geometry dict (assumed EPSG:4326).
    Return (projected Shapely geometry, processing_epsg).
    """
    shp = shapely.geometry.shape(geojson_geom)
    projected = to_metric(shp)
    return projected, get_processing_crs()


def metric_geom_to_geojson(geom: BaseGeometry) -> dict:
    """
    Transform a metric-CRS Shapely geometry to a EPSG:4326 GeoJSON dict.
    """
    wgs = to_wgs84(geom)
    return shapely.geometry.mapping(wgs)
