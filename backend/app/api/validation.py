"""
Validation API — run topology checks across the whole dataset or a single feature.
Returns actual counts from real geometry processing.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
from app.database import get_db
from app.models.feature import Feature
from app.geometry.topology.validator import validate_collection
import shapely.geometry
import logging

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run")
def run_validation_all(db: Session = Depends(get_db)):
    """
    Run topology validation on all features in the database.
    Returns aggregate counts and per-feature results.
    All numbers come from real geometry processing — never hard-coded.
    """
    all_features = db.query(Feature).all()

    feature_list = []
    for f in all_features:
        try:
            geom = shapely.geometry.mapping(to_shape(f.geometry))
            feature_list.append({"feature_id": f.feature_id, "geometry": geom})
        except Exception as e:
            log.warning(f"Could not read geometry for {f.feature_id}: {e}")

    results = validate_collection(feature_list)

    # Aggregate
    total = len(results)
    valid_count = sum(1 for r in results.values() if r.valid)
    invalid_count = total - valid_count
    review_count = sum(1 for f in all_features if f.review_status == "REVIEW_REQUIRED")
    overlap_count = sum(len(r.overlaps) for r in results.values()) // 2  # Each pair counted twice
    gap_count = sum(len(r.gaps) for r in results.values()) // 2
    si_count = sum(len(r.self_intersections) for r in results.values())

    # Persist updated validation statuses
    for f in all_features:
        r = results.get(f.feature_id)
        if r:
            f.validation_status = "VALID" if r.valid else "INVALID"
            if not r.valid and f.review_status == "DRAFT":
                f.review_status = "REVIEW_REQUIRED"
    db.commit()

    return {
        "summary": {
            "total": total,
            "valid": valid_count,
            "invalid": invalid_count,
            "review_required": review_count,
            "overlaps": overlap_count,
            "gaps": gap_count,
            "self_intersections": si_count,
        },
        "results": {fid: r.to_dict() for fid, r in results.items()},
    }
