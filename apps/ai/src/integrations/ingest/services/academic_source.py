"""
Author: Sean Froning
Created Date: 10.30.2026
Processing functions for Academic source
"""

import json
from datasets import load_dataset
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional
from fiery_python import config, error
from fiery_python import (
    TRAINING_DB_PAGE_SIZE,
    TrainingSplit,
    TrainingStatus,
    TrainingSampleSource,
    TrainingLanguageLabel,
    DatasetIngest,
    TrainingPassage,
    BlobStorageServices,
)
from .persist_service import IngestPersistService

HF_TOKEN = config.get("HF_TOKEN")

_HF_ID = "sfroning88/Academic"
_HF_REVISION = "academic-revision-unpinned"
_HF_SPLIT_MAP = (
    ("train", TrainingSplit.TRAIN),
    ("validation", TrainingSplit.VALIDATE),
    ("test", TrainingSplit.TEST),
)
_LABEL_NAMES = (
    TrainingLanguageLabel.GREEN,
    TrainingLanguageLabel.YELLOW,
    TrainingLanguageLabel.ORANGE,
    TrainingLanguageLabel.RED,
)
_LABEL_BY_VALUE = {label.value: label for label in _LABEL_NAMES}


class IngestAcademicSource:
    """Stream Academic passages to unrefined R2 and catalog training passages"""

    @classmethod
    def run(cls, ingest_id: str, max_samples: int = 5) -> int:
        """Download dataset, store unrefined samples, upsert passages; return asset_count"""
        if max_samples <= 0:
            raise ValueError("max_samples must be positive")
        started_at = datetime.now(timezone.utc)
        IngestPersistService.upsert_ingest(
            DatasetIngest(
                id=ingest_id,
                source=TrainingSampleSource.ACADEMIC,
                asset_count=0,
                status=TrainingStatus.EXECUTING,
                started_at=started_at,
            )
        )
        page: List[TrainingPassage] = []
        asset_count = 0
        try:
            for sample in cls._iter_samples(max_samples):
                body = cls._passage_body_bytes(sample["prompt"], sample["reference"])
                storage_path = BlobStorageServices.put_unrefined(
                    TrainingSampleSource.ACADEMIC, body
                )
                passage = TrainingPassage(
                    source=TrainingSampleSource.ACADEMIC,
                    split=sample.get("split", TrainingSplit.TRAIN),
                    label=sample.get("label", TrainingLanguageLabel.GREEN),
                    citation=sample.get("citation"),
                    published_at=sample.get("published_at"),
                    chunk_index=sample.get("chunk_index"),
                    storage_path=storage_path,
                    volcano_id=sample.get("volcano_id"),
                )
                page.append(passage)
                asset_count += 1
                if len(page) >= TRAINING_DB_PAGE_SIZE:
                    IngestPersistService.upsert_passages(page)
                    page.clear()
                if asset_count >= max_samples:
                    break
            if page:
                IngestPersistService.upsert_passages(page)
            finished_at = datetime.now(timezone.utc)
            IngestPersistService.upsert_ingest(
                DatasetIngest(
                    id=ingest_id,
                    source=TrainingSampleSource.ACADEMIC,
                    asset_count=asset_count,
                    status=TrainingStatus.COMPLETED,
                    started_at=started_at,
                    finished_at=finished_at,
                    error_message=None,
                )
            )
            return asset_count
        except Exception as err:
            finished_at = datetime.now(timezone.utc)
            IngestPersistService.upsert_ingest(
                DatasetIngest(
                    id=ingest_id,
                    source=TrainingSampleSource.ACADEMIC,
                    asset_count=asset_count,
                    status=TrainingStatus.FAILED,
                    started_at=started_at,
                    finished_at=finished_at,
                    error_message=str(err),
                )
            )
            raise

    @staticmethod
    def _passage_body_bytes(prompt: str, reference: str) -> bytes:
        payload = {"prompt": prompt, "reference": reference}
        return json.dumps(payload, ensure_ascii=False).encode("utf-8")

    @staticmethod
    def _label_from_event(row: Any) -> Optional[TrainingLanguageLabel]:
        if not isinstance(row, dict):
            return None
        raw = row.get("label")
        if isinstance(raw, int) and 0 <= raw < len(_LABEL_NAMES):
            return _LABEL_NAMES[raw]
        if isinstance(raw, str):
            return _LABEL_BY_VALUE.get(raw.lower())
        return None

    @staticmethod
    def _published_at_from_event(row: Any) -> Optional[datetime]:
        if not isinstance(row, dict):
            return None
        raw = row.get("published_at")
        if isinstance(raw, datetime):
            if raw.tzinfo is None:
                return raw.replace(tzinfo=timezone.utc)
            return raw
        if isinstance(raw, str) and raw:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        return None

    @staticmethod
    def _citation_from_event(row: Any) -> Optional[str]:
        if not isinstance(row, dict):
            return None
        raw = row.get("citation")
        if isinstance(raw, str) and raw:
            return raw
        return None

    @staticmethod
    def _chunk_index_from_event(row: Any) -> Optional[int]:
        if not isinstance(row, dict):
            return None
        raw = row.get("chunk_index")
        if isinstance(raw, bool):
            return None
        if isinstance(raw, int):
            return raw
        return None

    @staticmethod
    def _text_from_event(row: Any, key: str) -> Optional[str]:
        if not isinstance(row, dict):
            return None
        raw = row.get(key)
        if isinstance(raw, str) and raw:
            return raw
        return None

    @staticmethod
    def _iter_samples(max_samples: int) -> Iterator[Dict[str, Any]]:
        """Yield unrefined passage text plus catalog fields"""
        if not HF_TOKEN or not isinstance(HF_TOKEN, str):
            raise error("HF_TOKEN not configured")
        remaining = max_samples
        for hf_split, training_split in _HF_SPLIT_MAP:
            if remaining <= 0:
                break
            dataset = load_dataset(
                _HF_ID,
                split=hf_split,
                revision=_HF_REVISION,
                token=HF_TOKEN,
                streaming=True,
            )
            dataset = dataset.take(remaining)
            for row in dataset:
                prompt = IngestAcademicSource._text_from_event(row, "prompt")
                reference = IngestAcademicSource._text_from_event(row, "reference")
                label = IngestAcademicSource._label_from_event(row)
                citation = IngestAcademicSource._citation_from_event(row)
                published_at = IngestAcademicSource._published_at_from_event(row)
                chunk_index = IngestAcademicSource._chunk_index_from_event(row)
                if (
                    prompt is None
                    or reference is None
                    or label is None
                    or citation is None
                    or published_at is None
                    or chunk_index is None
                ):
                    continue
                volcano_id = row.get("volcano_id") if isinstance(row, dict) else None
                if volcano_id is not None and not isinstance(volcano_id, str):
                    volcano_id = None
                yield {
                    "prompt": prompt,
                    "reference": reference,
                    "label": label,
                    "split": training_split,
                    "citation": citation,
                    "published_at": published_at,
                    "chunk_index": chunk_index,
                    "volcano_id": volcano_id,
                }
                remaining -= 1
                if remaining <= 0:
                    break
