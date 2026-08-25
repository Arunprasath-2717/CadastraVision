"""app/routers/metrics.py — GET /v1/models/metrics (AI model performance)."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.metrics import ModelMetrics

router = APIRouter(prefix="/v1/models", tags=["Metrics"])


@router.get(
    "/metrics",
    response_model=ModelMetrics,
    summary="Get AI model metrics",
    description=(
        "Retrieve performance metrics for the deployed segmentation model. "
        "**INTEGRATION STUB** — Akshaya's model pipeline populates this (Phase 3)."
    ),
)
async def get_model_metrics() -> ModelMetrics:
    return ModelMetrics(
        model_name="yolo-cadastral",
        model_version="stub-0.0.0",
    )
