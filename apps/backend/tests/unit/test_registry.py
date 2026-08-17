"""
Author: Sean Froning
Created Date: 6.3.2026
Unit tests for model registry helpers
"""

from datetime import datetime, timezone

from ml.models import LoadedModel
from ml.registry import _ModelRegistry


def _loaded(model_type: str, *, winner: bool = False, score: float = 0.5):
    return LoadedModel(
        type=model_type,
        score=score,
        rmse=1.0,
        trained_at=datetime.now(tz=timezone.utc),
        winner=winner,
        batch_id="batch-1",
    )


def test_resolve_winner_returns_flagged_model_type():
    metadata = {
        "linear": _loaded("linear", winner=False, score=0.6),
        "ridge": _loaded("ridge", winner=True, score=0.9),
    }
    assert _ModelRegistry._resolve_winner(metadata) == "ridge"


def test_resolve_winner_returns_none_when_unmarked():
    metadata = {
        "linear": _loaded("linear"),
        "ridge": _loaded("ridge"),
    }
    assert _ModelRegistry._resolve_winner(metadata) is None
