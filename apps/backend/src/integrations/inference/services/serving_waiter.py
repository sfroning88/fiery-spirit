"""
Author: Sean Froning
Created Date: 8.28.2026
Processing functions for Serving waiter
"""

import time
import torch
import torch.nn.functional as F
import numpy as np
from datetime import datetime, timezone
from decimal import Decimal
from torch import Tensor
from typing import Dict, Tuple
from fiery_python import error, logging
from fiery_python import (
    STORAGE_OP_VERSION,
    TransformationRejected,
    Transformation,
    InferenceAbstainReason,
    ModelTier,
    ModelRole,
    TrainingDeformationLabel,
    InferenceDeformation,
    TrainingDeformation,
)
from ml import LoadedModel, model_registry
from .persist_service import InferencePersistService

logger = logging.get_logger(__name__)

_DEFORMATION_CLASS_ORDER = [
    TrainingDeformationLabel.NEGATIVE,
    TrainingDeformationLabel.POSITIVE,
]
_VIT_PX = 224


class InferenceServingWaiter:
    """"""

    @classmethod
    def run(
        cls, key: Tuple[ModelTier, ModelRole], sample: np.ndarray, interferogram_id: str
    ) -> Tuple[InferenceDeformation, Dict[str, Decimal]]:
        if not model_registry.is_ready(key):
            raise error(f"No is_ready model for {key} in registry")
        model = model_registry.get(key)
        metadata = LoadedModel(**model_registry.get_metadata(key))
        session_id = metadata.session_id
        training_deformation = InferencePersistService.select_deformation(session_id)
        if not training_deformation:
            raise error("No training_deformation was found")
        abstained = False
        abstained_reason = None
        valid_transformation = True
        started = time.perf_counter()
        try:
            tensor = cls._image_to_nchw_tensor(
                cls._preprocess(metadata, sample, training_deformation)
            )
        except TransformationRejected as err:
            abstained = True
            abstained_reason = Transformation.map_rejection_to_reason(str(err))
            valid_transformation = False
        threshold = Decimal(str(metadata.preprocessing["threshold"]))
        abstention_band = Decimal(str(metadata.preprocessing["abstention_band"]))
        score = None
        label = None
        probabilities: Dict[str, Decimal] = {}
        if valid_transformation:
            with torch.no_grad():
                logits = model.eval()(tensor.unsqueeze(0))
                probs = torch.softmax(logits, dim=-1)[0]
            probabilities = {
                deformation_label.value: Decimal(str(probs[idx].item()))
                for idx, deformation_label in enumerate(_DEFORMATION_CLASS_ORDER)
            }
            score = probabilities["positive"]
            if abs(score - threshold) < abstention_band:
                abstained = True
                abstained_reason = InferenceAbstainReason.LOW_CONFIDENCE
            else:
                label = (
                    TrainingDeformationLabel.POSITIVE
                    if (score >= threshold)
                    else TrainingDeformationLabel.NEGATIVE
                )
        inferred_at = datetime.now(timezone.utc)
        latency_ms = Decimal(str(round((time.perf_counter() - started) * 1000, 3)))
        return (
            InferenceDeformation(
                score=score,
                label=label,
                threshold_used=threshold,
                abstention_band=abstention_band,
                abstained=abstained,
                abstained_reason=abstained_reason,
                transform_hash=metadata.preprocessing["transform_hash"],
                op_version=int(metadata.preprocessing["op_version"]),
                latency_ms=latency_ms,
                inferred_at=inferred_at,
                artifact_id=metadata.artifact_id,
                interferogram_id=interferogram_id,
            ),
            probabilities,
        )

    @classmethod
    def _preprocess(
        cls, metadata: LoadedModel, raw: np.ndarray, deformation: TrainingDeformation
    ) -> np.ndarray:
        decision = metadata.preprocessing
        if int(decision["op_version"]) != STORAGE_OP_VERSION:
            raise error(f"Artifact-Contract mismatch for {metadata.artifact_id}")
        resolved = Transformation.transform_hash_deformation(deformation)
        if resolved != decision["transform_hash"]:
            raise error(f"Artifact-Contract mismatch for {metadata.artifact_id}")
        return Transformation.apply_deformation(raw, deformation)

    @staticmethod
    def _image_to_nchw_tensor(image: np.ndarray) -> Tensor:
        tensor = torch.from_numpy(image).float()
        if tensor.ndim != 2:
            raise error("Expected image array of shape (H, W)")
        tensor = tensor.unsqueeze(0).unsqueeze(0)
        if tensor.shape[-2] != _VIT_PX or tensor.shape[-1] != _VIT_PX:
            tensor = F.interpolate(
                tensor, size=(_VIT_PX, _VIT_PX), mode="bilinear", align_corners=False
            )
        return tensor.squeeze(0).repeat(3, 1, 1)
