"""
Author: Sean Froning
Created Date: 8.27.2026
Build training dataset
"""

import numpy as np
from torch import Generator, Tensor
from torch.utils.data import DataLoader, TensorDataset
from typing import Dict, Optional, Tuple
from fiery_python import r2_s3
from fiery_python import TrainingStage, TrainingSplit

_BATCH_SIZE = 16
_VIT_PX = 224


def build_loaders(spec: dict) -> Dict[str, DataLoader]:
    stage = spec["stage"]
    if not stage or not isinstance(stage, str):
        raise RuntimeError("Missing stage from spec")
    match stage:
        case TrainingStage.PRETRAIN.value:
            raise NotImplementedError("Unsupported stage from spec: pretrain")
        case TrainingStage.LORA.value:
            return _build_lora_loaders(spec)
        case TrainingStage.DISTILL.value:
            raise NotImplementedError("Unsupported stage from spec: distill")
        case TrainingStage.PRUNE.value:
            raise NotImplementedError("Unsupported stage from spec: prune")
        case TrainingStage.QUANTIZE.value:
            raise NotImplementedError("Unsupported stage from spec: quantize")
        case _:
            raise RuntimeError(f"Invalid stage from spec: {stage}")


def _build_lora_loaders(spec: dict) -> Dict[str, DataLoader]:
    import json
    from fiery_python import STORAGE_SHARD_BUCKET_NAME

    manifest_path = spec["manifest_path"]
    if not manifest_path or not isinstance(manifest_path, str):
        raise RuntimeError("Missing manifest_path from spec")
    manifest = json.loads(r2_s3.get_bytes(STORAGE_SHARD_BUCKET_NAME, manifest_path))
    splits = manifest.get("splits") or {}
    seed = spec["seed"]
    samples = spec.get("samples")
    loaders: Dict[str, DataLoader] = {}
    for split in TrainingSplit:
        images, targets = _load_split_tensors(splits, split)
        if split is TrainingSplit.TRAIN and isinstance(samples, int) and samples > 0:
            images = images[:samples]
            targets = targets[:samples]
        if images.shape[0] == 0:
            if split is TrainingSplit.TRAIN:
                raise RuntimeError("Empty train split")
            continue
        loaders[split.value] = DataLoader(
            TensorDataset(images, targets),
            batch_size=_BATCH_SIZE,
            shuffle=split is TrainingSplit.TRAIN,
            generator=_generator(seed),
        )
    return loaders


def _load_split_tensors(splits: dict, split: TrainingSplit) -> Tuple[Tensor, Tensor]:
    import torch
    from fiery_python import BlobStorageServices, Shard

    bucket = splits.get(split.value) or {}
    shards = bucket.get("shards") or []
    images = []
    targets = []
    for shard in shards:
        key = shard.get("key")
        if not key:
            continue
        unpacked = Shard.read(BlobStorageServices.get_shard(key))
        for _sample_key, phase, label in unpacked:
            target = _label_to_index(label)
            if target is None:
                continue
            images.append(_phase_to_tensor(phase))
            targets.append(target)
    if not images:
        empty = torch.empty(0, 3, _VIT_PX, _VIT_PX)
        return empty, torch.empty(0, dtype=torch.long)
    return torch.stack(images), torch.tensor(targets, dtype=torch.long)


def _phase_to_tensor(phase: np.ndarray) -> Tensor:
    import torch
    import torch.nn.functional as F

    tensor = torch.from_numpy(phase).float()
    if tensor.ndim != 2:
        raise RuntimeError("Expected phase array of shape (H, W)")
    tensor = tensor.unsqueeze(0).unsqueeze(0)
    if tensor.shape[-2] != _VIT_PX or tensor.shape[-1] != _VIT_PX:
        tensor = F.interpolate(
            tensor, size=(_VIT_PX, _VIT_PX), mode="bilinear", align_corners=False
        )
    return tensor.squeeze(0).repeat(3, 1, 1)


def _label_to_index(label: dict) -> Optional[int]:
    from fiery_python import TrainingDeformationLabel

    value = label.get("label")
    if value == TrainingDeformationLabel.POSITIVE.value:
        return 1
    if value == TrainingDeformationLabel.NEGATIVE.value:
        return 0
    return None


def _generator(seed: int) -> Generator:
    import torch

    generator = torch.Generator()
    generator.manual_seed(seed)
    return generator
