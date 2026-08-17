"""
Author: Sean Froning
Created Date: 6.3.2026
Unit tests for snapshot function shuffling
"""

from unittest.mock import patch

from focus_python import TrainingFunction
from integrations.training.services.shuffle import ShuffleServices


@patch(
    "integrations.training.services.shuffle.PersistServices.seed_split_with_functions"
)
@patch("integrations.training.services.shuffle.PersistServices.fetch_property_ids")
def test_shuffle_assigns_every_property(mock_fetch, mock_seed):
    mock_fetch.return_value = [f"prop-{index}" for index in range(10)]

    result = ShuffleServices.shuffle_snapshot_functions(seed=42)

    assert result["seed"] == 42
    mock_seed.assert_called_once()
    assignments = mock_seed.call_args[0][0]
    assert len(assignments) == 10
    assert sum(result["counts"].values()) == 10
    assert all(isinstance(func, TrainingFunction) for func in assignments.values())
