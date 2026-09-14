"""
Author: Sean Froning
Created Date: 9.14.2026
Unit tests for InferenceImageLoader
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

import numpy as np
import pytest
from fiery_python import error
from fiery_python import (
    TrainingDeformationLabel,
    TrainingSampleSource,
    TrainingSeismicLabel,
    TrainingSplit,
    TrainingInterferogram,
    TrainingSeismicEvent,
)
from integrations.inference.schemas import InferencePreviewRequest
from integrations.inference.services.image_loader import InferenceImageLoader

IFG_ID = "22222222-2222-2222-2222-222222222222"
EVT_ID = "33333333-3333-3333-3333-333333333333"
VOL_ID = "44444444-4444-4444-4444-444444444444"
NOW = datetime.now(timezone.utc)
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _deformation_request() -> InferencePreviewRequest:
    return InferencePreviewRequest(interferogram_id=IFG_ID)


def _seismic_request() -> InferencePreviewRequest:
    return InferencePreviewRequest(seismic_event_id=EVT_ID)


def _interferogram() -> TrainingInterferogram:
    return TrainingInterferogram(
        id=IFG_ID,
        source=TrainingSampleSource.HEPHAESTUS,
        split=TrainingSplit.HOLDOUT,
        label=TrainingDeformationLabel.POSITIVE,
        storage_path="hephaestus/abc.npz",
        volcano_id=VOL_ID,
    )


def _seismic_event() -> TrainingSeismicEvent:
    return TrainingSeismicEvent(
        id=EVT_ID,
        source=TrainingSampleSource.LLAIMA,
        split=TrainingSplit.HOLDOUT,
        label=TrainingSeismicLabel.LP,
        recorded_at=NOW,
        duration_s=Decimal("60.000"),
        sampling_hz=100,
        waveform_path="llaima/abc.npz",
        volcano_id=VOL_ID,
    )


def test_png_bytes_writes_png_header():
    sample = np.linspace(0, 1, 16, dtype=np.float32).reshape(2, 2, 4)
    png = InferenceImageLoader._interferogram_png_bytes(sample)
    assert png.startswith(PNG_MAGIC)


def test_png_bytes_accepts_waveform():
    sample = np.linspace(-1, 1, 8, dtype=np.float32)
    png = InferenceImageLoader._interferogram_png_bytes(sample)
    assert png.startswith(PNG_MAGIC)


def test_run_raises_when_sample_unselected():
    payload = InferencePreviewRequest()
    with pytest.raises(error, match="interferogram or seismic_event"):
        InferenceImageLoader.run(payload)


def test_run_raises_when_interferogram_missing():
    with patch(
        "integrations.inference.services.image_loader.InferencePersistService.select_interferogram",
        return_value=None,
    ):
        with pytest.raises(error, match="No image asset"):
            InferenceImageLoader.run(_deformation_request())


def test_run_raises_when_seismic_event_missing():
    with patch(
        "integrations.inference.services.image_loader.InferencePersistService.select_seismic_event",
        return_value=None,
    ):
        with pytest.raises(error, match="No image asset"):
            InferenceImageLoader.run(_seismic_request())


def test_run_returns_png_for_interferogram():
    sample = np.zeros((2, 4, 4), dtype=np.float32)
    sample[0, 0, 0] = 1.0
    with (
        patch(
            "integrations.inference.services.image_loader.InferencePersistService.select_interferogram",
            return_value=_interferogram(),
        ) as select_interferogram,
        patch(
            "integrations.inference.services.image_loader.BlobStorageServices.get_unrefined",
            return_value=b"npz",
        ) as get_unrefined,
        patch(
            "integrations.inference.services.image_loader.InferencePersistService.load_npz",
            return_value=sample,
        ) as load_npz,
    ):
        response = InferenceImageLoader.run(_deformation_request())
    select_interferogram.assert_called_once_with((IFG_ID, None))
    get_unrefined.assert_called_once_with("hephaestus/abc.npz")
    load_npz.assert_called_once_with(b"npz")
    assert response.media_type == "image/png"
    assert response.status_code == 200
    assert response.body.startswith(PNG_MAGIC)


def test_run_returns_png_for_seismic_event():
    sample = np.zeros(16, dtype=np.float32)
    sample[0] = 1.0
    with (
        patch(
            "integrations.inference.services.image_loader.InferencePersistService.select_seismic_event",
            return_value=_seismic_event(),
        ) as select_event,
        patch(
            "integrations.inference.services.image_loader.BlobStorageServices.get_unrefined",
            return_value=b"npz",
        ) as get_unrefined,
        patch(
            "integrations.inference.services.image_loader.InferencePersistService.load_npz",
            return_value=sample,
        ),
    ):
        response = InferenceImageLoader.run(_seismic_request())
    select_event.assert_called_once_with((EVT_ID, None))
    get_unrefined.assert_called_once_with("llaima/abc.npz")
    assert response.media_type == "image/png"
    assert response.body.startswith(PNG_MAGIC)
