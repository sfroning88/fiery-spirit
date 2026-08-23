"""
Author: Sean Froning
Created Date: 8.23.2026
Unit tests for TrainPersistService
"""

from unittest.mock import patch

from fiery_python import (
    PoolFetch,
    TrainingHyperparameterLora,
    TrainingSession,
    TrainingSignal,
    TrainingStage,
    TrainingStatus,
    TrainingTargetModules,
)
from integrations.train.services.persist_service import TrainPersistService


def test_select_version_maps_row():
    row = {
        "transform_hash": "abc",
        "manifest_path": "contract-1/abc/manifest.json",
        "shard_count": 2,
        "sample_count": 10,
        "status": TrainingStatus.COMPLETED.value,
        "contract_id": "contract-1",
    }
    with patch(
        "integrations.train.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        version = TrainPersistService.select_version("ver-1")
    assert run.call_args.args[1] == ("ver-1",)
    assert run.call_args.kwargs["fetch"] is PoolFetch.ONE
    assert version.id == "ver-1"
    assert version.transform_hash == "abc"
    assert version.shard_count == 2
    assert version.status is TrainingStatus.COMPLETED
    assert version.contract_id == "contract-1"


def test_select_version_returns_none_when_empty():
    with patch(
        "integrations.train.services.persist_service.db_pool.run",
        return_value=None,
    ):
        assert TrainPersistService.select_version("ver-1") is None


def test_select_lora_maps_row():
    row = {
        "rank": 8,
        "alpha": 16,
        "dropout": 0.1,
        "epochs": 10,
        "learning_rate": 0.0003,
        "target_modules_id": "mod-1",
        "query": True,
        "key": False,
        "value": True,
        "output": False,
    }
    with patch(
        "integrations.train.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        lora, modules = TrainPersistService.select_lora("lora-1")
    assert run.call_args.args[1] == ("lora-1",)
    assert run.call_args.kwargs["fetch"] is PoolFetch.ONE
    assert lora.id == "lora-1"
    assert lora.rank == 8
    assert lora.target_modules_id == "mod-1"
    assert modules.id == "mod-1"
    assert modules.query is True
    assert modules.key is False


def test_select_lora_returns_none_when_empty():
    with patch(
        "integrations.train.services.persist_service.db_pool.run",
        return_value=None,
    ):
        assert TrainPersistService.select_lora("lora-1") is None


def test_select_session_maps_row():
    row = {
        "signal": TrainingSignal.DEFORMATION.value,
        "stage": TrainingStage.LORA.value,
        "status": TrainingStatus.PENDING.value,
        "samples": 10,
        "seed": 42,
        "git_sha": "abc123",
        "git_url": None,
        "started_at": None,
        "finished_at": None,
        "error_message": None,
        "hyperparameter_pretrain_id": None,
        "hyperparameter_lora_id": "lora-1",
        "hyperparameter_distill_id": None,
        "hyperparameter_prune_id": None,
        "hyperparameter_quantize_id": None,
        "contract_id": "contract-1",
        "version_id": "ver-1",
    }
    with patch(
        "integrations.train.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        session = TrainPersistService.select_session("sess-1")
    assert run.call_args.args[1] == ("sess-1",)
    assert session.id == "sess-1"
    assert session.signal is TrainingSignal.DEFORMATION
    assert session.stage is TrainingStage.LORA
    assert session.status is TrainingStatus.PENDING
    assert session.hyperparameter_lora_id == "lora-1"
    assert session.version_id == "ver-1"


def test_select_session_returns_none_when_empty():
    with patch(
        "integrations.train.services.persist_service.db_pool.run",
        return_value=None,
    ):
        assert TrainPersistService.select_session("sess-1") is None


def test_upsert_lora_runs_modules_then_lora():
    modules = TrainingTargetModules()
    lora = TrainingHyperparameterLora(target_modules_id=modules.deterministic_id())
    with patch("integrations.train.services.persist_service.db_pool.run") as run:
        TrainPersistService.upsert_lora(lora, modules)
    assert run.call_count == 2
    assert run.call_args_list[0].args[1]["query"] is True
    assert run.call_args_list[1].args[1]["rank"] == 8
    assert run.call_args_list[1].args[1]["target_modules_id"] == modules.id


def test_upsert_session_passes_storage_dict():
    session = TrainingSession(
        id="11111111-1111-1111-1111-111111111111",
        signal=TrainingSignal.DEFORMATION,
        stage=TrainingStage.LORA,
        status=TrainingStatus.PENDING,
        samples=10,
        seed=42,
        contract_id="22222222-2222-2222-2222-222222222222",
        version_id="33333333-3333-3333-3333-333333333333",
    )
    with patch("integrations.train.services.persist_service.db_pool.run") as run:
        TrainPersistService.upsert_session(session)
    run.assert_called_once()
    params = run.call_args.args[1]
    assert params["id"] == session.id
    assert params["signal"] == TrainingSignal.DEFORMATION.value
    assert params["stage"] == TrainingStage.LORA.value
    assert params["status"] == TrainingStatus.PENDING.value
    assert params["contract_id"] == session.contract_id
