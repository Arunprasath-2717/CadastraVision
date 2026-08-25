"""
Features API — CRUD, topology validation, geometry update (with HTTP 409 version check), flags.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.shape import to_shape, from_shape
from app.database import get_db
from app.models.feature import Feature
from app.geometry.validator import validate_geojson_geometry
from app.geometry.topology.validator import validate_single
from app.geometry.metrics import geojson_area_m2, geojson_perimeter_m
from app.geometry.confidence import calculate_confidence
import shapely.geometry
import logging

log = logging.getLogger(__name__)
router = APIRouter()


def _feature_to_dict(f: Feature) -> dict:
    geom = shapely.geometry.mapping(to_shape(f.geometry))
    return {
        "feature_id": f.feature_id,
        "feature_type": f.feature_type,
        "source": f.source,
        "geometry": geom,
        "crs": "EPSG:4326",
        "geometry_version": f.geometry_version,
        "confidence_score": f.confidence_score,
        "validation_status": f.validation_status,
        "review_status": f.review_status,
        "approval_status": f.approval_status,
        "properties": f.properties or {},
    }


@router.get("/")
def list_features(
    feature_type: str = None,
    review_status: str = None,
    db: Session = Depends(get_db),
):
    q = db.query(Feature)
    if feature_type:
        q = q.filter(Feature.feature_type == feature_type)
    if review_status:
        q = q.filter(Feature.review_status == review_status)
    features = q.limit(1000).all()
    return [_feature_to_dict(f) for f in features]


@router.get("/{feature_id}")
def get_feature(feature_id: str, db: Session = Depends(get_db)):
    f = db.query(Feature).filter(Feature.feature_id == feature_id).first()
    if not f:
        raise HTTPException(status_code=404, detail=f"Feature {feature_id!r} not found.")
    return _feature_to_dict(f)


@router.post("/import")
def import_features(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
):
    """
    Import a GeoJSON FeatureCollection from the frontend.
    Converts to canonical features and stores in PostGIS.
    Skips duplicates using stable feature_id.
    """
    features = payload.get("features", [])
    created, skipped = 0, 0

    for feat in features:
        props = feat.get("properties", {}) or {}
        fid = (
            props.get("feature_id")
            or props.get("osm_id")
            or props.get("id")
            or f"import:{shapely.geometry.shape(feat['geometry']).wkt[:32]}"
        )
        geom_dict = feat.get("geometry")
        ftype = props.get("feature_type", "building")

        if not geom_dict:
            skipped += 1
            continue

        # Skip duplicates
        existing = db.query(Feature).filter(Feature.feature_id == fid).first()
        if existing:
            skipped += 1
            continue

        try:
            shp = shapely.geometry.shape(geom_dict)
            wkb = from_shape(shp, srid=4326)
            db.add(Feature(
                feature_id=fid,
                feature_type=ftype,
                source=props.get("source", "import"),
                geometry=wkb,
                properties=props,
            ))
            created += 1
        except Exception as e:
            log.warning(f"Could not import feature {fid}: {e}")
            skipped += 1

    db.commit()
    return {"created": created, "skipped": skipped}


@router.put("/{feature_id}/geometry")
def update_geometry(
    feature_id: str,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
):
    """
    Update feature geometry with version check (HTTP 409 on stale version).
    Runs full GIS validation after update.
    """
    client_version = payload.get("geometry_version")
    new_geom_dict = payload.get("geometry")

    if not new_geom_dict:
        raise HTTPException(status_code=422, detail="'geometry' is required.")

    f = db.query(Feature).filter(Feature.feature_id == feature_id).first()
    if not f:
        raise HTTPException(status_code=404, detail=f"Feature {feature_id!r} not found.")

    # Version check — HTTP 409 on mismatch
    if client_version is not None and client_version != f.geometry_version:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "geometry_version_conflict",
                "message": "Client geometry version is stale.",
                "server_version": f.geometry_version,
                "client_version": client_version,
            },
        )

    # Validate new geometry
    val = validate_geojson_geometry(new_geom_dict)
    if not val.valid:
        raise HTTPException(status_code=422, detail={
            "error": "invalid_geometry",
            "issues": val.to_dict()["issues"],
        })

    # Run topology
    topo = validate_single(feature_id, new_geom_dict)

    # Update geometry
    try:
        shp = shapely.geometry.shape(new_geom_dict)
        f.geometry = from_shape(shp, srid=4326)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Geometry conversion failed: {e}")

    f.geometry_version = (f.geometry_version or 1) + 1
    f.validation_status = "VALID" if topo.valid else "INVALID"
    f.review_status = "REVIEW_REQUIRED" if not topo.valid else "EDITED"

    # Confidence
    area = geojson_area_m2(new_geom_dict)
    perim = geojson_perimeter_m(new_geom_dict)
    conf = calculate_confidence(
        topology_valid=topo.valid,
        topology_flags=topo.flags,
        source=f.source or "unknown",
        area_m2=area,
        perimeter_m=perim,
    )
    f.confidence_score = conf.score

    db.commit()
    db.refresh(f)
    return {**_feature_to_dict(f), "topology": topo.to_dict(), "confidence": conf.to_dict()}


@router.post("/{feature_id}/validate")
def validate_feature(feature_id: str, db: Session = Depends(get_db)):
    """Run GIS validation on an existing feature."""
    f = db.query(Feature).filter(Feature.feature_id == feature_id).first()
    if not f:
        raise HTTPException(status_code=404, detail=f"Feature {feature_id!r} not found.")

    geom_dict = shapely.geometry.mapping(to_shape(f.geometry))
    topo = validate_single(feature_id, geom_dict)

    area = geojson_area_m2(geom_dict)
    perim = geojson_perimeter_m(geom_dict)
    conf = calculate_confidence(
        topology_valid=topo.valid,
        topology_flags=topo.flags,
        source=f.source or "unknown",
        area_m2=area,
        perimeter_m=perim,
    )

    f.validation_status = "VALID" if topo.valid else "INVALID"
    f.confidence_score = conf.score
    if not topo.valid:
        f.review_status = "REVIEW_REQUIRED"
    db.commit()

    return {"topology": topo.to_dict(), "confidence": conf.to_dict(), "feature": _feature_to_dict(f)}


@router.get("/{feature_id}/flags")
def get_feature_flags(feature_id: str, db: Session = Depends(get_db)):
    """Return the topology flags for a feature."""
    f = db.query(Feature).filter(Feature.feature_id == feature_id).first()
    if not f:
        raise HTTPException(status_code=404, detail=f"Feature {feature_id!r} not found.")

    geom_dict = shapely.geometry.mapping(to_shape(f.geometry))
    topo = validate_single(feature_id, geom_dict)
    return {"feature_id": feature_id, "flags": topo.flags, "topology": topo.to_dict()}
