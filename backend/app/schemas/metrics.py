"""app/schemas/metrics.py — AI model performance metrics schema."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ModelMetrics(BaseModel):
    """GET /v1/models/metrics — AI segmentation model performance."""
    model_name: str = Field(description="Model identifier (e.g. yolo-v8-cadastral)")
    model_version: str
    precision: float | None = Field(default=None, description="0.0 – 1.0")
    recall: float | None = Field(default=None, description="0.0 – 1.0")
    f1_score: float | None = Field(default=None, description="0.0 – 1.0")
    iou: float | None = Field(default=None, description="Intersection over Union 0.0 – 1.0")
    tiles_processed: int = 0
    parcels_generated: int = 0
    evaluated_at: datetime | None = None
    # INTEGRATION STUB — populated by Akshaya's model pipeline
    note: str = "Metrics stub: integration ready for Akshaya's AI pipeline (Phase 3)"
