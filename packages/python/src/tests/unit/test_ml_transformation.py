"""
Author: Sean Froning
Created Date: 8.20.2026
Unit tests for Transformation interferogram preprocess
"""

from decimal import Decimal

import numpy as np
import pytest
from fiery_python import (
    TrainingDeformation,
    TrainingNormalize,
    Transformation,
    TransformationRejected,
)


def _params(
    *,
    patch_px: int = 4,
    wrap_rad: str = "3.141592653589793",
    normalize: TrainingNormalize = TrainingNormalize.NONE,
    coherence_min: str = "0.3",
    class_id: str = "class-1",
) -> TrainingDeformation:
    return TrainingDeformation(
        patch_px=patch_px,
        wrap_rad=Decimal(wrap_rad),
        normalize=normalize,
        coherence_min=Decimal(coherence_min),
        class_id=class_id,
    )


def _stack(phase: np.ndarray, coherence: np.ndarray) -> np.ndarray:
    return np.stack([phase, coherence]).astype(np.float32)


def test_apply_wraps_and_center_crops_with_none_normalize():
    phase = np.full((8, 8), 4.0, dtype=np.float32)
    coherence = np.ones((8, 8), dtype=np.float32)
    wrap_rad = np.pi
    out = Transformation.apply(_stack(phase, coherence), _params())

    expected = np.mod(4.0 + wrap_rad, 2.0 * wrap_rad) - wrap_rad
    assert out.shape == (4, 4)
    np.testing.assert_allclose(out, expected, rtol=1e-5)


def test_apply_rejects_wrong_rank_or_channel_count():
    params = _params()
    with pytest.raises(TransformationRejected, match="\\(2, H, W\\)"):
        Transformation.apply(np.zeros((8, 8), dtype=np.float32), params)
    with pytest.raises(TransformationRejected, match="\\(2, H, W\\)"):
        Transformation.apply(np.zeros((3, 8, 8), dtype=np.float32), params)


def test_apply_rejects_array_smaller_than_patch():
    phase = np.zeros((2, 2), dtype=np.float32)
    coherence = np.ones((2, 2), dtype=np.float32)
    with pytest.raises(TransformationRejected, match="patch_px"):
        Transformation.apply(_stack(phase, coherence), _params(patch_px=4))


def test_apply_rejects_low_coherence():
    phase = np.zeros((8, 8), dtype=np.float32)
    coherence = np.full((8, 8), 0.1, dtype=np.float32)
    with pytest.raises(TransformationRejected, match="coherence"):
        Transformation.apply(_stack(phase, coherence), _params())


def test_apply_minmax_scales_crop_to_unit_interval():
    phase = np.zeros((8, 8), dtype=np.float32)
    phase[2:6, 2:6] = np.array(
        [
            [0.0, 1.0, 2.0, 3.0],
            [0.0, 1.0, 2.0, 3.0],
            [0.0, 1.0, 2.0, 3.0],
            [0.0, 1.0, 2.0, 3.0],
        ],
        dtype=np.float32,
    )
    coherence = np.ones((8, 8), dtype=np.float32)
    out = Transformation.apply(
        _stack(phase, coherence),
        _params(wrap_rad="1000", normalize=TrainingNormalize.MINMAX),
    )
    assert float(out.min()) == pytest.approx(0.0)
    assert float(out.max()) == pytest.approx(1.0)


def test_transform_hash_is_stable_and_ignores_class_id():
    first = Transformation.transform_hash(_params(class_id="a"))
    second = Transformation.transform_hash(_params(class_id="b"))
    assert first == second
    assert len(first) == 64


def test_transform_hash_changes_when_patch_px_changes():
    assert Transformation.transform_hash(
        _params(patch_px=4)
    ) != Transformation.transform_hash(_params(patch_px=8))
