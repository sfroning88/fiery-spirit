"""
Author: Sean Froning
Created Date: 8.21.2026
Processing functions for Hephaestus source
"""

import numpy as np
from datasets import load_dataset
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional, Tuple
from fiery_python import config, error, logging
from fiery_python import (
    TRAINING_DB_PAGE_SIZE,
    TrainingSplit,
    TrainingStatus,
    TrainingSampleSource,
    TrainingDeformationLabel,
    DatasetIngest,
    TrainingInterferogram,
    BlobStorageServices,
)
from .persist_service import IngestPersistService

logger = logging.get_logger(__name__)

HF_STREAM_TOKEN = config.get("HF_STREAM_TOKEN")

_HF_ID = "orion-ai-lab/Thalia"
_HF_SPLIT = "train"
_HF_REVISION = "543216fef7483825e786b3da96caeb1ee197befc"
_PHASE_KEYS = ("insar_difference",)
_COHERENCE_KEYS = ("insar_coherence",)


class IngestHephaestusSource:
    """Stream Hephaestus frames to unrefined R2 and catalog interferograms"""

    @classmethod
    def run(cls, ingest_id: str, max_samples: int = 5) -> int:
        """Download pathes, store unrefined samples, upsert interferograms; return asset_count"""
        max_samples = max(max_samples, 5)
        started_at = datetime.now(timezone.utc)
        IngestPersistService.upsert_ingest(
            DatasetIngest(
                id=ingest_id,
                source=TrainingSampleSource.HEPHAESTUS,
                asset_count=0,
                status=TrainingStatus.EXECUTING,
                started_at=started_at,
            )
        )
        page: List[TrainingInterferogram] = []
        asset_count = 0
        try:
            for sample in cls._iter_samples(max_samples):
                body = IngestPersistService.npz_bytes(
                    sample["phase"], sample["coherence"]
                )
                storage_path = BlobStorageServices.put_unrefined(
                    TrainingSampleSource.HEPHAESTUS, body
                )
                interferogram = TrainingInterferogram(
                    source=TrainingSampleSource.HEPHAESTUS,
                    split=sample.get("split", TrainingSplit.TRAIN),
                    label=sample.get("label", TrainingDeformationLabel.NEGATIVE),
                    frame_id=sample.get("frame_id"),
                    primary_at=sample.get("primary_at"),
                    secondary_at=sample.get("secondary_at"),
                    coherence_mean=sample.get("coherence_mean"),
                    storage_path=storage_path,
                )
                page.append(interferogram)
                asset_count += 1
                if len(page) >= TRAINING_DB_PAGE_SIZE:
                    IngestPersistService.upsert_interferograms(page)
                    page.clear()
                if asset_count >= max_samples:
                    break
            if page:
                IngestPersistService.upsert_interferograms(page)
            finished_at = datetime.now(timezone.utc)
            IngestPersistService.upsert_ingest(
                DatasetIngest(
                    id=ingest_id,
                    source=TrainingSampleSource.HEPHAESTUS,
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
                    source=TrainingSampleSource.HEPHAESTUS,
                    asset_count=asset_count,
                    status=TrainingStatus.FAILED,
                    started_at=started_at,
                    finished_at=finished_at,
                    error_message=str(err),
                )
            )
            raise

    @staticmethod
    def _cast_height_width(array: np.ndarray) -> np.ndarray:
        array = np.asarray(array, dtype=np.float32)
        array = np.squeeze(array)
        if array.ndim == 3:
            channel_axis = int(np.argmin(array.shape))
            array = np.take(array, -1, axis=channel_axis)
        if array.ndim != 2:
            raise ValueError("expected (H, W) InSAR channel")
        return array

    @staticmethod
    def _pick_channel(
        sample: Dict[str, np.ndarray], names: Tuple[str, ...]
    ) -> Optional[np.ndarray]:
        for name in names:
            array = sample.get(name)
            if array is not None:
                return IngestHephaestusSource._cast_height_width(array)
        return None

    @staticmethod
    def _channels_from_interferogram(
        sample: Any,
    ) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        phase = IngestHephaestusSource._pick_channel(sample, _PHASE_KEYS)
        coherence = IngestHephaestusSource._pick_channel(sample, _COHERENCE_KEYS)
        if phase is None or coherence is None:
            return None
        if phase.shape != coherence.shape:
            return None
        if float(np.nanmax(coherence)) > 1.0:
            coherence = coherence / 255.0
        return phase, np.clip(coherence, 0.0, 1.0)

    @staticmethod
    def _label_interferogram(sample: Any) -> Optional[TrainingDeformationLabel]:
        flags = sample
        if isinstance(sample.get("json"), dict):
            flags = sample["json"]
        raw = flags.get("label") or []
        if isinstance(raw, str):
            raw = [raw]
        names = {str(item) for item in raw}
        if flags.get("corrupted") or flags.get("no_info") or flags.get("low_coherence"):
            return None
        if "Earthquake" in names:
            return TrainingDeformationLabel.UNCERTAIN
        if "Deformation" in names:
            return TrainingDeformationLabel.POSITIVE
        if "Non_Deformation" in names:
            return TrainingDeformationLabel.NEGATIVE
        return TrainingDeformationLabel.UNCERTAIN

    @staticmethod
    def _iter_samples(max_samples: int) -> Iterator[Dict[str, Any]]:
        """Yield unrefined phase/coherence plus catalog fields"""
        if not HF_STREAM_TOKEN or not isinstance(HF_STREAM_TOKEN, str):
            raise error("HF_STREAM_TOKEN not configured")
        dataset = load_dataset(
            _HF_ID,
            split=_HF_SPLIT,
            revision=_HF_REVISION,
            token=HF_STREAM_TOKEN,
            streaming=True,
        )
        dataset = dataset.take(max_samples)
        for sample in dataset:
            channels = IngestHephaestusSource._channels_from_interferogram(sample)
            if channels is None:
                continue
            phase, coherence = channels
            label = IngestHephaestusSource._label_interferogram(sample)
            if label is None:
                continue
            yield {
                "phase": phase,
                "coherence": coherence,
                "split": TrainingSplit.TRAIN,
                "label": label,
                "frame_id": sample.get("frame_id") or sample.get("id"),
                "primary_at": sample.get("primary_date"),
                "secondary_at": sample.get("secondary_date"),
                "coherence_mean": float(np.mean(coherence)),
            }
