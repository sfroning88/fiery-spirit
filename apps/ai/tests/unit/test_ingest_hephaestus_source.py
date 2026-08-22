"""
Author: Sean Froning
Created Date: 8.21.2026
Unit tests for IngestHephaestusSource
"""

from unittest.mock import patch

import numpy as np
import pytest
from fiery_python import (
    TrainingDeformationLabel,
    TrainingSampleSource,
    TrainingSplit,
    TrainingStatus,
)
from integrations.ingest.services.hephaestus_source import IngestHephaestusSource


def test_cast_height_width_squeezes_leading_dims():
    stacked = np.arange(12, dtype=np.float32).reshape(1, 3, 4)
    out = IngestHephaestusSource._cast_height_width(stacked)
    assert out.shape == (3, 4)
    assert out.dtype == np.float32


def test_cast_height_width_rejects_vector():
    with pytest.raises(ValueError, match="expected \\(H, W\\)"):
        IngestHephaestusSource._cast_height_width(np.ones((8,), dtype=np.float32))


def test_channels_maps_insar_difference_to_phase():
    phase = np.full((2, 2), 0.3, dtype=np.float32)
    coherence = np.full((2, 2), 200.0, dtype=np.float32)
    sample = {"insar_difference": phase, "insar_coherence": coherence}
    got_phase, got_coherence = IngestHephaestusSource._channels_from_interferogram(
        sample
    )
    np.testing.assert_array_equal(got_phase, phase)
    np.testing.assert_allclose(got_coherence, coherence / 255.0)


def test_channels_returns_none_when_missing():
    assert IngestHephaestusSource._channels_from_interferogram({}) is None


def test_channels_returns_none_on_shape_mismatch():
    sample = {
        "insar_difference": np.ones((2, 2), dtype=np.float32),
        "insar_coherence": np.ones((3, 3), dtype=np.float32),
    }
    assert IngestHephaestusSource._channels_from_interferogram(sample) is None


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"label": ["Deformation"]}, TrainingDeformationLabel.POSITIVE),
        ({"label": ["Non_Deformation"]}, TrainingDeformationLabel.NEGATIVE),
        ({"label": ["Earthquake"]}, TrainingDeformationLabel.UNCERTAIN),
        ({"label": ["Deformation"], "corrupted": 1}, None),
        ({"json": {"label": "Non_Deformation"}}, TrainingDeformationLabel.NEGATIVE),
    ],
)
def test_label_interferogram(payload, expected):
    assert IngestHephaestusSource._label_interferogram(payload) == expected


def test_iter_samples_skips_bad_rows():
    good_phase = np.ones((2, 2), dtype=np.float32)
    good_coh = np.full((2, 2), 0.8, dtype=np.float32)
    rows = [
        {
            "insar_difference": good_phase,
            "insar_coherence": good_coh,
            "label": ["Deformation"],
            "frame_id": "f1",
        },
        {},
        {
            "insar_difference": good_phase,
            "insar_coherence": good_coh,
            "label": ["Deformation"],
            "corrupted": 1,
        },
    ]
    fake_dataset = MagicIter(rows)
    with (
        patch(
            "integrations.ingest.services.hephaestus_source.load_dataset",
            return_value=fake_dataset,
        ),
        patch(
            "integrations.ingest.services.hephaestus_source.HF_STREAM_TOKEN",
            "test-token",
        ),
    ):
        samples = list(IngestHephaestusSource._iter_samples(max_samples=3))
    assert fake_dataset.taken == 3
    assert len(samples) == 1
    assert len(samples) == 1
    assert samples[0]["label"] == TrainingDeformationLabel.POSITIVE
    assert samples[0]["frame_id"] == "f1"


def test_run_upserts_completed_and_returns_count():
    phase = np.ones((2, 2), dtype=np.float32)
    coherence = np.full((2, 2), 0.9, dtype=np.float32)
    samples = [
        {
            "phase": phase,
            "coherence": coherence,
            "split": TrainingSplit.TRAIN,
            "label": TrainingDeformationLabel.POSITIVE,
            "frame_id": "f1",
            "primary_at": None,
            "secondary_at": None,
            "coherence_mean": 0.9,
        }
    ]
    with (
        patch.object(IngestHephaestusSource, "_iter_samples", return_value=samples),
        patch(
            "integrations.ingest.services.hephaestus_source.IngestPersistService.upsert_ingest"
        ) as upsert_ingest,
        patch(
            "integrations.ingest.services.hephaestus_source.IngestPersistService.upsert_interferograms"
        ) as upsert_interferograms,
        patch(
            "integrations.ingest.services.hephaestus_source.IngestPersistService.npz_bytes",
            return_value=b"npz",
        ),
        patch(
            "integrations.ingest.services.hephaestus_source.BlobStorageServices.put_unrefined",
            return_value="hephaestus/abc.npz",
        ),
    ):
        count = IngestHephaestusSource.run("ingest-1", max_samples=1)
    assert count == 1
    assert upsert_ingest.call_args_list[0].args[0].status == TrainingStatus.EXECUTING
    assert upsert_ingest.call_args_list[-1].args[0].status == TrainingStatus.COMPLETED
    rows = upsert_interferograms.call_args.args[0]
    assert rows[0].storage_path == "hephaestus/abc.npz"
    assert rows[0].source == TrainingSampleSource.HEPHAESTUS


def test_run_marks_failed_and_reraises():
    with (
        patch.object(
            IngestHephaestusSource,
            "_iter_samples",
            side_effect=RuntimeError("hf down"),
        ),
        patch(
            "integrations.ingest.services.hephaestus_source.IngestPersistService.upsert_ingest"
        ) as upsert_ingest,
    ):
        with pytest.raises(RuntimeError, match="hf down"):
            IngestHephaestusSource.run("ingest-1", max_samples=1)
    assert upsert_ingest.call_args_list[-1].args[0].status == TrainingStatus.FAILED


def test_run_clamps_max_samples():
    with (
        patch.object(
            IngestHephaestusSource, "_iter_samples", return_value=[]
        ) as iter_samples,
        patch(
            "integrations.ingest.services.hephaestus_source.IngestPersistService.upsert_ingest"
        ),
    ):
        IngestHephaestusSource.run("ingest-1", max_samples=50)
    iter_samples.assert_called_once_with(5)


class MagicIter:
    def __init__(self, rows):
        self._rows = rows
        self.taken = None

    def take(self, n):
        self.taken = n
        return self

    def __iter__(self):
        return iter(self._rows)
