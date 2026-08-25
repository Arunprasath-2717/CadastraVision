"""app/schemas/geo.py — GeoJSON FeatureCollection schemas for geographic queries."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GeoFeatureProperties(BaseModel):
    parcel_id: str
    workflow_status: str
    confidence: float | None = None
    zone: str | None = None


class GeoFeature(BaseModel):
    type: str = "Feature"
    geometry: dict[str, Any] | None = Field(
        description="GeoJSON geometry object (null if no geometry)"
    )
    properties: GeoFeatureProperties


class GeoFeatureCollection(BaseModel):
    """GET /v1/geo/parcels — GeoJSON FeatureCollection."""
    type: str = "FeatureCollection"
    features: list[GeoFeature] = Field(default_factory=list)
    total: int = 0

    model_config = {"json_schema_extra": {"example": {
        "type": "FeatureCollection",
        "features": [],
        "total": 0,
    }}}
