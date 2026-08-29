"""
Author: Sean Froning
Created Date: 8.29.2026
Main entrypoint for Fiery AI/ML API
"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__)))

from fiery_python import logging
from fiery_python import ModelStorageServices
from .build_loaders import build_loaders
from .build_job import DistillPair, build_job
from .train_model import train_model
from .score_model import score_model
from .send_callback import send_callback

# Setup structured logging
logging.setup_structured_logging()
logger = logging.get_logger(__name__)

_MAX_TRAINING_ATTEMPTS = 2


def entrypoint(spec: Dict, architecture: str) -> Dict:
    import torch

    storage_path = None
    signature = None
    param_count = None
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
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = model.to(device)
            model = train_model(model, loaders, spec)
            if model is None:
                raise RuntimeError("Failed to train model")
            metrics, decision = score_model(spec, model, loaders)
            if not metrics or not decision:
                raise RuntimeError("Failed to score model")
            if isinstance(model, DistillPair):
                architecture = (spec.get("distill") or {}).get(
                    "student_architecture"
                ) or architecture
                model = model.student
            cpu_model = model.cpu()
            sidecar = {
                "architecture": architecture,
                "spec": spec,
                "decision": decision,
            }
            if "lora" in spec:
                sidecar["lora"] = spec["lora"]
            ModelStorageServices.save_artifact(
                cpu_model.state_dict(), sidecar, storage_path
            )
            signature = ModelStorageServices.head_hmac(storage_path)
            param_count = sum(param.numel() for param in cpu_model.parameters())
            break
        except Exception as err:
            logger.warning(
                "lora_screener_failed",
                spec=spec["session_id"],
                attempt=attempt,
                error=str(err),
            )
    if storage_path and signature and param_count and metrics and decision:
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
