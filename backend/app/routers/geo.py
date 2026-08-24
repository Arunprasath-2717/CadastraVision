"""app/routers/geo.py — GET /v1/geo/parcels (GeoJSON FeatureCollection)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas.geo import GeoFeatureCollection

router = APIRouter(prefix="/v1/geo", tags=["Geographic Data"])


@router.get(
    "/parcels",
    response_model=GeoFeatureCollection,
    summary="Get parcels as GeoJSON",
    description=(
        "Return all (or filtered) parcels as a GeoJSON FeatureCollection. "
        "Supports bbox, zone, and jurisdiction filters. "
        "**STUB** — Phase 3: real spatial query."
    ),
)
async def get_geo_parcels(
    bbox: str | None = Query(default=None, description="Bounding box: minLon,minLat,maxLon,maxLat"),
    zone: str | None = Query(default=None),
    jurisdiction: str | None = Query(default=None),
) -> GeoFeatureCollection:
    return GeoFeatureCollection(features=[], total=0)
