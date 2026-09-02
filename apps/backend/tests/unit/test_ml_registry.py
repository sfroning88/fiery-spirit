"""
Author: Sean Froning
Created Date: 8.29.2026
Unit tests for the inference-side model registry cache
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
import importlib.util

import pytest
from fiery_python import ModelRole, ModelTier, TrainingPrecision, TrainingStage
from ml.models import LoadedModel
from ml.registry import (
    SeismicCnn,
    _ModelRegistry,
    _VIT_BASE_MODEL_ID,
    _VIT_REVISION,
    _VIT_SNAPSHOT,
    _VIT_WEIGHTS,
)

KEY = (ModelTier.CLOUD, ModelRole.SCREENER)
NOW = datetime.now(tz=timezone.utc)


def _artifact_row(**overrides):
    row = {
        "id": "art-1",
        "tier": ModelTier.CLOUD.value,
        "role": ModelRole.SCREENER.value,
        "stage": TrainingStage.LORA.value,
        "precision": TrainingPrecision.FP32.value,
        "architecture": _VIT_SNAPSHOT,
        "param_count": 22_100_000,
        "sparsity": "0.0",
        "storage_path": "cloud/screener/art-1.safetensors",
        "signature": "sig-art-1",
        "signed_at": NOW,
        "promoted": True,
        "promoted_at": NOW,
        "session_id": "session-1",
        "parent_id": None,
    }
    row.update(overrides)
    return row


def _loaded(artifact_id: str = "art-1") -> LoadedModel:
    return LoadedModel(
        artifact_id=artifact_id,
        tier=ModelTier.CLOUD,
        role=ModelRole.SCREENER,
        stage=TrainingStage.LORA,
        precision=TrainingPrecision.FP32,
        architecture=_VIT_SNAPSHOT,
        param_count=22_100_000,
        sparsity=Decimal("0.0"),
        storage_path="cloud/screener/art-1.safetensors",
        signature="sig-art-1",
        signed_at=NOW,
        promoted=True,
        promoted_at=NOW,
        session_id="session-1",
    )


def test_get_raises_when_slot_empty():
    registry = _ModelRegistry()

    with pytest.raises(RuntimeError, match="not loaded"):
        registry.get(KEY)


def test_get_metadata_returns_empty_when_slot_empty():
    registry = _ModelRegistry()

    assert registry.get_metadata(KEY) == {}


def test_is_ready_false_when_slot_empty():
    registry = _ModelRegistry()

    assert registry.is_ready(KEY) is False


def test_load_resets_slot_when_no_promoted_row():
    registry = _ModelRegistry()
    slot = registry._slot(KEY)
    slot.get().model = object()
    slot.get().artifact_id = "stale"

    with patch.object(registry, "_fetch_promoted_artifact", return_value=None):
        registry.load(KEY)

    assert registry.is_ready(KEY) is False
    assert registry.get_metadata(KEY) == {}


def test_load_resets_slot_when_row_has_no_id():
    registry = _ModelRegistry()
    slot = registry._slot(KEY)
    slot.get().model = object()
    slot.get().artifact_id = "stale"

    with patch.object(registry, "_fetch_promoted_artifact", return_value={"id": None}):
        registry.load(KEY)

    assert registry.is_ready(KEY) is False
    assert registry.get_metadata(KEY) == {}


def test_load_wraps_lookup_failure():
    registry = _ModelRegistry()

    with patch.object(
        registry, "_fetch_promoted_artifact", side_effect=RuntimeError("db down")
    ):
        with pytest.raises(RuntimeError, match="Model registry lookup failed"):
            registry.load(KEY)


def test_load_skips_when_already_current():
    registry = _ModelRegistry()
    slot = registry._slot(KEY)
    slot.get().model = object()
    slot.get().metadata = _loaded()
    slot.get().artifact_id = "art-1"

    with (
        patch.object(
            registry, "_fetch_promoted_artifact", return_value=_artifact_row()
        ),
        patch.object(registry, "_load_model_entry") as load_entry,
    ):
        registry.load(KEY)

    load_entry.assert_not_called()


def test_load_reloads_when_force_even_if_current():
    registry = _ModelRegistry()
    slot = registry._slot(KEY)
    slot.get().model = object()
    slot.get().metadata = _loaded()
    slot.get().artifact_id = "art-1"
    artifact = object()
    entry = _loaded()

    with (
        patch.object(
            registry, "_fetch_promoted_artifact", return_value=_artifact_row()
        ),
        patch.object(
            registry, "_load_model_entry", return_value=(entry, artifact)
        ) as load_entry,
    ):
        registry.load(KEY, force=True)

    load_entry.assert_called_once()
    assert registry.get(KEY) is artifact
    assert registry.get_metadata(KEY)["artifact_id"] == "art-1"
    assert registry.is_ready(KEY) is True


def test_load_keeps_empty_slot_when_artifact_fails_to_materialize():
    registry = _ModelRegistry()

    with (
        patch.object(
            registry, "_fetch_promoted_artifact", return_value=_artifact_row()
        ),
        patch.object(registry, "_load_model_entry", return_value=(None, None)),
    ):
        with pytest.raises(RuntimeError, match="failed to materialize"):
            registry.load(KEY)

    assert registry.is_ready(KEY) is False


def test_load_keeps_cached_when_artifact_fails_to_materialize():
    registry = _ModelRegistry()
    cached = object()
    slot = registry._slot(KEY)
    slot.get().model = cached
    slot.get().metadata = _loaded("stale")
    slot.get().artifact_id = "stale"

    with (
        patch.object(
            registry, "_fetch_promoted_artifact", return_value=_artifact_row()
        ),
        patch.object(registry, "_load_model_entry", return_value=(None, None)),
    ):
        with pytest.raises(RuntimeError, match="failed to materialize"):
            registry.load(KEY)

    assert registry.get(KEY) is cached
    assert registry.get_metadata(KEY)["artifact_id"] == "stale"


def test_load_caches_model_and_metadata():
    registry = _ModelRegistry()
    artifact = object()
    entry = _loaded()

    with (
        patch.object(
            registry, "_fetch_promoted_artifact", return_value=_artifact_row()
        ),
        patch.object(registry, "_load_model_entry", return_value=(entry, artifact)),
    ):
        registry.load(KEY)

    assert registry.get(KEY) is artifact
    metadata = registry.get_metadata(KEY)
    assert metadata["tier"] == ModelTier.CLOUD
    assert metadata["role"] == ModelRole.SCREENER
    assert metadata["architecture"] == _VIT_SNAPSHOT
    assert metadata["storage_path"] == "cloud/screener/art-1.safetensors"
    assert metadata["signature"] == "sig-art-1"
    assert metadata["promoted"] is True
    assert metadata["session_id"] == "session-1"


def test_reset_drops_all_cached_slots():
    registry = _ModelRegistry()
    other = (ModelTier.EDGE, ModelRole.STUDENT)
    registry._slot(KEY).get().model = object()
    registry._slot(other).get().model = object()

    registry.reset()

    assert registry.is_ready(KEY) is False
    assert registry.is_ready(other) is False


def test_load_model_entry_returns_none_without_storage_path():
    registry = _ModelRegistry()

    entry, artifact = registry._load_model_entry({"id": "art-1"}, "art-1")

    assert entry is None
    assert artifact is None


def test_load_model_entry_returns_none_when_storage_load_fails():
    registry = _ModelRegistry()

    with patch(
        "ml.registry.ModelStorageServices.load_artifact",
        side_effect=RuntimeError("s3 unavailable"),
    ):
        entry, artifact = registry._load_model_entry(_artifact_row(), "art-1")

    assert entry is None
    assert artifact is None


def test_load_model_entry_returns_none_when_materialize_fails():
    registry = _ModelRegistry()
    state_dict = {"weight": object()}
    sidecar = {"lora": {"rank": 8, "alpha": 16, "dropout": 0.1, "target_modules": {}}}

    with (
        patch(
            "ml.registry.ModelStorageServices.load_artifact",
            return_value=(state_dict, sidecar),
        ),
        patch.object(
            registry,
            "materialize",
            side_effect=RuntimeError("sidecar missing lora"),
        ),
    ):
        entry, artifact = registry._load_model_entry(_artifact_row(), "art-1")

    assert entry is None
    assert artifact is None


def test_load_model_entry_builds_loaded_model():
    registry = _ModelRegistry()
    artifact = MagicMock(name="weights")
    row = _artifact_row(parent_id="parent-9")
    state_dict = {"lora_A": object()}
    sidecar = {
        "architecture": _VIT_SNAPSHOT,
        "base_model_id": _VIT_BASE_MODEL_ID,
        "revision": _VIT_REVISION,
        "lora": {
            "rank": 8,
            "alpha": 16,
            "dropout": 0.1,
            "target_modules": {"query": True, "output": True},
        },
        "decision": {
            "threshold": 0.5,
            "abstention_band": "0.00000",
            "transform_hash": "a" * 64,
            "op_version": 1,
        },
    }

    with (
        patch(
            "ml.registry.ModelStorageServices.load_artifact",
            return_value=(state_dict, sidecar),
        ),
        patch.object(registry, "materialize", return_value=artifact),
        patch("ml.registry.set_peft_model_state_dict") as set_adapter,
    ):
        entry, loaded = registry._load_model_entry(row, "art-1")

    set_adapter.assert_called_once_with(artifact, state_dict)
    artifact.load_state_dict.assert_not_called()
    artifact.eval.assert_called_once()
    assert loaded is artifact
    assert entry is not None
    assert entry.artifact_id == "art-1"
    assert entry.parent_id == "parent-9"
    assert entry.param_count == 22_100_000
    assert entry.sparsity == Decimal("0.0")
    assert entry.storage_path == "cloud/screener/art-1.safetensors"
    assert entry.signature == "sig-art-1"
    assert entry.signed_at == NOW
    assert entry.promoted is True
    assert entry.session_id == "session-1"
    assert entry.preprocessing["threshold"] == 0.5


def test_materialize_vit_delegates_to_screener():
    sidecar = {
        "architecture": _VIT_SNAPSHOT,
        "lora": {
            "rank": 8,
            "alpha": 16,
            "dropout": 0.1,
            "target_modules": {"query": True},
        },
    }
    stub = MagicMock(name="vit")
    with patch.object(
        _ModelRegistry, "_materialize_screener", return_value=stub
    ) as screener:
        assert _ModelRegistry.materialize(sidecar) is stub
    screener.assert_called_once_with(sidecar)


def test_materialize_cnn_small_and_tiny():
    small = _ModelRegistry.materialize({"architecture": "cnn_small"})
    tiny = _ModelRegistry.materialize({"architecture": "cnn_tiny"})
    assert isinstance(small, SeismicCnn)
    assert isinstance(tiny, SeismicCnn)


def test_materialize_uses_spec_architecture_when_top_level_missing():
    sidecar = {"spec": {"architecture": "cnn_tiny"}}
    with patch.object(
        _ModelRegistry, "_materialize_cnn", return_value=MagicMock()
    ) as cnn:
        _ModelRegistry.materialize(sidecar)
    cnn.assert_called_once_with("cnn_tiny", sidecar)


def test_materialize_routes_quantize_sidecar_to_pt2e():
    sidecar = {
        "architecture": "cnn_tiny",
        "example_shape": [1, 1, 16, 16],
        "spec": {
            "stage": TrainingStage.QUANTIZE.value,
            "precision": TrainingPrecision.INT8.value,
            "quantize": {"method": "ptq"},
        },
    }
    stub = MagicMock(name="quantized")
    with patch.object(
        _ModelRegistry, "_materialize_quantized_cnn", return_value=stub
    ) as quantized:
        assert _ModelRegistry.materialize(sidecar) is stub
    quantized.assert_called_once_with("cnn_tiny", sidecar)


@pytest.mark.skipif(
    importlib.util.find_spec("torchao") is None, reason="torchao is not installed"
)
def test_materialize_quantized_cnn_rebuilds_pt2e_graph():
    sidecar = {
        "architecture": "cnn_tiny",
        "example_shape": [1, 1, 16, 16],
        "spec": {
            "stage": TrainingStage.QUANTIZE.value,
            "precision": TrainingPrecision.INT8.value,
            "quantize": {"method": "ptq"},
        },
    }
    converted = MagicMock(name="converted")
    exported = MagicMock(name="exported")
    exported.module.return_value = MagicMock(name="exported_module")
    prepared = MagicMock(name="prepared")
    with (
        patch("ml.registry.torch.export.export", return_value=exported) as export,
        patch("ml.registry.prepare_pt2e", return_value=prepared) as prepare,
        patch("ml.registry.convert_pt2e", return_value=converted) as convert,
        patch("ml.registry.allow_exported_model_train_eval") as allow_train_eval,
        patch("ml.registry.X86InductorQuantizer"),
        patch("ml.registry.get_default_x86_inductor_quantization_config"),
    ):
        result = _ModelRegistry.materialize(sidecar)
    assert result is converted
    export.assert_called_once()
    prepare.assert_called_once()
    convert.assert_called_once_with(prepared)
    allow_train_eval.assert_called_once_with(converted)


def test_materialize_quantized_cnn_requires_example_shape():
    sidecar = {
        "architecture": "cnn_tiny",
        "spec": {
            "stage": TrainingStage.QUANTIZE.value,
            "quantize": {"method": "ptq"},
        },
    }
    with pytest.raises(RuntimeError, match="sidecar missing example_shape"):
        _ModelRegistry.materialize(sidecar)


def test_materialize_unknown_architecture():
    with pytest.raises(RuntimeError, match="Unknown architecture"):
        _ModelRegistry.materialize({"architecture": "resnet18"})


def test_materialize_screener_requires_lora():
    with pytest.raises(RuntimeError, match="sidecar missing lora"):
        _ModelRegistry._materialize_screener({"architecture": _VIT_SNAPSHOT})


def test_materialize_screener_requires_target_modules():
    with pytest.raises(RuntimeError, match="Empty LoRA"):
        _ModelRegistry._materialize_screener(
            {
                "architecture": _VIT_SNAPSHOT,
                "lora": {
                    "rank": 8,
                    "alpha": 16,
                    "dropout": 0.1,
                    "target_modules": {},
                },
            }
        )


def test_materialize_screener_requires_base_pin():
    with pytest.raises(RuntimeError, match="Empty base_model_id"):
        _ModelRegistry._materialize_screener(
            {
                "architecture": _VIT_SNAPSHOT,
                "lora": {
                    "rank": 8,
                    "alpha": 16,
                    "dropout": 0.1,
                    "target_modules": {"query": True},
                },
            }
        )


def test_materialize_screener_wraps_pinned_backbone():
    backbone = MagicMock(name="backbone")
    wrapped = MagicMock(name="peft")
    sidecar = {
        "architecture": _VIT_SNAPSHOT,
        "base_model_id": _VIT_BASE_MODEL_ID,
        "revision": _VIT_REVISION,
        "lora": {
            "rank": 8,
            "alpha": 16,
            "dropout": 0.1,
            "target_modules": {"query": True, "output": True},
        },
    }
    with (
        patch(
            "ml.registry.hf_hub_download",
            return_value="/tmp/vit/model.safetensors",
        ) as download,
        patch("ml.registry.timm.create_model", return_value=backbone) as create_model,
        patch("ml.registry.get_peft_model", return_value=wrapped) as get_peft_model,
    ):
        result = _ModelRegistry._materialize_screener(sidecar)
    assert result is wrapped
    download.assert_called_once_with(
        repo_id=_VIT_BASE_MODEL_ID,
        filename=_VIT_WEIGHTS,
        revision=_VIT_REVISION,
    )
    create_model.assert_called_once_with(
        _VIT_SNAPSHOT,
        pretrained=True,
        num_classes=2,
    )
    config = get_peft_model.call_args[0][1]
    assert config.modules_to_save == ["head"]
    assert set(config.target_modules) == {"qkv", "proj"}
