"""
Author: Sean Froning
Created Date: 8.23.2026
Unit tests for TrainModalSpawn
"""

from unittest.mock import patch

import pytest
from fiery_python import (
    DatasetVersion,
    TrainingHyperparameterLora,
    TrainingSession,
    TrainingSignal,
    TrainingStage,
    TrainingStatus,
    TrainingTargetModules,
)
from fiery_python.fastapi.error import error as AppError
from integrations.train.services.modal_spawn import TrainModalSpawn


def _session(**overrides) -> TrainingSession:
    payload = {
        "id": "sess-1",
        "signal": TrainingSignal.DEFORMATION,
        "stage": TrainingStage.LORA,
        "status": TrainingStatus.PENDING,
        "samples": 10,
        "seed": 42,
        "hyperparameter_lora_id": "lora-1",
        "contract_id": "contract-1",
        "version_id": "ver-1",
    }
    payload.update(overrides)
    return TrainingSession(**payload)


def _version(**overrides) -> DatasetVersion:
    payload = {
        "id": "ver-1",
        "transform_hash": "abc",
        "manifest_path": "contract-1/abc/manifest.json",
        "shard_count": 2,
        "sample_count": 10,
        "status": TrainingStatus.COMPLETED,
        "contract_id": "contract-1",
    }
    payload.update(overrides)
    return DatasetVersion(**payload)


def _hyperparameters():
    lora = TrainingHyperparameterLora(id="lora-1", target_modules_id="mod-1")
    modules = TrainingTargetModules(id="mod-1")
    return lora, modules


def test_run_raises_when_session_missing():
    with patch(
        "integrations.train.services.modal_spawn.TrainPersistService.select_session",
        return_value=None,
    ):
        with pytest.raises(AppError, match="No Training Session"):
            TrainModalSpawn.run("sess-1")


def test_run_fails_when_version_not_ready():
    session = _session()
    with (
        patch(
            "integrations.train.services.modal_spawn.TrainPersistService.select_session",
            return_value=session,
        ),
        patch(
            "integrations.train.services.modal_spawn.TrainPersistService.select_version",
            return_value=_version(status=TrainingStatus.PENDING),
        ),
        patch(
            "integrations.train.services.modal_spawn.TrainPersistService.upsert_session"
        ) as upsert,
    ):
        with pytest.raises(AppError, match="No Dataset Version"):
            TrainModalSpawn.run("sess-1")
    assert upsert.call_args.args[0].status is TrainingStatus.FAILED


def test_run_fails_when_lora_missing():
    session = _session()
    with (
        patch(
            "integrations.train.services.modal_spawn.TrainPersistService.select_session",
            return_value=session,
        ),
        patch(
            "integrations.train.services.modal_spawn.TrainPersistService.select_version",
            return_value=_version(),
        ),
        patch(
            "integrations.train.services.modal_spawn.TrainPersistService.select_lora",
            return_value=None,
        ),
        patch(
            "integrations.train.services.modal_spawn.TrainPersistService.upsert_session"
        ) as upsert,
    ):
        with pytest.raises(AppError, match="No LoRA Hyperparameters"):
            TrainModalSpawn.run("sess-1")
    assert upsert.call_args.args[0].status is TrainingStatus.FAILED


def test_run_returns_modal_call_id():
    session = _session()
    spec = {"session_id": "sess-1"}
    with (
        patch(
            "integrations.train.services.modal_spawn.TrainPersistService.select_session",
            return_value=session,
        ),
        patch(
            "integrations.train.services.modal_spawn.TrainPersistService.select_version",
            return_value=_version(),
        ),
        patch(
            "integrations.train.services.modal_spawn.TrainPersistService.select_lora",
            return_value=_hyperparameters(),
        ),
        patch(
            "integrations.train.services.modal_spawn.TrainPersistService.upsert_session"
        ),
        patch(
            "integrations.train.services.modal_spawn.TrainJobSpec.build_lora_job_spec",
            return_value=spec,
        ),
        patch.object(
            TrainModalSpawn,
            "_spawn_modal_function",
            return_value=("call-1", None),
        ) as spawn,
    ):
        call_id = TrainModalSpawn.run("sess-1")
    assert call_id == "call-1"
    spawn.assert_called_once_with(spec)


def test_spawn_modal_function_handles_import_error():
    with patch.dict("sys.modules", {"modal": None}):
        call_id, message = TrainModalSpawn._spawn_modal_function({"session_id": "s"})
    assert call_id is None
    assert "import modal" in message
