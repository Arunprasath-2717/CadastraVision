from typing import Dict, Any
import uuid

def normalize_overture_feature(raw_feature: Dict[str, Any], feature_type: str) -> Dict[str, Any]:
    """
    Normalizes a raw Overture GeoJSON feature into our canonical schema.
    """
    props = raw_feature.get("properties", {})
    
    # Extract stable GERS ID or source ID if available
    gers_id = props.get("gers_id")
    source_id = props.get("id") or gers_id
    
    if source_id:
        feature_id = f"overture:{source_id}"
    else:
        # Fallback to UUID if no stable ID exists
        feature_id = f"overture:generated:{uuid.uuid4()}"
    
    canonical = {
        "feature_id": feature_id,
        "feature_type": feature_type,
        "source": "overture",
        "geometry": raw_feature.get("geometry"),
        "properties": {
            "overture_id": source_id,
            "gers_id": gers_id,
            "subtype": props.get("subtype"),
            "class": props.get("class"),
            "names": props.get("names")
        }
    }
    
    return canonical
