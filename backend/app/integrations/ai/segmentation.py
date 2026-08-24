"""
app/integrations/ai/segmentation.py
─────────────────────────────────────
SegmentationProcessor & AI Result Schemas.

Integration boundary for Akshaya's AI segmentation model pipeline.
Provides validated result data structures, confidence validation,
and model metadata tracking.

DO NOT hardcode YOLO/SAM/samgeo dependencies into core logic.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.core.errors import ValidationError

logger = logging.getLogger(__name__)


@dataclass
class SegmentationFeature:
    """Represents a single feature extracted by the AI pipeline."""

    feature_type: str  # "building", "road", "land_use", "parcel_candidate"
    geometry_wkt: str
    confidence: float
    feature_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Validate confidence range
        if not (0.0 <= self.confidence <= 1.0):
            raise ValidationError(
                detail=f"Invalid confidence score {self.confidence}. Must be between 0.0 and 1.0."
            )
        # Basic WKT structure check
        if not self.geometry_wkt or not self.geometry_wkt.strip():
            raise ValidationError(detail="Feature geometry_wkt cannot be empty.")
        valid_types = {"building", "road", "land_use", "parcel_candidate"}
        if self.feature_type not in valid_types:
            raise ValidationError(
                detail=f"Unsupported feature type '{self.feature_type}'. Supported: {sorted(valid_types)}"
            )


@dataclass
class SegmentationResult:
    """Validated result returned by SegmentationProcessor."""

    tile_id: str
    processing_job_id: str
    model_name: str = "cadastravision-segmentation-stub"
    model_version: str = "v1.0.0"
    features: list[SegmentationFeature] = field(default_factory=list)
    processing_time_s: float = 0.0

    @property
    def parcel_candidates(self) -> list[SegmentationFeature]:
        return [f for f in self.features if f.feature_type == "parcel_candidate"]

    @property
    def building_footprints(self) -> list[SegmentationFeature]:
        return [f for f in self.features if f.feature_type == "building"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "tile_id": self.tile_id,
            "processing_job_id": self.processing_job_id,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "feature_count": len(self.features),
            "parcel_count": len(self.parcel_candidates),
            "building_count": len(self.building_footprints),
            "processing_time_s": self.processing_time_s,
            "features": [
                {
                    "feature_id": f.feature_id,
                    "feature_type": f.feature_type,
                    "geometry_wkt": f.geometry_wkt,
                    "confidence": f.confidence,
                    "metadata": f.metadata,
                }
                for f in self.features
            ],
        }


class SegmentationProcessor:
    """
    Backend interface for AI tile segmentation.

    Akshaya implements the concrete AI inference engine.
    The core service calls process_tile() during job processing.
    """

    def __init__(self, mock_features: list[SegmentationFeature] | None = None) -> None:
        self._mock_features = mock_features

    async def process_tile(self, tile_id: str, job_id: str) -> SegmentationResult:
        """
        Execute AI segmentation on an imagery tile.

        INTEGRATION STUB — returns deterministic feature extractions.
        """
        logger.info("[AI SERVICE] Processing tile=%s for job=%s", tile_id, job_id)

        features = self._mock_features
        if features is None:
            # Default deterministic features for integration testing
            features = [
                SegmentationFeature(
                    feature_type="building",
                    geometry_wkt="POLYGON ((10 10, 10 20, 20 20, 20 10, 10 10))",
                    confidence=0.92,
                    metadata={"floors": 2, "material": "concrete"},
                ),
                SegmentationFeature(
                    feature_type="parcel_candidate",
                    geometry_wkt="POLYGON ((0 0, 0 50, 50 50, 50 0, 0 0))",
                    confidence=0.88,
                    metadata={"zone": "residential", "jurisdiction": "district-1"},
                ),
            ]

        result = SegmentationResult(
            tile_id=tile_id,
            processing_job_id=job_id,
            model_name="cadastravision-segmentation-stub",
            model_version="v1.0.0",
            features=features,
            processing_time_s=0.45,
        )
        return result
