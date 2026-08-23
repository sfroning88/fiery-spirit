"""
Author: Sean Froning
Created Date: 8.22.2026
Unit tests for RefineShardManifest
"""

import json
from decimal import Decimal

from fiery_python import (
    TrainingDeformation,
    TrainingDeformationLabel,
    TrainingNormalize,
    TrainingSplit,
)
from integrations.refine.services.shard_manifest import RefineShardManifest


def _deformation() -> TrainingDeformation:
    return TrainingDeformation(
        patch_px=8,
        wrap_rad=Decimal("3.14159"),
        normalize=TrainingNormalize.NONE,
        coherence_min=Decimal("0.300"),
        class_id="class-1",
    )


def test_payload_starts_with_zero_counts():
    manifest = RefineShardManifest("contract-1", "hash-1", _deformation())
    payload = manifest.payload()
    assert payload["format_version"] == 1
    assert payload["contract_id"] == "contract-1"
    assert payload["transform_hash"] == "hash-1"
    assert payload["patch_px"] == 8
    assert payload["normalize"] == TrainingNormalize.NONE.value
    assert payload["sample_count"] == 0
    assert payload["rejected_count"] == 0
    assert payload["shard_count"] == 0
    assert set(payload["splits"].keys()) == {split.value for split in TrainingSplit}


def test_record_kept_and_reject_update_totals():
    manifest = RefineShardManifest("contract-1", "hash-1", _deformation())
    manifest.record_kept(TrainingSplit.TRAIN, TrainingDeformationLabel.POSITIVE)
    manifest.record_kept(TrainingSplit.TRAIN, TrainingDeformationLabel.NEGATIVE)
    manifest.record_reject(
        TrainingSplit.VALIDATE,
        TrainingDeformationLabel.UNCERTAIN,
        "coherence below min",
    )
    manifest.record_reject(TrainingSplit.VALIDATE, None, "missing_identity")
    assert manifest.sample_count() == 2
    assert manifest.rejected_count() == 2
    train = manifest.payload()["splits"]["train"]
    assert train["sample_count"] == 2
    assert train["label_counts"]["positive"] == 1
    assert train["label_counts"]["negative"] == 1
    validate = manifest.payload()["splits"]["validate"]
    assert validate["rejected_count"] == 2
    assert validate["rejected_label_counts"]["uncertain"] == 1
    assert validate["reject_reasons"]["coherence below min"] == 1
    assert validate["reject_reasons"]["missing_identity"] == 1


def test_record_shard_indexes_keys():
    manifest = RefineShardManifest("contract-1", "hash-1", _deformation())
    manifest.record_shard(
        TrainingSplit.TRAIN, "contract-1/hash-1/train-00000.tar", 4, 128
    )
    manifest.record_shard(TrainingSplit.TEST, "contract-1/hash-1/test-00000.tar", 1, 32)
    assert manifest.shard_count() == 2
    train_shards = manifest.payload()["splits"]["train"]["shards"]
    assert train_shards[0]["key"] == "contract-1/hash-1/train-00000.tar"
    assert train_shards[0]["sample_count"] == 4
    assert train_shards[0]["bytes"] == 128


def test_dumps_is_canonical_json_bytes():
    manifest = RefineShardManifest("contract-1", "hash-1", _deformation())
    manifest.record_kept(TrainingSplit.TRAIN, TrainingDeformationLabel.POSITIVE)
    body = manifest.dumps()
    restored = json.loads(body)
    assert restored["sample_count"] == 1
    assert body == json.dumps(restored, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
