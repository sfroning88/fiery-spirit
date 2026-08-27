"""
Author: Sean Froning
Created Date: 8.27.2026
Main entrypoint for Fiery AI/ML API
"""

import sys
import torch.nn as nn
from torch.utils.data import DataLoader
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__)))

from fiery_python import logging
from fiery_python import ModelStorageServices
from .callback import send_callback
from .data import build_loaders
from .evaluate import score_model
from .model import build_job

# Setup structured logging
logging.setup_structured_logging()
logger = logging.get_logger(__name__)

_MAX_TRAINING_ATTEMPTS = 2


# Training deformation endpoint
def train_deformation(spec: Dict) -> Dict:
    storage_path = None
    signature = None
    param_count = None
    architecture = None
    metrics = None
    for attempt in range(_MAX_TRAINING_ATTEMPTS):
        try:
            seed = spec["seed"]
            if not seed or not isinstance(seed, int):
                raise RuntimeError("Missing seed from spec")
            _seed(seed)
            loaders = build_loaders(spec)
            if not loaders or "train" not in loaders:
                raise RuntimeError("Failed to load dataset")
            model = build_job(spec)
            if model is None:
                raise RuntimeError("Failed to build model")
            model = model.to("cuda")
            _train_lora_model(model, loaders["train"], spec["lora"])
            metrics = score_model(spec, model, loaders)
            if not metrics:
                raise RuntimeError("Failed to score metrics")
            architecture = "vit-small"
            storage_path = f"{spec["tier"]}/{spec["role"]}/{spec["session_id"]}.pkl"
            payload = {
                "model": model.cpu(),
                "spec": spec,
                "architecture": architecture,
            }
            ModelStorageServices.save(payload, storage_path)
            signature = ModelStorageServices.head_hmac(storage_path)
            param_count = sum(param.numel() for param in model.parameters())
            break
        except Exception as err:
            logger.warning(
                "train_deformation_failed",
                spec=spec["session_id"],
                attempt=attempt,
                error=str(err),
            )
    if storage_path and signature and architecture and param_count and metrics:
        send_callback(
            spec,
            storage_path=storage_path,
            signature=signature,
            param_count=param_count,
            architecture=architecture,
            metrics=metrics,
        )
    return {
        "ok": True,
        "spec": spec["session_id"],
        "storage_path": spec["storage_path"],
    }


def _seed(seed: int) -> None:
    import random
    import numpy as np
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


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
