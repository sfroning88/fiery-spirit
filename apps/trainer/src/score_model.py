"""
Author: Sean Froning
Created Date: 8.27.2026
Evaluate model performance
"""

import torch.nn as nn
from torch import Tensor, device
from torch.utils.data import DataLoader
from decimal import Decimal
from typing import List, Optional, Tuple
from fiery_python import (
    ModelTier,
    ModelRole,
    ModelMetricName,
    TrainingStage,
    TrainingSplit,
    ModelMetric,
    UuidUtils,
)

_SCREENER_MIN_PRECISION = 0.80


def score_model(
    spec: dict,
    model: nn.Module,
    loaders: dict[str, DataLoader],
) -> List[ModelMetric]:
    session_id = spec["session_id"]
    if not session_id or not isinstance(session_id, str):
        raise RuntimeError("Missing session_id from spec")
    artifact_id = UuidUtils.deterministic_uuid(session_id)
    stage = spec["stage"]
    tier = spec["tier"]
    role = spec["role"]
    if (
        not stage
        or not tier
        or not role
        or not isinstance(stage, str)
        or not isinstance(tier, str)
        or not isinstance(role, str)
    ):
        raise RuntimeError("Missing (stage, tier, role) from spec")
    match (stage, tier, role):
        case (
            TrainingStage.LORA.value,
            ModelTier.CLOUD.value,
            ModelRole.SCREENER.value,
        ):
            return _score_screener_model(model, loaders, artifact_id)
        case (
            TrainingStage.PRETRAIN.value,
            ModelTier.CLOUD.value,
            ModelRole.TEACHER.value,
        ):
            raise NotImplementedError(
                "Unsupported (stage, tier, spec) from spec: (pretrain, cloud, teacher)"
            )
        case (
            TrainingStage.DISTILL.value,
            ModelTier.EDGE.value,
            ModelRole.STUDENT.value,
        ):
            raise NotImplementedError(
                "Unsupported (stage, tier, spec) from spec: (distill, edge, student)"
            )
        case _:
            raise RuntimeError(
                f"Invalid (stage, tier, role) from spec: ({stage}, {tier}, {role})"
            )


def _score_screener_model(
    model: nn.Module,
    loaders: dict[str, DataLoader],
    artifact_id: str,
) -> List[ModelMetric]:
    device = next(model.parameters()).device
    model.eval()
    validate = loaders.get(TrainingSplit.VALIDATE.value)
    if not validate:
        raise RuntimeError("Missing validate loader")
    val_probs, val_labels = _collect_positive_probs(model, validate, device)
    threshold = _tune_screener_threshold(val_probs, val_labels)
    metrics: List[ModelMetric] = []
    for split in (TrainingSplit.TEST, TrainingSplit.HOLDOUT):
        loader = loaders.get(split.value)
        if not loader:
            continue
        probs, labels = _collect_positive_probs(model, loader, device)
        recall, abstention_rate = _screener_scores(probs, labels, threshold)
        metrics.extend(
            [
                ModelMetric(
                    name=ModelMetricName.RECALL,
                    split=split,
                    value=Decimal(str(round(recall, 6))),
                    artifact_id=artifact_id,
                ),
                ModelMetric(
                    name=ModelMetricName.ABSTENTION_RATE,
                    split=split,
                    value=Decimal(str(round(abstention_rate, 6))),
                    artifact_id=artifact_id,
                ),
            ]
        )
    if not metrics:
        raise RuntimeError("Missing test or holdout loader")
    return metrics


def _collect_positive_probs(
    model: nn.Module,
    loader: DataLoader,
    device: device,
) -> Tuple[Tensor, Tensor]:
    import torch

    probs = []
    labels = []
    with torch.no_grad():
        for images, targets in loader:
            logits = model(images.to(device))
            positive = torch.softmax(logits, dim=1)[:, 1]
            probs.append(positive.cpu())
            labels.append(targets.cpu())
    return torch.cat(probs), torch.cat(labels)


def _screener_scores(
    probs: Tensor, labels: Tensor, threshold: float
) -> Tuple[float, float]:
    predicted_positive = probs >= threshold
    num_labels = int(labels.numel())
    if num_labels == 0:
        raise RuntimeError("Empty split while scoring")
    abstention_rate = float((~predicted_positive).sum().item()) / num_labels
    positives = int((labels == 1).sum().item())
    if positives == 0:
        recall = 0.0
    else:
        true_positive = int(((labels == 1) & predicted_positive).sum().item())
        recall = true_positive / positives
    return recall, abstention_rate


def _committed_precision(probs: Tensor, labels: Tensor, threshold: float) -> float:
    predicted_positive = probs >= threshold
    predicted_count = int(predicted_positive.sum().item())
    if predicted_count == 0:
        return 0.0
    true_positive = int(((labels == 1) & predicted_positive).sum().item())
    return true_positive / predicted_count


def _tune_screener_threshold(probs: Tensor, labels: Tensor) -> float:
    import torch

    candidates = torch.linspace(0.50, 0.95, steps=10)
    feasible: Optional[Tuple[float, float, float]] = None
    fallback = (float("-inf"), float("-inf"), float("inf"), 0.50)
    for threshold in candidates:
        value = float(threshold)
        recall, abstention_rate = _screener_scores(probs, labels, value)
        precision = _committed_precision(probs, labels, value)
        if precision >= _SCREENER_MIN_PRECISION:
            candidate = (recall, abstention_rate, value)
            if (
                feasible is None
                or candidate[0] > feasible[0]
                or (candidate[0] == feasible[0] and candidate[1] < feasible[1])
            ):
                feasible = candidate
        ranked = (precision, recall, -abstention_rate, value)
        if ranked[:-1] > fallback[:-1]:
            fallback = ranked
    if feasible is not None:
        return feasible[2]
    return fallback[3]
