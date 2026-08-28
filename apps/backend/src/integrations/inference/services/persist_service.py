"""
Author: Sean Froning
Created Date: 8.28.2026
Operations pertaining to Inference persistence
"""

import io
import numpy as np
from typing import Optional, Tuple
from fiery_python import db_pool, logging
from fiery_python import (
    PoolFetch,
    InferenceDeformation,
    TrainingInterferogram,
    TrainingDeformation,
)
from ..queries.select_training_interferogram import QUERY as SELECT_INTERFEROGRAM
from ..queries.select_training_deformation import QUERY as SELECT_DEFORMATION
from ..queries.upsert_inference_deformation import QUERY as UPSERT_DEFORMATION

logger = logging.get_logger(__name__)


class InferencePersistService:
    """Load npz bytes; select interferogram, deformation; upsert deformation"""

    @staticmethod
    def load_npz(body: bytes) -> np.ndarray:
        buf = io.BytesIO(body)
        return np.load(buf)["data"]

    @staticmethod
    def select_interferogram(
        interferogram_or_volcano_id: Tuple[Optional[str], Optional[str]],
    ) -> Optional[TrainingInterferogram]:
        interferogram_id, volcano_id = interferogram_or_volcano_id
        if not interferogram_id and not volcano_id:
            logger.warning("fetch_training_interferogram_impossible")
            return None
        row = db_pool.run(
            SELECT_INTERFEROGRAM,
            (interferogram_id, volcano_id),
            fetch=PoolFetch.ONE,
            error_event="fetch_training_interferogram_failed",
        )
        if not row:
            logger.warning(
                "fetch_training_interferogram_empty",
                interferogram_id=interferogram_id or "None",
                volcano_id=volcano_id or "None",
            )
            return None
        return TrainingInterferogram(
            id=row.get("id"),
            source=row.get("source"),
            split=row.get("split"),
            label=row.get("label"),
            frame_id=row.get("frame_id"),
            primary_at=row.get("primary_at"),
            secondary_at=row.get("secondary_at"),
            coherence_mean=row.get("coherence_mean"),
            is_augmented=row.get("is_augmented"),
            storage_path=row.get("storage_path"),
            deformation_source_id=row.get("deformation_source_id"),
            volcano_id=row.get("volcano_id"),
        )

    @staticmethod
    def select_deformation(session_id: str) -> Optional[TrainingDeformation]:
        row = db_pool.run(
            SELECT_DEFORMATION,
            (session_id,),
            fetch=PoolFetch.ONE,
            error_event="fetch_training_deformation_failed",
        )
        if not row:
            logger.warning("fetch_training_deformation_empty", session_id=session_id)
            return None
        return TrainingDeformation(
            id=row.get("id"),
            patch_px=row.get("patch_px"),
            wrap_rad=row.get("wrap_rad"),
            normalize=row.get("normalize"),
            coherence_min=row.get("coherence_min"),
            class_id=row.get("class_id"),
        )

    @staticmethod
    def upsert_deformation(deformation: InferenceDeformation) -> None:
        db_pool.run(
            UPSERT_DEFORMATION,
            deformation.prepare_for_storage(include_id=False),
        )
