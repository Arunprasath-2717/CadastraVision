"""
app/schemas/change_detection.py
─────────────────────────────────
Pydantic schemas for geospatial change detection operations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.change import ChangeStatus, ChangeType


class ChangeRunRequest(BaseModel):
    historical_tile_id: Optional[str] = Field(None, description="UUID of historical imagery tile")
    current_tile_id: Optional[str] = Field(None, description="UUID of current imagery tile")
    tile_id_before: Optional[str] = Field(None, description="Alias for historical_tile_id")
    tile_id_after: Optional[str] = Field(None, description="Alias for current_tile_id")

    parcel_id: Optional[str] = Field(None, description="Optional target parcel UUID filter")
    algorithm_version: Optional[str] = Field("v1.0", description="Algorithm version identifier")
    confidence_threshold: Optional[float] = Field(0.5, ge=0.0, le=1.0)

    @model_validator(mode="before")
    @classmethod
    def populate_tile_ids(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("historical_tile_id") and data.get("tile_id_before"):
                data["historical_tile_id"] = data["tile_id_before"]
            if not data.get("current_tile_id") and data.get("tile_id_after"):
                data["current_tile_id"] = data["tile_id_after"]
            if not data.get("historical_tile_id"):
                data["historical_tile_id"] = "default_hist"
            if not data.get("current_tile_id"):
                data["current_tile_id"] = "default_curr"
        return data


class ChangeReviewRequest(BaseModel):
    review_notes: Optional[str] = Field(None, description="Optional notes from human reviewer")


class ChangeRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    historical_tile_id: str
    current_tile_id: str
    job_id: Optional[str] = None
    parcel_id: Optional[str] = None
    previous_feature_id: Optional[str] = None
    current_feature_id: Optional[str] = None

    change_type: ChangeType
    status: ChangeStatus
    confidence: float
    geometry_diff_wkt: Optional[str] = None
    attribute_diff_json: Optional[Dict[str, Any]] = None
    idempotency_hash: Optional[str] = None

    reviewed_by_id: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_notes: Optional[str] = None

    created_at: Any = None
    updated_at: Any = None

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence score must be bounded between 0.0 and 1.0")
        return v


class ChangeJobResponse(BaseModel):
    job_id: str
    status: str
    historical_tile_id: str
    current_tile_id: str
    changes_detected: int = 0
    created_at: Any = None


class ChangeListResponse(BaseModel):
    items: List[ChangeRecordResponse]
    total: int
