"""
Author: Sean Froning
Created Date: 8.21.2026
Unit tests for IngestOkadaSource
"""

from unittest.mock import patch

import numpy as np
import pytest
from fiery_python import (
    TrainingDeformationLabel,
    TrainingDeformationSource,
    TrainingInterferogram,
    TrainingSampleSource,
    TrainingStatus,
)
from integrations.ingest.services.okada_source import (
    IngestOkadaSource,
    _PATCH_PX,
)


def test_forward_phase_shape_and_coherence():
    phase, coherence = IngestOkadaSource._forward_phase(0.5)
    assert phase.shape == (_PATCH_PX, _PATCH_PX)
    assert coherence.shape == (_PATCH_PX, _PATCH_PX)
    assert np.all(coherence == 0.85)
    assert float(np.max(np.abs(phase))) <= np.pi + 1e-5


def test_forward_phase_zero_slip_is_flat():
    phase, _coherence = IngestOkadaSource._forward_phase(0.0)
    np.testing.assert_allclose(phase, 0.0, atol=1e-6)


def test_iter_samples_unique_sources_and_labels():
    samples = list(IngestOkadaSource._iter_samples())
    assert len(samples) == 10
    ids = {sample["source"].id for sample in samples}
    assert len(ids) == 10
    negatives = [
        sample
        for sample in samples
        if sample["label"] is TrainingDeformationLabel.NEGATIVE
    ]
    assert len(negatives) >= 1
    assert all(
        sample["source"].id == sample["source"].deterministic_id() for sample in samples
    )


def test_run_flushes_sources_before_interferograms():
    samples = list(IngestOkadaSource._iter_samples())[:2]
    order = []

    def _record_interferograms(rows):
        order.append(("interferograms", len(rows)))
        assert isinstance(rows[0], TrainingInterferogram)
        assert rows[0].deformation_source_id == samples[0]["source"].id

    def _record_sources(rows):
        order.append(("sources", len(rows)))
        assert isinstance(rows[0], TrainingDeformationSource)

    with (
        patch.object(IngestOkadaSource, "_iter_samples", return_value=samples),
        patch(
            "integrations.ingest.services.okada_source.IngestPersistService.upsert_ingest"
        ) as upsert_ingest,
        patch(
            "integrations.ingest.services.okada_source.IngestPersistService.upsert_deformation_sources",
            side_effect=_record_sources,
        ),
        patch(
            "integrations.ingest.services.okada_source.IngestPersistService.upsert_interferograms",
            side_effect=_record_interferograms,
        ),
        patch(
            "integrations.ingest.services.okada_source.IngestPersistService.npz_bytes",
            return_value=b"npz",
        ),
        patch(
            "integrations.ingest.services.okada_source.BlobStorageServices.put_unrefined",
            return_value="okada/abc.npz",
        ),
    ):
        count = IngestOkadaSource.run("ingest-okada")
    assert count == 2
    assert order == [("sources", 2), ("interferograms", 2)]
    assert upsert_ingest.call_args_list[-1].args[0].status == TrainingStatus.COMPLETED
    assert upsert_ingest.call_args_list[-1].args[0].source == TrainingSampleSource.OKADA


def test_run_marks_failed_and_reraises():
    with (
        patch.object(
            IngestOkadaSource, "_iter_samples", side_effect=RuntimeError("synth")
        ),
        patch(
            "integrations.ingest.services.okada_source.IngestPersistService.upsert_ingest"
        ) as upsert_ingest,
    ):
        with pytest.raises(RuntimeError, match="synth"):
            IngestOkadaSource.run("ingest-okada")
    assert upsert_ingest.call_args_list[-1].args[0].status == TrainingStatus.FAILED
