"""
Author: Sean Froning
Created Date: 8.20.2026
Unit tests for the inference-side model registry cache
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fiery_python import ModelRole, ModelTier, TrainingPrecision, TrainingStage
from ml.models import LoadedModel
from ml.registry import _ModelRegistry

KEY = (ModelTier.CLOUD, ModelRole.SCREENER)


def _artifact_row(**overrides):
    row = {
        "id": "art-1",
        "storage_path": "models/cloud/screener/art-1.pt",
        "tier": ModelTier.CLOUD.value,
        "role": ModelRole.SCREENER.value,
        "stage": TrainingStage.LORA.value,
        "precision": TrainingPrecision.FP32.value,
        "architecture": "vit-small",
        "param_count": 22_000_000,
        "sparsity": "0.0",
        "promoted_at": datetime.now(tz=timezone.utc),
        "parent_id": None,
    }
    row.update(overrides)
    return row


def _loaded(artifact_id: str = "art-1") -> LoadedModel:
    return LoadedModel(
        tier=ModelTier.CLOUD,
        role=ModelRole.SCREENER,
        stage=TrainingStage.LORA,
        precision=TrainingPrecision.FP32,
        architecture="vit-small",
        param_count=22_000_000,
        sparsity=Decimal("0.0"),
        artifact_id=artifact_id,
        promoted_at=datetime.now(tz=timezone.utc),
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
    assert metadata["architecture"] == "vit-small"


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
        "ml.registry.ModelStorageServices.load",
        side_effect=RuntimeError("s3 unavailable"),
    ):
        entry, artifact = registry._load_model_entry(_artifact_row(), "art-1")

    assert entry is None
    assert artifact is None


def test_load_model_entry_returns_none_when_payload_missing_model():
    registry = _ModelRegistry()

    with patch("ml.registry.ModelStorageServices.load", return_value={}):
        entry, artifact = registry._load_model_entry(_artifact_row(), "art-1")

    assert entry is None
    assert artifact is None


def test_load_model_entry_builds_loaded_model():
    registry = _ModelRegistry()
    artifact = MagicMock(name="weights")
    row = _artifact_row(parent_id="parent-9")

    with patch(
        "ml.registry.ModelStorageServices.load",
        return_value={"model": artifact},
    ):
        entry, loaded = registry._load_model_entry(row, "art-1")

    assert loaded is artifact
    assert entry is not None
    assert entry.artifact_id == "art-1"
    assert entry.parent_id == "parent-9"
    assert entry.param_count == 22_000_000
    assert entry.sparsity == Decimal("0.0")
