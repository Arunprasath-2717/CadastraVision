from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.feature import Feature
from geoalchemy2.shape import to_shape
import shapely.geometry
import json

router = APIRouter()

@router.get("/features")
def get_map_features(
    bbox: str = Query(..., description="minLon,minLat,maxLon,maxLat"),
    db: Session = Depends(get_db)
):
    try:
        minLon, minLat, maxLon, maxLat = map(float, bbox.split(","))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid bbox format")

    # Bounding box string for PostGIS
    polygon_wkt = f"POLYGON(({minLon} {minLat}, {maxLon} {minLat}, {maxLon} {maxLat}, {minLon} {maxLat}, {minLon} {minLat}))"
    
    # Query database for features intersecting the bbox
    features = db.query(Feature).filter(
        Feature.geometry.ST_Intersects(polygon_wkt)
    ).all()

    # If no features exist and provider is overture, we should ideally trigger the fetch here.
    # For now, just return what we have in PostGIS.

    feature_collection = {
        "type": "FeatureCollection",
        "features": []
    }
    
    for f in features:
        # Convert WKB geometry to GeoJSON
        geom = shapely.geometry.mapping(to_shape(f.geometry))
        feature_collection["features"].append({
            "type": "Feature",
            "id": f.feature_id,
            "geometry": geom,
            "properties": {
                "feature_type": f.feature_type,
                "source": f.source,
                "geometry_version": f.geometry_version,
                "confidence_score": f.confidence_score,
                "validation_status": f.validation_status,
                "review_status": f.review_status,
                **f.properties
            }
        })

    return feature_collection
