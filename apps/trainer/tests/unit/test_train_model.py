"""
Author: Sean Froning
Created Date: 8.27.2026
Unit tests for trainer training loop
"""

from unittest.mock import patch

import pytest
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from fiery_python import TrainingStage
from src.train_model import _train_lora_model, train_model


def _loader() -> DataLoader:
    images = torch.randn(2, 4)
    targets = torch.tensor([0, 1])
    return DataLoader(TensorDataset(images, targets), batch_size=2)


def test_train_model_raises_when_stage_missing():
    with pytest.raises(RuntimeError, match="Missing stage from spec"):
        train_model(nn.Linear(4, 2), {"train": _loader()}, {"stage": None})


def test_train_model_raises_when_stage_invalid():
    with pytest.raises(RuntimeError, match="Invalid stage from spec"):
        train_model(nn.Linear(4, 2), {"train": _loader()}, {"stage": "unknown"})


@pytest.mark.parametrize(
    "stage",
    [
        TrainingStage.PRETRAIN.value,
        TrainingStage.DISTILL.value,
        TrainingStage.PRUNE.value,
        TrainingStage.QUANTIZE.value,
    ],
)
def test_train_model_rejects_unimplemented_stages(stage: str):
    with pytest.raises(NotImplementedError, match="Unsupported stage from spec"):
        train_model(nn.Linear(4, 2), {"train": _loader()}, {"stage": stage})


def test_train_model_dispatches_lora():
    model = nn.Linear(4, 2)
    loaders = {"train": _loader()}
    spec = {
        "stage": TrainingStage.LORA.value,
        "lora": {"epochs": 1, "learning_rate": 1e-2},
    }
    with patch("src.train_model._train_lora_model") as train_lora:
        train_model(model, loaders, spec)
    train_lora.assert_called_once_with(model, loaders["train"], spec["lora"])


def test_train_lora_model_runs_one_step():
    model = nn.Linear(4, 2)
    loader = _loader()
    before = model.weight.detach().clone()
    _train_lora_model(model, loader, {"epochs": 1, "learning_rate": 1e-2})
    assert not torch.equal(before, model.weight.detach())
