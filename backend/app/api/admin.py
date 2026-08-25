from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.feature import Feature
from app.providers.overture import OvertureProvider
from app.providers.overture_normalizer import normalize_overture_feature
from geoalchemy2.shape import from_shape
import shapely.geometry
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def fetch_and_save_overture(bbox: tuple[float, float, float, float], db: Session):
    provider = OvertureProvider()
    
    # 1. Fetch buildings
    buildings = provider.get_buildings(bbox)
    for b in buildings:
        canonical = normalize_overture_feature(b, "building")
        save_canonical_feature(canonical, db)

    # 2. Fetch roads
    roads = provider.get_roads(bbox)
    for r in roads:
        canonical = normalize_overture_feature(r, "road")
        save_canonical_feature(canonical, db)

    # 3. Fetch fields (base)
    fields = provider.get_fields(bbox)
    for f in fields:
        canonical = normalize_overture_feature(f, "field")
        save_canonical_feature(canonical, db)

def save_canonical_feature(canonical: dict, db: Session):
    # Check if exists
    feature_id = canonical["feature_id"]
    existing = db.query(Feature).filter(Feature.feature_id == feature_id).first()
    
    # Convert GeoJSON dict to WKB
    geom_shape = shapely.geometry.shape(canonical["geometry"])
    wkb_element = from_shape(geom_shape, srid=4326)

    if existing:
        # Check for conflict if locally modified
        if existing.geometry_version > 1 or existing.review_status != "DRAFT":
            # Do not overwrite, possibly log a conflict
            logger.info(f"Skipping overwrite of locally modified feature {feature_id}")
            return
        
        # Update existing
        existing.geometry = wkb_element
        existing.properties = canonical["properties"]
    else:
        # Create new
        new_feature = Feature(
            feature_id=feature_id,
            feature_type=canonical["feature_type"],
            source=canonical["source"],
            geometry=wkb_element,
            properties=canonical["properties"]
        )
        db.add(new_feature)
    
    db.commit()

@router.post("/refresh")
def refresh_data(bbox: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        minLon, minLat, maxLon, maxLat = map(float, bbox.split(","))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid bbox format")
    
    bbox_tuple = (minLon, minLat, maxLon, maxLat)
    
    # Run fetch in background to avoid blocking API
    background_tasks.add_task(fetch_and_save_overture, bbox_tuple, db)
    
    return {"message": "Data refresh started in background."}
