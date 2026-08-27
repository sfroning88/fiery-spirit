"""
Author: Sean Froning
Created Date: 8.27.2026
Build training frame
"""

import torch.nn as nn
from peft import PeftModel
from typing import List, Optional
from fiery_python import TrainingStage


def build_job(spec: dict) -> Optional[nn.Module]:
    stage = spec["stage"]
    if not stage or not isinstance(stage, str):
        raise RuntimeError("Missing stage from spec")
    match stage:
        case TrainingStage.PRETRAIN.value:
            raise NotImplementedError("Unsupported stage from spec: pretrain")
        case TrainingStage.LORA.value:
            return _build_lora_job(spec["lora"])
        case TrainingStage.DISTILL.value:
            raise NotImplementedError("Unsupported stage from spec: distill")
        case TrainingStage.PRUNE.value:
            raise NotImplementedError("Unsupported stage from spec: prune")
        case TrainingStage.QUANTIZE.value:
            raise NotImplementedError("Unsupported stage from spec: quantize")
        case _:
            raise RuntimeError(f"Invalid stage from spec: {stage}")


def _build_lora_job(lora: dict) -> Optional[PeftModel]:
    import timm
    from peft import LoraConfig, TaskType, get_peft_model

    targets = _peft_targets(lora["target_modules"])
    if not targets:
        raise RuntimeError("Empty LoRA target modules")
    backbone = timm.create_model(
        "vit_small_patch16_224",
        pretrained=True,
        num_classes=2,
    )
    config = LoraConfig(
        r=lora["rank"],
        lora_alpha=lora["alpha"],
        lora_dropout=lora["dropout"],
        target_modules=targets,
        bias="none",
        task_type=TaskType.FEATURE_EXTRACTION,
    )
    return get_peft_model(backbone, config)


def _peft_targets(target_modules: dict) -> List[str]:
    targets = []
    if (
        target_modules.get("query")
        or target_modules.get("key")
        or target_modules.get("value")
    ):
        targets.append("qkv")
    if target_modules.get("output"):
        targets.append("proj")
    return targets
