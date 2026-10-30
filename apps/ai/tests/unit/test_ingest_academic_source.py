"""
Author: Sean Froning
Created Date: 8.28.2026
Unit tests for IngestAcademicSource
"""

import json
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fiery_python import (
    TrainingSampleSource,
    TrainingLanguageLabel,
    TrainingSplit,
    TrainingStatus,
)
from integrations.ingest.services.academic_source import IngestAcademicSource

_PUBLISHED_AT = datetime(2015, 3, 3, tzinfo=timezone.utc)


def _academic_row(
    *,
    label="green",
    prompt="Summarize unrest.",
    reference="Mild degassing increased.",
    citation="SERNAGEOMIN bulletin",
    published_at="2015-03-03T00:00:00+00:00",
    chunk_index=0,
    volcano_id=None,
):
    row = {
        "prompt": prompt,
        "reference": reference,
        "label": label,
        "citation": citation,
        "published_at": published_at,
        "chunk_index": chunk_index,
    }
    if volcano_id is not None:
        row["volcano_id"] = volcano_id
    return row


class MagicIter:
    def __init__(self, rows):
        self._rows = rows
        self.taken = None

    def take(self, n):
        self.taken = n
        return self

    def __iter__(self):
        return iter(self._rows)


def test_passage_body_bytes_encodes_prompt_and_reference():
    body = IngestAcademicSource._passage_body_bytes("p", "r")
    assert json.loads(body.decode("utf-8")) == {"prompt": "p", "reference": "r"}


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"label": 0}, TrainingLanguageLabel.GREEN),
        ({"label": 1}, TrainingLanguageLabel.YELLOW),
        ({"label": 2}, TrainingLanguageLabel.ORANGE),
        ({"label": 3}, TrainingLanguageLabel.RED),
        ({"label": "green"}, TrainingLanguageLabel.GREEN),
        ({"label": "ORANGE"}, TrainingLanguageLabel.ORANGE),
        ({"label": 4}, None),
        ({"label": "unknown"}, None),
        ({}, None),
    ],
)
def test_label_from_event(payload, expected):
    assert IngestAcademicSource._label_from_event(payload) == expected


def test_published_at_from_event_parses_iso_string():
    got = IngestAcademicSource._published_at_from_event(
        {"published_at": "2015-03-03T00:00:00Z"}
    )
    assert got == _PUBLISHED_AT


def test_iter_samples_skips_bad_rows():
    rows_by_split = {
        "train": [
            _academic_row(label="green"),
            {},
            _academic_row(label="unknown"),
        ]
    }
    datasets = {}

    def load_dataset(*_args, **kwargs):
        fake = MagicIter(rows_by_split.get(kwargs["split"], []))
        datasets[kwargs["split"]] = fake
        return fake

    with (
        patch(
            "integrations.ingest.services.academic_source.load_dataset",
            side_effect=load_dataset,
        ),
        patch(
            "integrations.ingest.services.academic_source.HF_TOKEN",
            "test-token",
        ),
    ):
        samples = list(IngestAcademicSource._iter_samples(max_samples=3))
    assert datasets["train"].taken == 3
    assert len(samples) == 1
    assert samples[0]["label"] == TrainingLanguageLabel.GREEN
    assert samples[0]["split"] == TrainingSplit.TRAIN
    assert samples[0]["citation"] == "SERNAGEOMIN bulletin"
    assert samples[0]["chunk_index"] == 0
    assert samples[0]["published_at"] == _PUBLISHED_AT


def test_iter_samples_maps_hub_splits():
    rows_by_split = {
        "train": [_academic_row(label="green")],
        "validation": [_academic_row(label="yellow")],
        "test": [_academic_row(label="red")],
    }

    def load_dataset(*_args, **kwargs):
        return MagicIter(rows_by_split.get(kwargs["split"], []))

    with (
        patch(
            "integrations.ingest.services.academic_source.load_dataset",
            side_effect=load_dataset,
        ) as load_ds,
        patch(
            "integrations.ingest.services.academic_source.HF_TOKEN",
            "test-token",
        ),
    ):
        samples = list(IngestAcademicSource._iter_samples(max_samples=3))
    assert [call.kwargs["split"] for call in load_ds.call_args_list] == [
        "train",
        "validation",
        "test",
    ]
    assert [(row["split"], row["label"]) for row in samples] == [
        (TrainingSplit.TRAIN, TrainingLanguageLabel.GREEN),
        (TrainingSplit.VALIDATE, TrainingLanguageLabel.YELLOW),
        (TrainingSplit.TEST, TrainingLanguageLabel.RED),
    ]


def test_iter_samples_stops_after_max_samples():
    loaded = []

    def load_dataset(*_args, **kwargs):
        loaded.append(kwargs["split"])
        return MagicIter([_academic_row(label="green")])

    with (
        patch(
            "integrations.ingest.services.academic_source.load_dataset",
            side_effect=load_dataset,
        ),
        patch(
            "integrations.ingest.services.academic_source.HF_TOKEN",
            "test-token",
        ),
    ):
        samples = list(IngestAcademicSource._iter_samples(max_samples=1))
    assert loaded == ["train"]
    assert len(samples) == 1


def test_run_upserts_completed_and_returns_count():
    samples = [
        {
            "prompt": "Summarize unrest.",
            "reference": "Mild degassing increased.",
            "label": TrainingLanguageLabel.ORANGE,
            "split": TrainingSplit.TRAIN,
            "citation": "SERNAGEOMIN bulletin",
            "published_at": _PUBLISHED_AT,
            "chunk_index": 2,
            "volcano_id": "vol-1",
        }
    ]
    with (
        patch.object(IngestAcademicSource, "_iter_samples", return_value=samples),
        patch(
            "integrations.ingest.services.academic_source.IngestPersistService.upsert_ingest"
        ) as upsert_ingest,
        patch(
            "integrations.ingest.services.academic_source.IngestPersistService.upsert_passages"
        ) as upsert_passages,
        patch(
            "integrations.ingest.services.academic_source.BlobStorageServices.put_unrefined",
            return_value="academic/abc.npz",
        ) as put_unrefined,
    ):
        count = IngestAcademicSource.run("ingest-1", max_samples=1)
    assert count == 1
    assert upsert_ingest.call_args_list[0].args[0].status == TrainingStatus.EXECUTING
    assert upsert_ingest.call_args_list[-1].args[0].status == TrainingStatus.COMPLETED
    assert (
        upsert_ingest.call_args_list[-1].args[0].source == TrainingSampleSource.ACADEMIC
    )
    put_unrefined.assert_called_once()
    assert put_unrefined.call_args.args[0] == TrainingSampleSource.ACADEMIC
    rows = upsert_passages.call_args.args[0]
    assert rows[0].storage_path == "academic/abc.npz"
    assert rows[0].source == TrainingSampleSource.ACADEMIC
    assert rows[0].label == TrainingLanguageLabel.ORANGE
    assert rows[0].citation == "SERNAGEOMIN bulletin"
    assert rows[0].chunk_index == 2
    assert rows[0].volcano_id == "vol-1"


def test_run_marks_failed_and_reraises():
    with (
        patch.object(
            IngestAcademicSource,
            "_iter_samples",
            side_effect=RuntimeError("hf down"),
        ),
        patch(
            "integrations.ingest.services.academic_source.IngestPersistService.upsert_ingest"
        ) as upsert_ingest,
    ):
        with pytest.raises(RuntimeError, match="hf down"):
            IngestAcademicSource.run("ingest-1", max_samples=1)
    assert upsert_ingest.call_args_list[-1].args[0].status == TrainingStatus.FAILED


def test_run_passes_max_samples_through():
    with (
        patch.object(
            IngestAcademicSource, "_iter_samples", return_value=[]
        ) as iter_samples,
        patch(
            "integrations.ingest.services.academic_source.IngestPersistService.upsert_ingest"
        ),
    ):
        IngestAcademicSource.run("ingest-1", max_samples=1)
        IngestAcademicSource.run("ingest-1", max_samples=50)
    assert iter_samples.call_args_list[0].args == (1,)
    assert iter_samples.call_args_list[1].args == (50,)


def test_run_rejects_non_positive_max_samples():
    with pytest.raises(ValueError, match="max_samples must be positive"):
        IngestAcademicSource.run("ingest-1", max_samples=0)
    with pytest.raises(ValueError, match="max_samples must be positive"):
        IngestAcademicSource.run("ingest-1", max_samples=-1)
