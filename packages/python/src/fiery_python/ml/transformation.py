"""
Author: Sean Froning
Created Date: 8.20.2026
Deterministic interferogram preprocess for deformation shards
"""

import hashlib
import json
import numpy as np
from typing import Tuple, assert_never
from ..constants import STORAGE_OP_VERSION
from ..enums import TrainingNormalize
from ..models import TrainingDeformation


class TransformationRejected(ValueError):
    """Sample failed coherence_min (or shape) and prevent from entering shard"""


class Transformation:
    """Pure wrap / crop / normalize over (phase, coherence) stacks"""

    @staticmethod
    def _split_channels(array: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Require float32 (2, H, W): channel 0 phase, channel 1 coherence"""
        if array.ndim != 3 or array.shape[0] != 2:
            raise TransformationRejected("expected array shape (2, H, W)")
        return array[0], array[1]

    @staticmethod
    def _center_crop(array: np.ndarray, patch_px: int) -> np.ndarray:
        """Center crop to patch_px; reject if either side is smaller"""
        if patch_px <= 0:
            raise TransformationRejected("patch_px must be postive int")
        height, width = array.shape[-2], array.shape[-1]
        if height < patch_px or width < patch_px:
            raise TransformationRejected("array smaller than patch_px")
        top = (height - patch_px) // 2
        left = (width - patch_px) // 2
        return array[top : top + patch_px, left : left + patch_px]

    @staticmethod
    def _normalize(array: np.ndarray, normalize: TrainingNormalize) -> np.ndarray:
        """Apply TrainingNormalize; PERCENTILE uses fixed 2-98 clips"""
        match normalize:
            case TrainingNormalize.NONE:
                return array
            case TrainingNormalize.MINMAX:
                low, high = float(np.min(array)), float(np.max(array))
                if high <= low:
                    raise TransformationRejected("minmax range is empy")
                return (array - low) / (high - low)
            case TrainingNormalize.ZSCORE:
                mean, std = float(np.mean(array)), float(np.std(array))
                if std == 0.0:
                    raise TransformationRejected("zscore std is zero")
                return (array - mean) / std
            case TrainingNormalize.PERCENTILE:
                low, high = np.percentile(array, (2.0, 98.0))
                low, high = float(low), float(high)
                if high <= low:
                    raise TransformationRejected("percentile range is empty")
                clipped = np.clip(array, low, high)
                return (clipped - low) / (high - low)
            case _:
                assert_never(normalize)

    @classmethod
    def apply(
        cls, array: np.ndarray, training_deformation: TrainingDeformation
    ) -> np.ndarray:
        """Deterministic preprocess: wrap, crop, normalize; raise if incoherent"""
        phase, coherence = cls._split_channels(array)
        if not (np.isfinite(phase).all() and np.isfinite(coherence).all()):
            raise TransformationRejected("non-finite phase or coherence")
        if float(np.mean(coherence)) < float(training_deformation.coherence_min):
            raise TransformationRejected("coherence below min")
        wrap_rad = float(training_deformation.wrap_rad)
        if not np.isfinite(wrap_rad) or wrap_rad <= 0:
            raise TransformationRejected("wrap_rad must be positive finite")
        wrapped = np.mod(phase + wrap_rad, 2.0 * wrap_rad) - wrap_rad
        cropped = cls._center_crop(wrapped, training_deformation.patch_px)
        return cls._normalize(cropped, training_deformation.normalize)

    @classmethod
    def transform_hash(cls, training_deformation: TrainingDeformation) -> str:
        """SHA-256 of sorted deformation transformations and source of apply"""
        payload = {
            "op_version": STORAGE_OP_VERSION,
            "patch_px": training_deformation.patch_px,
            "wrap_rad": str(training_deformation.wrap_rad),
            "normalize": training_deformation.normalize.value,
            "coherence_min": str(training_deformation.coherence_min),
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        return hashlib.sha256(blob).hexdigest()
