"""
Author: Sean Froning
Created Date: 8.27.2026
Unit tests for trainer entrypoint
"""

from decimal import Decimal
from unittest.mock import patch

import torch
from torch import nn
from fiery_python import (
    ModelMetric,
    ModelMetricName,
    ModelRole,
    ModelTier,
    TrainingPrecision,
    TrainingSplit,
    TrainingStage,
)
from src.entrypoint import _seed, train_deformation


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
        patch("src.entrypoint.train_model"),
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
    assert result == {
        "ok": True,
        "spec": "sess-1",
        "storage_path": "unused",
    }


def test_train_deformation_skips_callback_when_train_fails():
    spec = _spec()
    with (
        patch(
            "src.entrypoint.build_loaders",
            side_effect=RuntimeError("Failed to load dataset"),
        ),
        patch("src.entrypoint.send_callback") as callback,
    ):
        result = train_deformation(spec)
    callback.assert_not_called()
    assert result == {
        "ok": False,
        "spec": "sess-1",
        "storage_path": "unused",
    }
