"""
Geometry Validator — checks geometry for well-formedness before any GIS processing.

Never raises raw Shapely exceptions into the API layer.
All failures become structured ValidationResult objects.
"""
from dataclasses import dataclass, field
from typing import Optional, List
import shapely.geometry
import shapely.validation
from shapely.geometry.base import BaseGeometry
import logging

log = logging.getLogger(__name__)

SUPPORTED_TYPES = {
    "Point", "MultiPoint",
    "LineString", "MultiLineString",
    "Polygon", "MultiPolygon",
    "GeometryCollection",
}


@dataclass
class ValidationIssue:
    code: str
    message: str
    severity: str = "error"  # error | warning
    location: Optional[dict] = None  # GeoJSON point or geometry where issue occurs


@dataclass
class ValidationResult:
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    repaired_geometry: Optional[dict] = None
    repair_method: Optional[str] = None

    def add(self, code: str, message: str, severity: str = "error", location=None):
        self.issues.append(ValidationIssue(code, message, severity, location))
        if severity == "error":
            self.valid = False

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "issues": [
                {"code": i.code, "message": i.message, "severity": i.severity, "location": i.location}
                for i in self.issues
            ],
            "repaired_geometry": self.repaired_geometry,
            "repair_method": self.repair_method,
        }


def validate_geojson_geometry(geojson_geom: dict) -> ValidationResult:
    """
    Full geometry validation pipeline for a GeoJSON geometry dict.
    Returns a ValidationResult — never raises.
    """
    result = ValidationResult(valid=True)

    # 1. Existence
    if not geojson_geom:
        result.add("EMPTY_GEOMETRY", "Geometry is null or missing.")
        return result

    # 2. Type check
    geom_type = geojson_geom.get("type")
    if geom_type not in SUPPORTED_TYPES:
        result.add("UNSUPPORTED_TYPE", f"Geometry type '{geom_type}' is not supported.")
        return result

    # 3. Coordinates exist
    if geom_type != "GeometryCollection" and not geojson_geom.get("coordinates"):
        result.add("EMPTY_COORDINATES", "Geometry has no coordinates.")
        return result

    # 4. Parse with Shapely
    try:
        shp: BaseGeometry = shapely.geometry.shape(geojson_geom)
    except Exception as exc:
        result.add("PARSE_ERROR", f"Could not parse geometry: {exc}")
        return result

    # 5. Empty geometry
    if shp.is_empty:
        result.add("DEGENERATE", "Geometry is empty after parsing.")
        return result

    # 6. Finite coordinates — use shapely.get_coordinates() which works on all types
    try:
        all_coords = shapely.get_coordinates(shp)
        for coord in all_coords:
            if not all(isinstance(float(v), float) and abs(v) < 1e15 for v in coord):
                result.add("INFINITE_COORDINATES", "Geometry contains non-finite coordinate values.")
                return result
    except Exception:
        pass  # Non-critical coordinate check; validity check below will catch issues


    # 7. Shapely validity
    if not shp.is_valid:
        reason = shapely.validation.explain_validity(shp)
        result.add("INVALID_GEOMETRY", f"Shapely validity check failed: {reason}")
        # Attempt buffer(0) repair
        try:
            repaired = shp.buffer(0)
            if repaired.is_valid and not repaired.is_empty:
                result.repaired_geometry = shapely.geometry.mapping(repaired)
                result.repair_method = "buffer(0)"
                result.add(
                    "AUTO_REPAIRED",
                    "Geometry was automatically repaired using buffer(0). Review required.",
                    severity="warning"
                )
        except Exception:
            pass

    # 8. Ring checks for polygons
    if geom_type in ("Polygon", "MultiPolygon"):
        polys = [shp] if geom_type == "Polygon" else list(shp.geoms)
        for poly in polys:
            if not hasattr(poly, "exterior"):
                continue
            if len(poly.exterior.coords) < 4:
                result.add("DEGENERATE_RING", "Polygon exterior ring has fewer than 4 coordinates.")
            for interior in poly.interiors:
                if len(interior.coords) < 4:
                    result.add("DEGENERATE_HOLE", "Polygon interior ring (hole) has fewer than 4 coordinates.")

    return result


def shapely_from_geojson(geojson_geom: dict) -> Optional[BaseGeometry]:
    """Safe conversion — returns None on failure."""
    try:
        return shapely.geometry.shape(geojson_geom)
    except Exception:
        return None
