"""
Author: Sean Froning
Created Date: 8.27.2026
Unit tests for trainer dataset loaders
"""

import json
from unittest.mock import patch

import numpy as np
import pytest
import torch
from fiery_python import TrainingDeformationLabel, TrainingStage, TrainingSplit
from src.build_loaders import (
    _BATCH_SIZE,
    _VIT_PX,
    _build_lora_loaders,
    _generator,
    _label_to_index,
    _load_split_tensors,
    _phase_to_tensor,
    build_loaders,
)


def test_build_loaders_raises_when_stage_missing():
    with pytest.raises(RuntimeError, match="Missing stage from spec"):
        build_loaders({"stage": None})


def test_build_loaders_raises_when_stage_invalid():
    with pytest.raises(RuntimeError, match="Invalid stage from spec"):
        build_loaders({"stage": "unknown"})


@pytest.mark.parametrize(
    "stage",
    [
        TrainingStage.PRETRAIN.value,
        TrainingStage.DISTILL.value,
        TrainingStage.PRUNE.value,
        TrainingStage.QUANTIZE.value,
    ],
)
def test_build_loaders_rejects_unimplemented_stages(stage: str):
    with pytest.raises(NotImplementedError, match="Unsupported stage from spec"):
        build_loaders({"stage": stage})


def test_label_to_index_maps_binary_labels():
    assert _label_to_index({"label": TrainingDeformationLabel.POSITIVE.value}) == 1
    assert _label_to_index({"label": TrainingDeformationLabel.NEGATIVE.value}) == 0
    assert _label_to_index({"label": TrainingDeformationLabel.UNCERTAIN.value}) is None


def test_phase_to_tensor_repeats_and_resizes():
    phase = np.ones((32, 32), dtype=np.float32)
    tensor = _phase_to_tensor(phase)
    assert tensor.shape == (3, _VIT_PX, _VIT_PX)
    assert torch.allclose(tensor[0], tensor[1])


def test_phase_to_tensor_rejects_non_hw():
    with pytest.raises(RuntimeError, match="Expected phase array"):
        _phase_to_tensor(np.ones((2, 8, 8), dtype=np.float32))


def test_generator_is_seeded():
    assert _generator(7).initial_seed() == 7


def test_load_split_tensors_skips_uncertain_and_missing_keys():
    phase = np.ones((_VIT_PX, _VIT_PX), dtype=np.float32)
    splits = {TrainingSplit.TRAIN.value: {"shards": [{"key": "train-00000.tar"}, {}]}}
    unpacked = [
        ("a", phase, {"label": TrainingDeformationLabel.POSITIVE.value}),
        ("b", phase, {"label": TrainingDeformationLabel.UNCERTAIN.value}),
        ("c", phase, {"label": TrainingDeformationLabel.NEGATIVE.value}),
    ]
    with (
        patch("fiery_python.BlobStorageServices.get_shard", return_value=b"tar"),
        patch("fiery_python.Shard.read", return_value=unpacked),
    ):
        images, targets = _load_split_tensors(splits, TrainingSplit.TRAIN)
    assert images.shape == (2, 3, _VIT_PX, _VIT_PX)
    assert targets.tolist() == [1, 0]


def test_load_split_tensors_empty_when_no_shards():
    images, targets = _load_split_tensors({}, TrainingSplit.TEST)
    assert images.shape[0] == 0
    assert targets.shape[0] == 0


def test_build_lora_loaders_caps_train_and_skips_empty_splits():
    phase = np.ones((_VIT_PX, _VIT_PX), dtype=np.float32)
    manifest = {
        "splits": {
            TrainingSplit.TRAIN.value: {"shards": [{"key": "train-00000.tar"}]},
            TrainingSplit.VALIDATE.value: {"shards": [{"key": "val-00000.tar"}]},
            TrainingSplit.TEST.value: {"shards": []},
            TrainingSplit.HOLDOUT.value: {"shards": []},
        }
    }
    unpacked = [
        ("a", phase, {"label": TrainingDeformationLabel.POSITIVE.value}),
        ("b", phase, {"label": TrainingDeformationLabel.NEGATIVE.value}),
        ("c", phase, {"label": TrainingDeformationLabel.POSITIVE.value}),
    ]
    spec = {
        "manifest_path": "contract/hash/manifest.json",
        "seed": 42,
        "samples": 2,
    }
    with (
        patch(
            "src.build_loaders.r2_s3.get_bytes",
            return_value=json.dumps(manifest).encode("utf-8"),
        ),
        patch("fiery_python.BlobStorageServices.get_shard", return_value=b"tar"),
        patch("fiery_python.Shard.read", return_value=unpacked),
    ):
        loaders = _build_lora_loaders(spec)
    assert set(loaders) == {
        TrainingSplit.TRAIN.value,
        TrainingSplit.VALIDATE.value,
    }
    train_images, train_targets = next(iter(loaders[TrainingSplit.TRAIN.value]))
    assert train_images.shape[0] == 2
    assert train_targets.shape[0] == 2
    assert loaders[TrainingSplit.TRAIN.value].batch_size == _BATCH_SIZE


def test_build_lora_loaders_raises_when_manifest_missing():
    with pytest.raises(RuntimeError, match="Missing manifest_path from spec"):
        _build_lora_loaders({"seed": 1, "manifest_path": None})


def test_build_lora_loaders_raises_when_train_empty():
    manifest = {"splits": {TrainingSplit.TRAIN.value: {"shards": []}}}
    with patch(
        "src.build_loaders.r2_s3.get_bytes",
        return_value=json.dumps(manifest).encode("utf-8"),
    ):
        with pytest.raises(RuntimeError, match="Empty train split"):
            _build_lora_loaders(
                {"manifest_path": "contract/hash/manifest.json", "seed": 1}
            )


def test_build_loaders_dispatches_lora():
    expected = {"train": object()}
    with patch("src.build_loaders._build_lora_loaders", return_value=expected) as build:
        result = build_loaders({"stage": TrainingStage.LORA.value})
    assert result is expected
    build.assert_called_once_with({"stage": TrainingStage.LORA.value})
