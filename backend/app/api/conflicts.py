"""
Conflicts API — detect, list, and resolve geometry conflicts.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
from app.database import get_db
from app.models.feature import Feature
from app.geometry.topology.overlap import detect_overlaps
import shapely.geometry
import logging

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
def list_conflicts(db: Session = Depends(get_db)):
    """
    Detect and return all geometric conflicts (overlaps) for current features in DB.
    Returns exact intersection geometries.
    """
    all_features = db.query(Feature).filter(
        Feature.feature_type.in_(["building", "field", "parcel"])
    ).all()

    feature_list = []
    for f in all_features:
        try:
            geom = shapely.geometry.mapping(to_shape(f.geometry))
            feature_list.append({"feature_id": f.feature_id, "geometry": geom})
        except Exception:
            pass

    overlaps = detect_overlaps(feature_list)
    return {
        "conflict_count": len(overlaps),
        "conflicts": [o.to_dict() for o in overlaps],
    }


@router.post("/{conflict_id}/resolve")
def resolve_conflict(
    conflict_id: str,  # format: "featureA__featureB"
    payload: dict = Body(...),
    db: Session = Depends(get_db),
):
    """
    Record a conflict resolution decision.
    Allowed decisions: accept_ai | retain_existing | escalate
    No silent overwrites. No default choice.
    """
    decision = payload.get("decision")
    if decision not in ("accept_ai", "retain_existing", "escalate"):
        raise HTTPException(
            status_code=422,
            detail="Decision must be one of: accept_ai, retain_existing, escalate"
        )

    # Parse the two feature IDs from conflict_id
    parts = conflict_id.split("__")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="conflict_id must be 'featureA__featureB'")

    fid_a, fid_b = parts

    # Record decision in properties — actual approval still requires backend auth
    for fid in (fid_a, fid_b):
        f = db.query(Feature).filter(Feature.feature_id == fid).first()
        if f:
            props = f.properties or {}
            props["conflict_resolution"] = {
                "decision": decision,
                "resolved_against": fid_b if fid == fid_a else fid_a,
            }
            f.properties = props
            if decision == "retain_existing":
                f.review_status = "REVALIDATED"
            elif decision == "escalate":
                f.review_status = "REVIEW_REQUIRED"

    db.commit()

    return {
        "conflict_id": conflict_id,
        "decision": decision,
        "message": f"Conflict resolution recorded: {decision}. Requires authorized approval.",
    }
