"""
Author: Sean Froning
Created Date: 6.3.2026
Unit tests for training batch outcome resolution
"""

from focus_python import TrainingModel, TrainingStatus, TrainingType
from integrations.training.services.persist import PersistServices


def _model(model_type: TrainingType, status: TrainingStatus, score: float = 0.5):
    return TrainingModel(
        id=f"model-{model_type.value}",
        type=model_type,
        status=status,
        r2_score=score,
        batch_id="batch-1",
    )


def test_resolve_batch_outcome_failed_when_any_model_failed():
    models = [
        _model(TrainingType.LINEAR, TrainingStatus.COMPLETED),
        _model(TrainingType.RIDGE, TrainingStatus.FAILED),
    ]
    assert PersistServices._resolve_batch_outcome(models) == TrainingStatus.FAILED


def test_resolve_batch_outcome_executing_when_incomplete():
    models = [_model(TrainingType.LINEAR, TrainingStatus.COMPLETED)]
    assert PersistServices._resolve_batch_outcome(models) == TrainingStatus.EXECUTING


def test_resolve_batch_outcome_completed_when_all_types_done():
    models = [
        _model(model_type, TrainingStatus.COMPLETED) for model_type in TrainingType
    ]
    assert PersistServices._resolve_batch_outcome(models) == TrainingStatus.COMPLETED


def test_pick_winner_selects_highest_r2_score():
    models = [
        _model(TrainingType.LINEAR, TrainingStatus.COMPLETED, score=0.7),
        _model(TrainingType.RIDGE, TrainingStatus.COMPLETED, score=0.9),
        _model(TrainingType.FOREST, TrainingStatus.PENDING),
    ]
    winner = PersistServices._pick_winner(models)
    assert winner.type == TrainingType.RIDGE
