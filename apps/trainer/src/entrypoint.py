"""
Author: Sean Froning
Created Date: 8.27.2026
Main entrypoint for Fiery AI/ML API
"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__)))

from fiery_python import logging
from fiery_python import ModelStorageServices
from .build_loaders import build_loaders
from .build_job import build_job
from .train_model import train_model
from .score_model import score_model
from .send_callback import send_callback

# Setup structured logging
logging.setup_structured_logging()
logger = logging.get_logger(__name__)

_MAX_TRAINING_ATTEMPTS = 2


def lora_screener(spec: Dict) -> Dict:
    storage_path = None
    signature = None
    param_count = None
    architecture = None
    metrics = None
    decision = None
    for attempt in range(_MAX_TRAINING_ATTEMPTS):
        try:
            seed = spec["seed"]
            if seed is None or not isinstance(seed, int):
                raise RuntimeError("Missing seed from spec")
            _seed(seed)
            storage_path = (
                f"{spec['tier']}/{spec['role']}/{spec['session_id']}.safetensors"
            )
            loaders = build_loaders(spec)
            if not loaders or "train" not in loaders:
                raise RuntimeError("Failed to build dataset")
            model = build_job(spec)
            if model is None:
                raise RuntimeError("Failed to build job")
            model = model.to("cuda")
            train_model(model, loaders, spec)
            metrics, decision = score_model(spec, model, loaders)
            if not metrics or not decision:
                raise RuntimeError("Failed to score model")
            architecture = "vit_small_patch16_224"
            cpu_model = model.cpu()
            sidecar = {
                "architecture": architecture,
                "spec": spec,
                "decision": decision,
                "lora": spec["lora"],
            }
            ModelStorageServices.save_artifact(
                cpu_model.state_dict(), sidecar, storage_path
            )
            signature = ModelStorageServices.head_hmac(storage_path)
            param_count = sum(param.numel() for param in model.parameters())
            break
        except Exception as err:
            logger.warning(
                "lora_screener_failed",
                spec=spec["session_id"],
                attempt=attempt,
                error=str(err),
            )
    if (
        storage_path
        and signature
        and architecture
        and param_count
        and metrics
        and decision
    ):
        send_callback(
            spec,
            storage_path=storage_path,
            signature=signature,
            param_count=param_count,
            architecture=architecture,
            metrics=metrics,
            decision=decision,
        )
        return {
            "ok": True,
            "spec": spec["session_id"],
            "storage_path": spec["storage_path"],
        }
    else:
        return {
            "ok": False,
            "spec": spec["session_id"],
        }


def _seed(seed: int) -> None:
    import random
    import numpy as np
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
