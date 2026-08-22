"""
Author: Sean Froning
Created Date: 8.22.2026
Unit tests for RefineShardWriter
"""

from decimal import Decimal
from unittest.mock import patch

import numpy as np
import pytest
from fiery_python import (
    DatasetVersion,
    TrainingDeformation,
    TrainingDeformationLabel,
    TrainingInterferogram,
    TrainingNormalize,
    TrainingSampleSource,
    TrainingSplit,
    TrainingStatus,
    TransformationRejected,
)
from integrations.refine.services.shard_manifest import RefineShardManifest
from integrations.refine.services.shard_writer import RefineShardWriter


def _deformation() -> TrainingDeformation:
    return TrainingDeformation(
        patch_px=2,
        wrap_rad=Decimal("3.141592653589793"),
        normalize=TrainingNormalize.NONE,
        coherence_min=Decimal("0.300"),
        class_id="class-1",
    )


def _interferogram(**overrides) -> TrainingInterferogram:
    payload = {
        "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "source": TrainingSampleSource.HEPHAESTUS,
        "split": TrainingSplit.TRAIN,
        "label": TrainingDeformationLabel.POSITIVE,
        "storage_path": "hephaestus/abc.npz",
    }
    payload.update(overrides)
    return TrainingInterferogram(**payload)


def _version() -> DatasetVersion:
    return DatasetVersion(
        id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        transform_hash="hash-1",
        manifest_path="contract-1/hash-1/manifest.json",
        shard_count=0,
        sample_count=0,
        status=TrainingStatus.PENDING,
        contract_id="contract-1",
    )


def test_transform_rejects_missing_identity():
    manifest = RefineShardManifest("contract-1", "hash-1", _deformation())
    interferogram = _interferogram(id=None, storage_path="")
    interferogram.id = None
    result = RefineShardWriter._transform_interferogram(
        interferogram, _deformation(), manifest
    )
    assert result is None
    assert manifest.rejected_count() == 1


def test_transform_records_rejected_and_returns_none():
    manifest = RefineShardManifest("contract-1", "hash-1", _deformation())
    interferogram = _interferogram()
    with (
        patch(
            "integrations.refine.services.shard_writer.BlobStorageServices.get_unrefined",
            return_value=b"npz",
        ),
        patch(
            "integrations.refine.services.shard_writer.RefinePersistService.load_npz",
            return_value=np.ones((2, 2, 2), dtype=np.float32),
        ),
        patch(
            "integrations.refine.services.shard_writer.Transformation.apply",
            side_effect=TransformationRejected("coherence below min"),
        ),
    ):
        result = RefineShardWriter._transform_interferogram(
            interferogram, _deformation(), manifest
        )
    assert result is None
    assert manifest.sample_count() == 0
    assert manifest.rejected_count() == 1


def test_transform_keeps_phase_and_label():
    manifest = RefineShardManifest("contract-1", "hash-1", _deformation())
    interferogram = _interferogram()
    phase = np.ones((2, 2), dtype=np.float32)
    with (
        patch(
            "integrations.refine.services.shard_writer.BlobStorageServices.get_unrefined",
            return_value=b"npz",
        ),
        patch(
            "integrations.refine.services.shard_writer.RefinePersistService.load_npz",
            return_value=np.ones((2, 2, 2), dtype=np.float32),
        ),
        patch(
            "integrations.refine.services.shard_writer.Transformation.apply",
            return_value=phase,
        ),
    ):
        key, out, label = RefineShardWriter._transform_interferogram(
            interferogram, _deformation(), manifest
        )
    assert key == interferogram.id
    np.testing.assert_array_equal(out, phase)
    assert label == {
        "label": TrainingDeformationLabel.POSITIVE.value,
        "split": TrainingSplit.TRAIN.value,
        "format_version": 1,
    }
    assert manifest.sample_count() == 1


def test_flush_shard_puts_tar_and_records():
    manifest = RefineShardManifest("contract-1", "hash-1", _deformation())
    phase = np.ones((2, 2), dtype=np.float32)
    buffer = [
        ("k1", phase, {"label": "positive", "split": "train", "format_version": 1})
    ]
    with (
        patch(
            "integrations.refine.services.shard_writer.Shard.write",
            return_value=b"tar-bytes",
        ) as write,
        patch(
            "integrations.refine.services.shard_writer.BlobStorageServices.put_shard",
            return_value="contract-1/hash-1/train-00000.tar",
        ) as put_shard,
    ):
        RefineShardWriter._flush_shard(
            "contract-1",
            "hash-1",
            TrainingSplit.TRAIN,
            0,
            buffer,
            manifest,
        )
    write.assert_called_once_with(buffer)
    put_shard.assert_called_once_with(
        "contract-1", "hash-1", TrainingSplit.TRAIN, 0, b"tar-bytes"
    )
    assert manifest.shard_count() == 1


def test_write_split_flushes_when_target_bytes_hit():
    interferograms = [
        _interferogram(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"),
        _interferogram(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2"),
    ]
    phase = np.ones((2, 2), dtype=np.float32)
    manifest = RefineShardManifest("contract-1", "hash-1", _deformation())
    with (
        patch(
            "integrations.refine.services.shard_writer.RefinePersistService.select_interferograms",
            return_value=interferograms,
        ),
        patch.object(
            RefineShardWriter,
            "_transform_interferogram",
            side_effect=[
                (interferograms[0].id, phase, {"label": "positive"}),
                (interferograms[1].id, phase, {"label": "positive"}),
            ],
        ),
        patch.object(RefineShardWriter, "_flush_shard") as flush,
        patch("integrations.refine.services.shard_writer._TARGET_SHARD_BYTES", 1),
    ):
        kept = RefineShardWriter._write_split(
            "contract-1",
            "hash-1",
            TrainingSplit.TRAIN,
            _deformation(),
            manifest,
        )
    assert kept == 2
    assert flush.call_count == 2


def test_run_upserts_completed_and_returns_count():
    deformation = _deformation()
    version = _version()
    with (
        patch(
            "integrations.refine.services.shard_writer.RefinePersistService.select_deformation",
            return_value=deformation,
        ),
        patch(
            "integrations.refine.services.shard_writer.Transformation.transform_hash",
            return_value="hash-1",
        ),
        patch(
            "integrations.refine.services.shard_writer.RefinePersistService.select_version",
            return_value=version,
        ),
        patch(
            "integrations.refine.services.shard_writer.RefinePersistService.upsert_version"
        ) as upsert_version,
        patch.object(RefineShardWriter, "_write_split", return_value=3),
        patch(
            "integrations.refine.services.shard_writer.BlobStorageServices.put_manifest",
            return_value="contract-1/hash-1/manifest.json",
        ),
    ):
        count = RefineShardWriter.run("contract-1", version.id)
    assert count == 3 * len(TrainingSplit)
    assert upsert_version.call_args_list[0].args[0].status is TrainingStatus.EXECUTING
    assert upsert_version.call_args_list[-1].args[0].status is TrainingStatus.COMPLETED
    assert upsert_version.call_args_list[-1].args[0].sample_count == 0


def test_run_marks_failed_and_reraises():
    deformation = _deformation()
    version = _version()
    with (
        patch(
            "integrations.refine.services.shard_writer.RefinePersistService.select_deformation",
            return_value=deformation,
        ),
        patch(
            "integrations.refine.services.shard_writer.Transformation.transform_hash",
            return_value="hash-1",
        ),
        patch(
            "integrations.refine.services.shard_writer.RefinePersistService.select_version",
            return_value=version,
        ),
        patch(
            "integrations.refine.services.shard_writer.RefinePersistService.upsert_version"
        ) as upsert_version,
        patch.object(
            RefineShardWriter, "_write_split", side_effect=RuntimeError("r2 down")
        ),
    ):
        with pytest.raises(RuntimeError, match="r2 down"):
            RefineShardWriter.run("contract-1", version.id)
    assert upsert_version.call_args_list[-1].args[0].status is TrainingStatus.FAILED
