"""
Author: Sean Froning
Created Date: 8.27.2026
Unit tests for trainer scoring
"""

from decimal import Decimal
from unittest.mock import patch

import pytest
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from fiery_python import (
    ModelMetricName,
    ModelRole,
    ModelTier,
    TrainingStage,
    TrainingSplit,
    UuidUtils,
)
from src.score_model import (
    _screener_scores,
    _tune_screener_threshold,
    score_model,
)


class _ConstLogits(nn.Module):
    def __init__(self, positive_logit: float) -> None:
        super().__init__()
        self.bias = nn.Parameter(torch.zeros(1))
        self.positive_logit = positive_logit

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        batch = images.shape[0]
        logits = torch.zeros(batch, 2)
        logits[:, 1] = self.positive_logit
        return logits + self.bias


def _loader(labels: list[int]) -> DataLoader:
    images = torch.zeros(len(labels), 3, 8, 8)
    targets = torch.tensor(labels, dtype=torch.long)
    return DataLoader(TensorDataset(images, targets), batch_size=len(labels))


def _score_spec(**overrides) -> dict:
    data = {
        "session_id": "sess-1",
        "stage": TrainingStage.LORA.value,
        "tier": ModelTier.CLOUD.value,
        "role": ModelRole.SCREENER.value,
    }
    data.update(overrides)
    return data


def test_score_model_raises_when_session_missing():
    with pytest.raises(RuntimeError, match="Missing session_id from spec"):
        score_model({"session_id": None}, _ConstLogits(10.0), {})


def test_score_model_raises_when_slot_invalid():
    with pytest.raises(RuntimeError, match="Invalid \\(stage, tier, role\\)"):
        score_model(
            _score_spec(role=ModelRole.TEACHER.value),
            _ConstLogits(10.0),
            {},
        )


def test_score_model_rejects_unimplemented_slots():
    with pytest.raises(NotImplementedError, match="Unsupported"):
        score_model(
            _score_spec(
                stage=TrainingStage.PRETRAIN.value,
                role=ModelRole.TEACHER.value,
            ),
            _ConstLogits(10.0),
            {},
        )


def test_screener_scores_counts_abstain_as_miss():
    probs = torch.tensor([0.9, 0.1, 0.8])
    labels = torch.tensor([1, 1, 0])
    recall, abstention = _screener_scores(probs, labels, 0.5)
    assert recall == pytest.approx(0.5)
    assert abstention == pytest.approx(1 / 3)


def test_screener_scores_zero_recall_without_positives():
    probs = torch.tensor([0.2, 0.1])
    labels = torch.tensor([0, 0])
    recall, abstention = _screener_scores(probs, labels, 0.5)
    assert recall == 0.0
    assert abstention == pytest.approx(1.0)


def test_screener_scores_rejects_empty_split():
    with pytest.raises(RuntimeError, match="Empty split while scoring"):
        _screener_scores(torch.tensor([]), torch.tensor([]), 0.5)


def test_tune_screener_threshold_keeps_lowest_when_precision_already_holds():
    probs = torch.tensor([0.9, 0.9, 0.2])
    labels = torch.tensor([1, 1, 0])
    threshold = _tune_screener_threshold(probs, labels)
    recall, _abstention = _screener_scores(probs, labels, threshold)
    assert recall == pytest.approx(1.0)
    assert threshold == pytest.approx(0.50)


def test_tune_screener_threshold_raises_until_precision_floor():
    probs = torch.tensor([0.91, 0.91, 0.62])
    labels = torch.tensor([1, 1, 0])
    threshold = _tune_screener_threshold(probs, labels)
    assert threshold > 0.62
    recall, _abstention = _screener_scores(probs, labels, threshold)
    assert recall == pytest.approx(1.0)


def test_score_model_emits_recall_and_abstention_for_test_and_holdout():
    loaders = {
        TrainingSplit.VALIDATE.value: _loader([1, 0]),
        TrainingSplit.TEST.value: _loader([1, 1, 0]),
        TrainingSplit.HOLDOUT.value: _loader([1, 0]),
    }
    metrics = score_model(_score_spec(), _ConstLogits(10.0), loaders)
    artifact_id = UuidUtils.deterministic_uuid("sess-1")
    names = {(metric.name, metric.split) for metric in metrics}
    assert names == {
        (ModelMetricName.RECALL, TrainingSplit.TEST),
        (ModelMetricName.ABSTENTION_RATE, TrainingSplit.TEST),
        (ModelMetricName.RECALL, TrainingSplit.HOLDOUT),
        (ModelMetricName.ABSTENTION_RATE, TrainingSplit.HOLDOUT),
    }
    assert all(metric.artifact_id == artifact_id for metric in metrics)
    assert all(isinstance(metric.value, Decimal) for metric in metrics)


def test_score_model_requires_validate_loader():
    with pytest.raises(RuntimeError, match="Missing validate loader"):
        score_model(
            _score_spec(),
            _ConstLogits(10.0),
            {TrainingSplit.TEST.value: _loader([1])},
        )


def test_score_model_requires_test_or_holdout():
    with pytest.raises(RuntimeError, match="Missing test or holdout loader"):
        score_model(
            _score_spec(),
            _ConstLogits(10.0),
            {TrainingSplit.VALIDATE.value: _loader([1, 0])},
        )


def test_score_model_dispatches_screener():
    expected = [object()]
    with patch("src.score_model._score_screener_model", return_value=expected) as score:
        result = score_model(_score_spec(), _ConstLogits(1.0), {})
    assert result is expected
    score.assert_called_once()
    assert score.call_args[0][2] == UuidUtils.deterministic_uuid("sess-1")
