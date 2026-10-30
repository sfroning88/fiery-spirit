"""
Author: Sean Froning
Created Date: 8.29.2026
Build training dataset
"""

import json
import numpy as np
from torch import Generator, Tensor
from torch.utils.data import DataLoader, Dataset, Subset, TensorDataset
from transformers import AutoTokenizer
from typing import Dict, List, Optional, Tuple, assert_never
from fiery_python import r2_s3
from fiery_python import (
    TrainingStage,
    TrainingSignal,
    TrainingSplit,
    TrainingDeformationLabel,
    TrainingSeismicLabel,
    TrainingLanguageLabel,
)

_DEFORMATION_BATCH_SIZE = 16
_SEISMIC_BATCH_SIZE = 32
_LANGUAGE_BATCH_SIZE = 1
_VIT_PX = 224
_LABEL_INDEX = {
    TrainingSignal.DEFORMATION: {
        TrainingDeformationLabel.POSITIVE.value: 1,
        TrainingDeformationLabel.NEGATIVE.value: 0,
    },
    TrainingSignal.SEISMIC: {
        TrainingSeismicLabel.VT.value: 0,
        TrainingSeismicLabel.LP.value: 1,
        TrainingSeismicLabel.TR.value: 2,
        TrainingSeismicLabel.TC.value: 3,
    },
    TrainingSignal.LANGUAGE: {
        TrainingLanguageLabel.GREEN.value: 0,
        TrainingLanguageLabel.YELLOW.value: 1,
        TrainingLanguageLabel.ORANGE.value: 2,
        TrainingLanguageLabel.RED.value: 3,
    },
}
_DEFORMATION_EMPTY = (0, 3, _VIT_PX, _VIT_PX)
_SEISMIC_EMPTY = (0, 1, 0, 0)


class _PassageDataset(Dataset):

    def __init__(self, rows: List[dict], tokenizer) -> None:
        self.rows = rows
        self.tokenizer = tokenizer

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict:
        row = self.rows[index]
        prompt_ids = self.tokenizer(row["prompt"], add_special_tokens=False)[
            "input_ids"
        ]
        reference_ids = self.tokenizer(row["reference"], add_special_tokens=False)[
            "input_ids"
        ]
        eos = []
        if self.tokenizer.eos_token_id is not None:
            eos = [self.tokenizer.eos_token_id]
        return {
            "input_ids": prompt_ids + reference_ids + eos,
            "attention_mask": [1] * (len(prompt_ids) + len(reference_ids) + len(eos)),
            "labels": [-100] * len(prompt_ids) + reference_ids + eos,
        }


def build_loaders(spec: dict) -> Dict[str, DataLoader]:
    stage = spec["stage"]
    if not stage or not isinstance(stage, str):
        raise RuntimeError("Missing stage from spec")
    match stage:
        case TrainingStage.PRETRAIN.value:
            return _build_pretrain_loaders(spec)
        case TrainingStage.LORA_VISUAL.value:
            return _build_lora_visual_loaders(spec)
        case TrainingStage.LORA_LANGUAGE.value:
            return _build_lora_language_loaders(spec)
        case TrainingStage.DISTILL.value:
            return _build_distill_loaders(spec)
        case TrainingStage.PRUNE.value:
            return _build_prune_loaders(spec)
        case TrainingStage.QUANTIZE.value:
            return _build_quantize_loaders(spec)
        case _:
            raise RuntimeError(f"Invalid stage from spec: {stage}")


def _build_pretrain_loaders(spec: dict) -> Dict[str, DataLoader]:
    return _build_split_loaders(
        spec, batch_size=_nested_int(spec, "pretrain", "batch_size")
    )


def _build_lora_visual_loaders(spec: dict) -> Dict[str, DataLoader]:
    return _build_split_loaders(spec, batch_size=_DEFORMATION_BATCH_SIZE)


def _build_lora_language_loaders(spec: dict) -> Dict[str, DataLoader]:
    splits = _manifest_splits(spec)
    tokenizer = _language_tokenizer(spec)
    seed = spec["seed"]
    samples = spec.get("samples")
    loaders: Dict[str, DataLoader] = {}
    for split in TrainingSplit:
        rows = _load_split_passages(splits, split)
        if split is TrainingSplit.TRAIN and isinstance(samples, int) and samples > 0:
            rows = rows[:samples]
        if not rows:
            if split is TrainingSplit.TRAIN:
                raise RuntimeError("Empty train split")
            continue
        loaders[split.value] = DataLoader(
            _PassageDataset(rows, tokenizer),
            batch_size=_LANGUAGE_BATCH_SIZE,
            shuffle=split is TrainingSplit.TRAIN,
            generator=_generator(seed),
            collate_fn=lambda batch: _pad_passages(batch, tokenizer.pad_token_id),
            pin_memory=True,
            num_workers=0,
        )
    return loaders


def _build_distill_loaders(spec: dict) -> Dict[str, DataLoader]:
    return _build_split_loaders(
        spec, batch_size=_nested_int(spec, "distill", "batch_size")
    )


def _build_prune_loaders(spec: dict) -> Dict[str, DataLoader]:
    return _build_split_loaders(spec, batch_size=_SEISMIC_BATCH_SIZE)


def _build_quantize_loaders(spec: dict) -> Dict[str, DataLoader]:
    loaders = _build_split_loaders(spec, batch_size=_SEISMIC_BATCH_SIZE)
    loaders["calibrate"] = _calibrate_loader(loaders["train"], spec)
    return loaders


def _language_tokenizer(spec: dict) -> AutoTokenizer:
    base_model_id = spec.get("base_model_id")
    revision = spec.get("revision")
    if (
        not base_model_id
        or not revision
        or not isinstance(base_model_id, str)
        or not isinstance(revision, str)
    ):
        raise RuntimeError("Empty base_model_id and/or revision")
    tokenizer = AutoTokenizer.from_pretrained(base_model_id, revision=revision)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def _pad_passages(batch: List[dict], pad_token_id: int) -> Dict[str, Tensor]:
    import torch

    width = max(len(row["input_ids"]) for row in batch)
    input_ids = []
    attention_mask = []
    labels = []
    for row in batch:
        pad = width - len(row["input_ids"])
        input_ids.append(row["input_ids"] + [pad_token_id] * pad)
        attention_mask.append(row["attention_mask"] + [0] * pad)
        labels.append(row["labels"] + [-100] * pad)
    return {
        "input_ids": torch.tensor(input_ids, dtype=torch.long),
        "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
        "labels": torch.tensor(labels, dtype=torch.long),
    }


def _build_split_loaders(spec: dict, *, batch_size: int) -> Dict[str, DataLoader]:
    splits = _manifest_splits(spec)
    seed = spec["seed"]
    samples = spec.get("samples")
    signal = _signal(spec)
    loaders: Dict[str, DataLoader] = {}
    for split in TrainingSplit:
        features, targets = _load_split_tensors(splits, split, signal)
        if split is TrainingSplit.TRAIN and isinstance(samples, int) and samples > 0:
            features = features[:samples]
            targets = targets[:samples]
        if features.shape[0] == 0:
            if split is TrainingSplit.TRAIN:
                raise RuntimeError("Empty train split")
            continue
        loaders[split.value] = DataLoader(
            TensorDataset(features, targets),
            batch_size=batch_size,
            shuffle=split is TrainingSplit.TRAIN,
            generator=_generator(seed),
            pin_memory=True,
            num_workers=0,
        )
    return loaders


def _manifest_splits(spec: dict) -> dict:
    from fiery_python import STORAGE_SHARD_BUCKET_NAME

    manifest_path = spec["manifest_path"]
    if not manifest_path or not isinstance(manifest_path, str):
        raise RuntimeError("Missing manifest_path from spec")
    manifest = json.loads(r2_s3.get_bytes(STORAGE_SHARD_BUCKET_NAME, manifest_path))
    return manifest.get("splits") or {}


def _load_split_passages(splits: dict, split: TrainingSplit) -> List[dict]:
    from fiery_python import BlobStorageServices, Shard

    bucket = splits.get(split.value) or {}
    shards = bucket.get("shards") or []
    rows: List[dict] = []
    for shard in shards:
        key = shard.get("key")
        if not key:
            continue
        unpacked = Shard.read(BlobStorageServices.get_shard(key))
        for _sample_key, array, label in unpacked:
            row = _passage_payload_from_array(array)
            value = label.get("label")
            if value is not None:
                row["label"] = value
            rows.append(row)
    return rows


def _passage_payload_from_array(array: np.ndarray) -> dict:
    if array.dtype != np.uint8 or array.ndim != 1:
        raise RuntimeError("Expected passage uint8 vector")
    payload = json.loads(array.tobytes().decode("utf-8"))
    prompt = payload.get("prompt")
    reference = payload.get("reference")
    if not prompt or not reference:
        raise RuntimeError("Passage shard missing prompt or reference")
    return {"prompt": prompt, "reference": reference}


def _load_split_tensors(
    splits: dict, split: TrainingSplit, signal: TrainingSignal
) -> Tuple[Tensor, Tensor]:
    import torch
    from fiery_python import BlobStorageServices, Shard

    bucket = splits.get(split.value) or {}
    shards = bucket.get("shards") or []
    features = []
    targets = []
    for shard in shards:
        key = shard.get("key")
        if not key:
            continue
        unpacked = Shard.read(BlobStorageServices.get_shard(key))
        for _sample_key, array, label in unpacked:
            target = _label_to_index(label, signal)
            if target is None:
                continue
            features.append(_array_to_tensor(array, signal))
            targets.append(target)
    if not features:
        if signal is TrainingSignal.DEFORMATION:
            empty = _DEFORMATION_EMPTY
        elif signal is TrainingSignal.SEISMIC:
            empty = _SEISMIC_EMPTY
        else:
            assert_never(signal)
        return torch.empty(empty), torch.empty(0, dtype=torch.long)
    return torch.stack(features), torch.tensor(targets, dtype=torch.long)


def _array_to_tensor(array: np.ndarray, signal: TrainingSignal) -> Tensor:
    import torch
    import torch.nn.functional as F

    tensor = torch.from_numpy(np.ascontiguousarray(array)).float()
    if signal is TrainingSignal.DEFORMATION:
        if tensor.ndim != 2:
            raise RuntimeError("Expected phase array of shape (H, W)")
        tensor = tensor.unsqueeze(0).unsqueeze(0)
        if tensor.shape[-2] != _VIT_PX or tensor.shape[-1] != _VIT_PX:
            tensor = F.interpolate(
                tensor, size=(_VIT_PX, _VIT_PX), mode="bilinear", align_corners=False
            )
        return tensor.squeeze(0).repeat(3, 1, 1)
    if signal is TrainingSignal.SEISMIC:
        if tensor.ndim != 3 or tensor.shape[0] != 1:
            raise RuntimeError("Expected log-mel array of shape (1, M, F)")
        return tensor
    if signal is TrainingSignal.LANGUAGE:
        raise NotImplementedError("TODO")
    assert_never(signal)


def _label_to_index(label: dict, signal: TrainingSignal) -> Optional[int]:
    value = label.get("label")
    mapping = _LABEL_INDEX.get(signal)
    if mapping is None:
        return None
    return mapping.get(value)


def _calibrate_loader(train_loader: DataLoader, spec: dict) -> DataLoader:
    import torch

    dataset = train_loader.dataset
    requested = spec.get("quantize") or {}
    num_samples = requested.get("calibration_samples") or 100
    num_samples = min(int(num_samples), len(dataset))
    if num_samples <= 0:
        raise RuntimeError("Empty calibration split")
    generator = _generator(spec["seed"])
    indices = torch.randperm(len(dataset), generator=generator)[:num_samples].tolist()
    return DataLoader(
        Subset(dataset, indices),
        batch_size=train_loader.batch_size,
        shuffle=False,
        pin_memory=True,
        num_workers=0,
    )


def _signal(spec: dict) -> TrainingSignal:
    value = spec.get("signal")
    if value == TrainingSignal.DEFORMATION.value:
        return TrainingSignal.DEFORMATION
    if value == TrainingSignal.SEISMIC.value:
        return TrainingSignal.SEISMIC
    if value == TrainingSignal.LANGUAGE.value:
        return TrainingSignal.LANGUAGE
    raise RuntimeError("Missing signal from spec")


def _nested_int(spec: dict, block: str, field: str) -> int:
    payload = spec.get(block) or {}
    value = payload.get(field)
    if not isinstance(value, int) or value <= 0:
        raise RuntimeError(f"Missing {block}.{field} from spec")
    return value


def _generator(seed: int) -> Generator:
    import torch

    generator = torch.Generator()
    generator.manual_seed(seed)
    return generator
