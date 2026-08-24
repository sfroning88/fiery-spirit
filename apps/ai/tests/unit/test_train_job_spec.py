"""
Author: Sean Froning
Created Date: 8.23.2026
Unit tests for TrainJobSpec
"""

import pytest
from fiery_python import (
    DatasetVersion,
    ModelRole,
    ModelTier,
    TrainingHyperparameterLora,
    TrainingPrecision,
    TrainingSession,
    TrainingSignal,
    TrainingStage,
    TrainingStatus,
    TrainingTargetModules,
)
from fiery_python.fastapi.error import error as AppError
from integrations.train.services.job_spec import TrainJobSpec


def _session() -> TrainingSession:
    return TrainingSession(
        id="sess-1",
        signal=TrainingSignal.DEFORMATION,
        stage=TrainingStage.LORA,
        status=TrainingStatus.PENDING,
        samples=10,
        seed=42,
        git_sha="abc123",
        contract_id="contract-1",
        version_id="ver-1",
    )


def _version() -> DatasetVersion:
    return DatasetVersion(
        id="ver-1",
        transform_hash="abc",
        manifest_path="contract-1/abc/manifest.json",
        shard_count=2,
        sample_count=10,
        status=TrainingStatus.COMPLETED,
        contract_id="contract-1",
    )


def _modules() -> TrainingTargetModules:
    return TrainingTargetModules(id="mod-1")


def _lora() -> TrainingHyperparameterLora:
    return TrainingHyperparameterLora(id="lora-1", target_modules_id="mod-1")


def test_build_lora_job_spec_payload(monkeypatch):
    monkeypatch.setattr(
        "integrations.train.services.job_spec.config.get_required",
        lambda _key: "https://ai.example",
    )
    spec = TrainJobSpec.build_lora_job_spec(
        _session(), _version(), _modules(), _lora(), "nonce-1"
    )
    assert spec["session_id"] == "sess-1"
    assert spec["signal"] == TrainingSignal.DEFORMATION.value
    assert spec["stage"] == TrainingStage.LORA.value
    assert spec["shard_prefix"] == "contract-1/abc/"
    assert spec["manifest_path"] == "contract-1/abc/manifest.json"
    assert spec["lora"]["id"] == "lora-1"
    assert spec["lora"]["target_modules"]["query"] is True
    assert spec["callback_url"] == "https://ai.example/api/callback/train"
    assert spec["nonce"] == "nonce-1"
    assert spec["tier"] == ModelTier.CLOUD.value
    assert spec["role"] == ModelRole.SCREENER.value
    assert spec["precision"] == TrainingPrecision.FP32.value


def test_build_lora_job_spec_requires_api_url(monkeypatch):
    monkeypatch.setattr(
        "integrations.train.services.job_spec.config.get_required",
        lambda _key: None,
    )
    with pytest.raises(AppError, match="AI_API_URL"):
        TrainJobSpec.build_lora_job_spec(
            _session(), _version(), _modules(), _lora(), "nonce-1"
        )
