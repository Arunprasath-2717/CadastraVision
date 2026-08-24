"""
app/integrations/ai/segmentation.py
─────────────────────────────────────
SegmentationProcessor — integration boundary for Akshaya's AI pipeline.

DO NOT implement YOLO/SAM/samgeo here. This file defines the interface
that Akshaya's module will implement.

Phase 2: Interface defined.
Phase 3: Wire real implementation.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class SegmentationProcessor:
    """
    Interface for AI segmentation of imagery tiles.

    Akshaya implements the concrete subclass in ai-service/.
    The ImageryService calls process_tile() after tile creation.

    INTEGRATION STUB — replace body with Akshaya's implementation.
    """

    async def process_tile(self, tile_id: str, job_id: str) -> dict:
        """
        Trigger AI segmentation for the given tile.

        Returns a result dict conforming to:
        {
            "features": [{"geometry_wkt": ..., "feature_type": ..., "confidence": ...}],
            "parcel_count": int,
            "processing_time_s": float,
        }

        STUB — returns empty result.
        """
        logger.info("[AI STUB] SegmentationProcessor.process_tile tile=%s job=%s", tile_id, job_id)
        return {"features": [], "parcel_count": 0, "processing_time_s": 0.0}
