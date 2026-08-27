"""
Author: Sean Froning
Created Date: 8.27.2026
Unit tests for trainer entrypoint
"""

from decimal import Decimal
from unittest.mock import patch

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from fiery_python import (
    ModelMetric,
    ModelMetricName,
    ModelRole,
    ModelTier,
    TrainingPrecision,
    TrainingSplit,
    TrainingStage,
)
from src.entrypoint import _seed, _train_lora_model, train_deformation


class _TinyModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.ones(2))

    def to(self, _device: str) -> "_TinyModel":
        return self

    def cpu(self) -> "_TinyModel":
        return self


def _metrics() -> list[ModelMetric]:
    return [
        ModelMetric(
            name=ModelMetricName.RECALL,
            split=TrainingSplit.TEST,
            value=Decimal("1.0"),
            artifact_id="art-1",
        )
    ]


def _spec(**overrides) -> dict:
    data = {
        "session_id": "sess-1",
        "stage": TrainingStage.LORA.value,
        "tier": ModelTier.CLOUD.value,
        "role": ModelRole.SCREENER.value,
        "precision": TrainingPrecision.FP32.value,
        "seed": 42,
        "lora": {"epochs": 1, "learning_rate": 1e-4},
        "callback_url": "https://ai.example/api/callback/train",
        "storage_path": "unused",
    }
    data.update(overrides)
    return data


def test_seed_sets_torch_rng():
    _seed(0)
    first = torch.rand(1)
    _seed(0)
    second = torch.rand(1)
    assert torch.equal(first, second)


def test_train_deformation_saves_then_callbacks():
    metrics = _metrics()
    model = _TinyModel()
    loaders = {"train": object()}
    with (
        patch("src.entrypoint.build_loaders", return_value=loaders),
        patch("src.entrypoint.build_job", return_value=model),
        patch("src.entrypoint._train_lora_model"),
        patch("src.entrypoint.score_model", return_value=metrics),
        patch("src.entrypoint.ModelStorageServices.save") as save,
        patch(
            "src.entrypoint.ModelStorageServices.head_hmac",
            return_value="b" * 64,
        ),
        patch("src.entrypoint.send_callback") as callback,
    ):
        result = train_deformation(_spec())
    save.assert_called_once()
    callback.assert_called_once()
    kwargs = callback.call_args.kwargs
    assert kwargs["storage_path"] == "cloud/screener/sess-1.pkl"
    assert kwargs["signature"] == "b" * 64
    assert kwargs["architecture"] == "vit-small"
    assert kwargs["metrics"] is metrics
    assert result["ok"] is True
    assert result["spec"] == "sess-1"


def test_train_deformation_skips_callback_when_train_fails():
    with (
        patch(
            "src.entrypoint.build_loaders",
            side_effect=RuntimeError("Failed to load dataset"),
        ),
        patch("src.entrypoint.send_callback") as callback,
    ):
        result = train_deformation(_spec())
    callback.assert_not_called()
    assert result["ok"] is True


def test_train_lora_model_runs_one_step():
    model = nn.Linear(4, 2)
    images = torch.randn(2, 4)
    targets = torch.tensor([0, 1])
    loader = DataLoader(TensorDataset(images, targets), batch_size=2)
    before = model.weight.detach().clone()
    _train_lora_model(model, loader, {"epochs": 1, "learning_rate": 1e-2})
    assert not torch.equal(before, model.weight.detach())
