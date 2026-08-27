"""
Author: Sean Froning
Created Date: 8.27.2026
Train corresponding model
"""

import torch.nn as nn
from torch.utils.data import DataLoader
from typing import Dict
from fiery_python import TrainingStage


def train_model(model: nn.Module, loaders: Dict[str, DataLoader], spec: dict) -> None:
    stage = spec["stage"]
    if not stage or not isinstance(stage, str):
        raise RuntimeError("Missing stage from spec")
    match stage:
        case TrainingStage.PRETRAIN.value:
            raise NotImplementedError("Unsupported stage from spec: pretrain")
        case TrainingStage.LORA.value:
            return _train_lora_model(model, loaders["train"], spec["lora"])
        case TrainingStage.DISTILL.value:
            raise NotImplementedError("Unsupported stage from spec: distill")
        case TrainingStage.PRUNE.value:
            raise NotImplementedError("Unsupported stage from spec: prune")
        case TrainingStage.QUANTIZE.value:
            raise NotImplementedError("Unsupported stage from spec: quantize")
        case _:
            raise RuntimeError(f"Invalid stage from spec: {stage}")


def _train_lora_model(model: nn.Module, loader: DataLoader, lora: dict) -> None:
    import torch

    device = next(model.parameters()).device
    model.train()
    optimizer = torch.optim.AdamW(
        (param for param in model.parameters() if param.requires_grad),
        lr=lora["learning_rate"],
    )
    loss_fn = nn.CrossEntropyLoss()
    for _ in range(lora["epochs"]):
        for images, targets in loader:
            images = images.to(device)
            targets = targets.to(device)
            optimizer.zero_grad()
            loss = loss_fn(model(images), targets)
            loss.backward()
            optimizer.step()
