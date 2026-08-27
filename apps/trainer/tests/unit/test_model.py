"""
Author: Sean Froning
Created Date: 8.27.2026
Unit tests for trainer model builders
"""

from unittest.mock import MagicMock, patch

import pytest
from fiery_python import TrainingStage
from src.model import _peft_targets, build_job


def _lora(**overrides) -> dict:
    data = {
        "rank": 8,
        "alpha": 16,
        "dropout": 0.1,
        "epochs": 1,
        "learning_rate": 1e-4,
        "target_modules": {
            "query": True,
            "key": False,
            "value": False,
            "output": True,
        },
    }
    data.update(overrides)
    return data


def test_build_job_raises_when_stage_missing():
    with pytest.raises(RuntimeError, match="Missing stage from spec"):
        build_job({"stage": None})


def test_build_job_raises_when_stage_invalid():
    with pytest.raises(RuntimeError, match="Invalid stage from spec"):
        build_job({"stage": "unknown"})


@pytest.mark.parametrize(
    "stage",
    [
        TrainingStage.PRETRAIN.value,
        TrainingStage.DISTILL.value,
        TrainingStage.PRUNE.value,
        TrainingStage.QUANTIZE.value,
    ],
)
def test_build_job_rejects_unimplemented_stages(stage: str):
    with pytest.raises(NotImplementedError, match="Unsupported stage from spec"):
        build_job({"stage": stage})


def test_peft_targets_maps_qkv_and_proj():
    assert _peft_targets(
        {"query": True, "key": False, "value": False, "output": True}
    ) == ["qkv", "proj"]


def test_peft_targets_empty_when_all_false():
    assert (
        _peft_targets({"query": False, "key": False, "value": False, "output": False})
        == []
    )


def test_build_lora_job_raises_when_targets_empty():
    with pytest.raises(RuntimeError, match="Empty LoRA target modules"):
        build_job(
            {
                "stage": TrainingStage.LORA.value,
                "lora": _lora(
                    target_modules={
                        "query": False,
                        "key": False,
                        "value": False,
                        "output": False,
                    }
                ),
            }
        )


def test_build_lora_job_wraps_timm_backbone():
    backbone = MagicMock(name="backbone")
    wrapped = MagicMock(name="peft")
    with (
        patch("timm.create_model", return_value=backbone) as create_model,
        patch("peft.get_peft_model", return_value=wrapped) as get_peft_model,
    ):
        result = build_job({"stage": TrainingStage.LORA.value, "lora": _lora()})
    assert result is wrapped
    create_model.assert_called_once_with(
        "vit_small_patch16_224",
        pretrained=True,
        num_classes=2,
    )
    get_peft_model.assert_called_once()
    config = get_peft_model.call_args[0][1]
    assert config.r == 8
    assert config.lora_alpha == 16
    assert set(config.target_modules) == {"qkv", "proj"}
