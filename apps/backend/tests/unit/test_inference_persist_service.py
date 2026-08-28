"""
Author: Sean Froning
Created Date: 8.28.2026
Unit tests for InferencePersistService
"""

import io
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

import numpy as np
from fiery_python import (
    PoolFetch,
    InferenceDeformation,
    TrainingDeformationLabel,
    TrainingNormalize,
    TrainingSampleSource,
    TrainingSplit,
)
from integrations.inference.services.persist_service import InferencePersistService


def test_load_npz_reads_data_key():
    stack = np.stack(
        [np.ones((3, 3), dtype=np.float32), np.full((3, 3), 0.4, dtype=np.float32)]
    )
    buf = io.BytesIO()
    np.savez_compressed(buf, data=stack)
    loaded = InferencePersistService.load_npz(buf.getvalue())
    assert loaded.shape == (2, 3, 3)
    np.testing.assert_array_equal(loaded[0], stack[0])
    np.testing.assert_array_equal(loaded[1], stack[1])


def test_select_interferogram_returns_none_when_ids_missing():
    with patch("integrations.inference.services.persist_service.db_pool.run") as run:
        assert InferencePersistService.select_interferogram((None, None)) is None
    run.assert_not_called()


def test_select_interferogram_maps_row():
    row = {
        "id": "ifg-1",
        "source": TrainingSampleSource.HEPHAESTUS.value,
        "split": TrainingSplit.HOLDOUT.value,
        "label": TrainingDeformationLabel.POSITIVE.value,
        "frame_id": "f1",
        "primary_at": None,
        "secondary_at": None,
        "coherence_mean": "0.800",
        "is_augmented": False,
        "storage_path": "hephaestus/abc.npz",
        "deformation_source_id": None,
        "volcano_id": "vol-1",
    }
    with patch(
        "integrations.inference.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        interferogram = InferencePersistService.select_interferogram(("ifg-1", None))
    run.assert_called_once()
    assert run.call_args.args[1] == ("ifg-1", None)
    assert run.call_args.kwargs["fetch"] is PoolFetch.ONE
    assert interferogram.id == "ifg-1"
    assert interferogram.storage_path == "hephaestus/abc.npz"
    assert interferogram.volcano_id == "vol-1"
    assert interferogram.label is TrainingDeformationLabel.POSITIVE


def test_select_interferogram_returns_none_when_empty():
    with patch(
        "integrations.inference.services.persist_service.db_pool.run",
        return_value=None,
    ):
        assert InferencePersistService.select_interferogram(("ifg-1", None)) is None


def test_select_deformation_maps_row():
    row = {
        "id": "def-1",
        "patch_px": 8,
        "wrap_rad": "3.14159",
        "normalize": TrainingNormalize.NONE.value,
        "coherence_min": "0.300",
        "class_id": "class-1",
    }
    with patch(
        "integrations.inference.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        deformation = InferencePersistService.select_deformation("session-1")
    assert run.call_args.args[1] == ("session-1",)
    assert run.call_args.kwargs["fetch"] is PoolFetch.ONE
    assert deformation.id == "def-1"
    assert deformation.patch_px == 8
    assert deformation.normalize is TrainingNormalize.NONE
    assert deformation.class_id == "class-1"


def test_select_deformation_returns_none_when_empty():
    with patch(
        "integrations.inference.services.persist_service.db_pool.run",
        return_value=None,
    ):
        assert InferencePersistService.select_deformation("session-1") is None


def test_upsert_deformation_passes_storage_dict():
    deformation = InferenceDeformation(
        score=Decimal("0.90000"),
        label=TrainingDeformationLabel.POSITIVE,
        threshold_used=Decimal("0.50000"),
        abstention_band=Decimal("0.00000"),
        abstained=False,
        transform_hash="a" * 64,
        op_version=1,
        inferred_at=datetime.now(timezone.utc),
        artifact_id="11111111-1111-1111-1111-111111111111",
        interferogram_id="22222222-2222-2222-2222-222222222222",
    )
    with patch("integrations.inference.services.persist_service.db_pool.run") as run:
        InferencePersistService.upsert_deformation(deformation)
    run.assert_called_once()
    params = run.call_args.args[1]
    assert "id" not in params
    assert params["score"] == Decimal("0.90000")
    assert params["label"] == TrainingDeformationLabel.POSITIVE.value
    assert params["artifact_id"] == deformation.artifact_id
    assert params["interferogram_id"] == deformation.interferogram_id
