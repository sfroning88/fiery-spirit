"""
Author: Sean Froning
Created Date: 8.29.2026
Processing functions for Serving waiter
"""

import time
import torch
import torch.nn.functional as F
import numpy as np
from datetime import datetime, timezone
from decimal import Decimal
from torch import Tensor
from typing import Dict, Optional, Tuple, Union, assert_never
from fiery_python import error, logging
from fiery_python import (
    STORAGE_OP_VERSION,
    TransformationRejected,
    Transformation,
    InferenceAbstainReason,
    ModelTier,
    ModelRole,
    TrainingDeformationLabel,
    TrainingSeismicLabel,
    InferenceDeformation,
    InferenceLanguage,
    InferenceSeismic,
    TrainingDeformation,
    TrainingLanguageLabel,
    TrainingSeismic,
)
from ml import LoadedModel, model_registry
from .persist_service import InferencePersistService

logger = logging.get_logger(__name__)

_DEFORMATION_CLASS_ORDER = [
    TrainingDeformationLabel.NEGATIVE,
    TrainingDeformationLabel.POSITIVE,
]
_SEISMIC_CLASS_ORDER = [
    TrainingSeismicLabel.VT,
    TrainingSeismicLabel.LP,
    TrainingSeismicLabel.TR,
    TrainingSeismicLabel.TC,
]
_VIT_PX = 224
_LANGUAGE_CLASS_ORDER = [
    TrainingLanguageLabel.GREEN,
    TrainingLanguageLabel.YELLOW,
    TrainingLanguageLabel.ORANGE,
    TrainingLanguageLabel.RED,
]
_LANGUAGE_MAX_NEW_TOKENS = 64


class InferenceServingWaiter:
    """Serve inference predictions from the model registry"""

    @classmethod
    def run(
        cls,
        key: Tuple[ModelTier, ModelRole],
        sample: Optional[np.ndarray] = None,
        interferogram_id: Optional[str] = None,
        seismic_event_id: Optional[str] = None,
        volcano_id: Optional[str] = None,
    ) -> Tuple[
        Union[InferenceDeformation, InferenceSeismic, InferenceLanguage],
        Dict[str, Decimal],
    ]:
        if key == (ModelTier.CLOUD, ModelRole.ANALYST):
            if not volcano_id:
                raise error("No volcano_id is selected")
            inference, probabilities, _transform_hash, _op_version = cls._language(
                volcano_id
            )
            return inference, probabilities
        if sample is None:
            raise error("Missing inference sample")
        if not model_registry.is_ready(key):
            raise error(f"No is_ready model for {key} in registry")
        if interferogram_id and seismic_event_id:
            raise error("Received both interferogram_id and seismic_event_id")
        model = model_registry.get(key)
        metadata = LoadedModel(**model_registry.get_metadata(key))
        session_id = metadata.session_id
        if interferogram_id:
            training_deformation = InferencePersistService.select_deformation(
                session_id
            )
            if not training_deformation:
                raise error("No training_deformation was found")
            training_entity: Union[TrainingDeformation, TrainingSeismic] = (
                training_deformation
            )
        elif seismic_event_id:
            training_seismic = InferencePersistService.select_seismic(session_id)
            if not training_seismic:
                raise error("No training_seismic was found")
            training_entity = training_seismic
        else:
            raise error("Missing both interferogram_id and seismic_event_id")
        abstained = False
        abstained_reason = None
        valid_transformation = True
        started = time.perf_counter()
        tensor: Optional[Tensor] = None
        try:
            transformed = cls._preprocess(metadata, sample, training_entity)
            if interferogram_id:
                tensor = cls._image_to_nchw_tensor(transformed)
            elif seismic_event_id:
                tensor = cls._mel_to_nchw_tensor(transformed)
            else:
                raise error("Missing both interferogram_id and seismic_event_id")
        except TransformationRejected as err:
            abstained = True
            abstained_reason = Transformation.map_rejection_to_reason(str(err))
            valid_transformation = False
        threshold = Decimal(str(metadata.preprocessing["threshold"]))
        abstention_band = Decimal(str(metadata.preprocessing["abstention_band"]))
        score = None
        deformation_label: Optional[TrainingDeformationLabel] = None
        seismic_label: Optional[TrainingSeismicLabel] = None
        probabilities: Dict[str, Decimal] = {}
        seismic_probabilities: list[Decimal] = []
        if valid_transformation and tensor is not None:
            with torch.no_grad():
                logits = model.eval()(tensor.unsqueeze(0))
                probs = torch.softmax(logits, dim=-1)[0]
            if interferogram_id:
                probabilities = {
                    deformation_class.value: Decimal(str(probs[idx].item()))
                    for idx, deformation_class in enumerate(_DEFORMATION_CLASS_ORDER)
                }
                score = probabilities["positive"]
                if abs(score - threshold) < abstention_band:
                    abstained = True
                    abstained_reason = InferenceAbstainReason.LOW_CONFIDENCE
                else:
                    deformation_label = (
                        TrainingDeformationLabel.POSITIVE
                        if (score >= threshold)
                        else TrainingDeformationLabel.NEGATIVE
                    )
            elif seismic_event_id:
                seismic_probabilities = [
                    Decimal(str(probs[idx].item()))
                    for idx in range(len(_SEISMIC_CLASS_ORDER))
                ]
                probabilities = {
                    seismic_class.value: seismic_probabilities[idx]
                    for idx, seismic_class in enumerate(_SEISMIC_CLASS_ORDER)
                }
                predicted = int(probs.argmax().item())
                max_probability = seismic_probabilities[predicted]
                if abs(max_probability - threshold) < abstention_band:
                    abstained = True
                    abstained_reason = InferenceAbstainReason.LOW_CONFIDENCE
                else:
                    seismic_label = _SEISMIC_CLASS_ORDER[predicted]
            else:
                raise error("Missing both interferogram_id and seismic_event_id")
        inferred_at = datetime.now(timezone.utc)
        latency_ms = Decimal(str(round((time.perf_counter() - started) * 1000, 3)))
        if interferogram_id:
            return (
                InferenceDeformation(
                    score=score,
                    label=deformation_label,
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
        elif seismic_event_id:
            return (
                InferenceSeismic(
                    label=seismic_label,
                    probabilities=seismic_probabilities,
                    class_order=list(_SEISMIC_CLASS_ORDER),
                    threshold_used=threshold,
                    abstention_band=abstention_band,
                    abstained=abstained,
                    abstained_reason=abstained_reason,
                    transform_hash=metadata.preprocessing["transform_hash"],
                    op_version=int(metadata.preprocessing["op_version"]),
                    latency_ms=latency_ms,
                    inferred_at=inferred_at,
                    artifact_id=metadata.artifact_id,
                    seismic_event_id=seismic_event_id,
                ),
                probabilities,
            )
        else:
            raise error("Missing both interferogram_id and seismic_event_id")

    @classmethod
    def _language(
        cls, volcano_id: str
    ) -> Tuple[InferenceLanguage, Dict[str, Decimal], str, int]:
        key = (ModelTier.CLOUD, ModelRole.ANALYST)
        if not model_registry.is_ready(key):
            raise error(f"No is_ready model for {key} in registry")
        model = model_registry.get(key)
        metadata = LoadedModel(**model_registry.get_metadata(key))
        training_language = InferencePersistService.select_language(metadata.session_id)
        if not training_language:
            raise error("No training_language was found")
        decision = metadata.preprocessing
        if int(decision["op_version"]) != STORAGE_OP_VERSION:
            raise error(f"Artifact-Contract mismatch for {metadata.artifact_id}")
        resolved = Transformation.transform_hash_language(training_language)
        if resolved != decision["transform_hash"]:
            raise error(f"Artifact-Contract mismatch for {metadata.artifact_id}")
        prompt = f"Volcano {volcano_id}. State the alert color and one sentence why."
        started = time.perf_counter()
        from transformers import AutoTokenizer

        name = getattr(model.config, "name_or_path", None)
        if not isinstance(name, str) or not name:
            raise error("Analyst model is missing a tokenizer name")
        tokenizer = AutoTokenizer.from_pretrained(name, local_files_only=True)
        encoded = tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
        ids = encoded["input_ids"]
        mask = encoded["attention_mask"]
        text = ""
        max_characters = training_language.max_characters
        with torch.no_grad():
            for _ in range(_LANGUAGE_MAX_NEW_TOKENS):
                logits = model(input_ids=ids, attention_mask=mask)
                if hasattr(logits, "logits"):
                    logits = logits.logits
                next_id = logits[:, -1, :].argmax(dim=-1)
                token = int(next_id[0].item())
                if (
                    tokenizer.eos_token_id is not None
                    and token == tokenizer.eos_token_id
                ):
                    break
                piece = tokenizer.decode([token], skip_special_tokens=True)
                if len(text) + len(piece) > max_characters:
                    break
                text += piece
                next_column = next_id.unsqueeze(1)
                ids = torch.cat([ids, next_column], dim=1)
                mask = torch.cat([mask, torch.ones_like(next_column)], dim=1)
        text = text.strip()
        label = next(
            (color for color in _LANGUAGE_CLASS_ORDER if color.value in text.lower()),
            None,
        )
        abstained = label is None or not text
        probabilities = {
            color.value: Decimal("1") if color is label else Decimal("0")
            for color in _LANGUAGE_CLASS_ORDER
        }
        inferred_at = datetime.now(timezone.utc)
        latency_ms = Decimal(str(round((time.perf_counter() - started) * 1000, 3)))
        threshold = Decimal(str(decision.get("threshold", "0")))
        abstention_band = Decimal(str(decision.get("abstention_band", "0")))
        return (
            InferenceLanguage(
                label=label,
                probabilities=[
                    probabilities[color.value] for color in _LANGUAGE_CLASS_ORDER
                ],
                class_order=list(_LANGUAGE_CLASS_ORDER),
                threshold_used=threshold,
                abstention_band=abstention_band,
                abstained=abstained,
                abstained_reason=(
                    InferenceAbstainReason.LOW_CONFIDENCE if abstained else None
                ),
                generated_text=text,
                latency_ms=latency_ms,
                inferred_at=inferred_at,
                transform_hash=decision["transform_hash"],
                op_version=int(decision["op_version"]),
                artifact_id=metadata.artifact_id,
                volcano_id=volcano_id,
            ),
            probabilities,
            decision["transform_hash"],
            int(decision["op_version"]),
        )

    @classmethod
    def _preprocess(
        cls,
        metadata: LoadedModel,
        raw: np.ndarray,
        training_entity: Union[TrainingDeformation, TrainingSeismic],
    ) -> np.ndarray:
        decision = metadata.preprocessing
        if int(decision["op_version"]) != STORAGE_OP_VERSION:
            raise error(f"Artifact-Contract mismatch for {metadata.artifact_id}")
        if isinstance(training_entity, TrainingDeformation):
            resolved = Transformation.transform_hash_deformation(training_entity)
            if resolved != decision["transform_hash"]:
                raise error(f"Artifact-Contract mismatch for {metadata.artifact_id}")
            return Transformation.apply_deformation(raw, training_entity)
        elif isinstance(training_entity, TrainingSeismic):
            resolved = Transformation.transform_hash_seismic(training_entity)
            if resolved != decision["transform_hash"]:
                raise error(f"Artifact-Contract mismatch for {metadata.artifact_id}")
            return Transformation.apply_seismic(raw, training_entity)
        assert_never(training_entity)

    @staticmethod
    def _mel_to_nchw_tensor(spectrogram: np.ndarray) -> Tensor:
        tensor = torch.from_numpy(np.ascontiguousarray(spectrogram)).float()
        if tensor.ndim != 3 or tensor.shape[0] != 1:
            raise error("Expected log-mel array of shape (1, M, F)")
        return tensor

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
