"""
Author: Sean Froning
Created Date: 8.22.2026
Processing functions for Shard writer
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from fiery_python import error, logging
from fiery_python import (
    TRAINING_DB_FETCH_SIZE,
    BlobStorageServices,
    DatasetVersion,
    Shard,
    TrainingDeformation,
    TrainingInterferogram,
    TrainingSplit,
    TrainingStatus,
    Transformation,
    TransformationRejected,
)
from .persist_service import RefinePersistService
from .shard_manifest import RefineShardManifest

logger = logging.get_logger(__name__)

_FORMAT_VERSION = 1
_TARGET_SHARD_BYTES = 200 * 1024 * 1024
_LABEL_OVERHEAD = 256
_BASE_ID = "00000000-0000-0000-0000-000000000000"


class RefineShardWriter:
    """Stream unrefined R2 and refine shards back to refined R2"""

    @classmethod
    def run(cls, contract_id: str, version_id: str) -> int:
        """Read unrefined samples, apply transform, store refined shards; return sample_count"""
        deformation = RefinePersistService.select_deformation(contract_id)
        if not deformation:
            raise error("Training deformation not found")
        transform_hash = Transformation.transform_hash(deformation)
        version = RefinePersistService.select_version(contract_id, transform_hash)
        if not version:
            raise error("Dataset version not found")
        if version.id != version_id:
            raise error("Dataset version mismatch")
        RefinePersistService.upsert_version(
            DatasetVersion(
                id=version.id,
                transform_hash=transform_hash,
                manifest_path=version.manifest_path,
                shard_count=0,
                sample_count=0,
                status=TrainingStatus.EXECUTING,
                contract_id=contract_id,
            )
        )
        manifest = RefineShardManifest(contract_id, transform_hash, deformation)
        sample_count = 0
        try:
            for split in TrainingSplit:
                sample_count += cls._write_split(
                    contract_id,
                    transform_hash,
                    split,
                    deformation,
                    manifest,
                )
            manifest_path = BlobStorageServices.put_manifest(
                contract_id, transform_hash, manifest.dumps()
            )
            RefinePersistService.upsert_version(
                DatasetVersion(
                    id=version.id,
                    transform_hash=transform_hash,
                    manifest_path=manifest_path,
                    shard_count=manifest.shard_count(),
                    sample_count=manifest.sample_count(),
                    status=TrainingStatus.COMPLETED,
                    contract_id=contract_id,
                )
            )
            return sample_count
        except Exception as err:
            RefinePersistService.upsert_version(
                DatasetVersion(
                    id=version.id,
                    transform_hash=transform_hash,
                    manifest_path=version.manifest_path,
                    shard_count=manifest.shard_count(),
                    sample_count=manifest.sample_count(),
                    status=TrainingStatus.FAILED,
                    contract_id=contract_id,
                )
            )
            logger.error(
                "refine_shard_writer_failed",
                contract_id=contract_id,
                version_id=version_id,
                error=str(err),
            )
            raise

    @classmethod
    def _write_split(
        cls,
        contract_id: str,
        transform_hash: str,
        split: TrainingSplit,
        deformation: TrainingDeformation,
        manifest: RefineShardManifest,
    ) -> int:
        buffer: List[Tuple[str, np.ndarray, Dict[str, Any]]] = []
        approx_bytes = 0
        shard_index = 0
        kept = 0
        interferograms = (
            RefinePersistService.select_interferograms(
                split, _BASE_ID, TRAINING_DB_FETCH_SIZE
            )
            or []
        )
        for interferogram in interferograms:
            sample = cls._transform_interferogram(interferogram, deformation, manifest)
            if sample is None:
                continue
            key, phase, label = sample
            buffer.append((key, phase, label))
            approx_bytes += int(phase.nbytes) + _LABEL_OVERHEAD
            kept += 1
            if approx_bytes >= _TARGET_SHARD_BYTES:
                cls._flush_shard(
                    contract_id,
                    transform_hash,
                    split,
                    shard_index,
                    buffer,
                    manifest,
                )
                buffer = []
                approx_bytes = 0
                shard_index += 1
        if buffer:
            cls._flush_shard(
                contract_id,
                transform_hash,
                split,
                shard_index,
                buffer,
                manifest,
            )
        return kept

    @staticmethod
    def _transform_interferogram(
        interferogram: TrainingInterferogram,
        deformation: TrainingDeformation,
        manifest: RefineShardManifest,
    ) -> Optional[Tuple[str, np.ndarray, Dict[str, Any]]]:
        if not interferogram.id or not interferogram.storage_path:
            manifest.record_reject(
                interferogram.split, interferogram.label, "missing_identity"
            )
            return None
        try:
            body = BlobStorageServices.get_unrefined(interferogram.storage_path)
            array = RefinePersistService.load_npz(body)
            phase = Transformation.apply(array, deformation)
        except TransformationRejected as err:
            manifest.record_reject(interferogram.split, interferogram.label, str(err))
            return None
        except Exception as err:
            manifest.record_reject(interferogram.split, interferogram.label, str(err))
            return None
        manifest.record_kept(interferogram.split, interferogram.label)
        return (
            interferogram.id,
            phase,
            {
                "label": interferogram.label.value,
                "split": interferogram.split.value,
                "format_version": _FORMAT_VERSION,
            },
        )

    @staticmethod
    def _flush_shard(
        contract_id: str,
        transform_hash: str,
        split: TrainingSplit,
        shard_index: int,
        buffer: List[Tuple[str, np.ndarray, Dict[str, Any]]],
        manifest: RefineShardManifest,
    ) -> None:
        body = Shard.write(buffer)
        key = BlobStorageServices.put_shard(
            contract_id, transform_hash, split, shard_index, body
        )
        manifest.record_shard(split, key, len(buffer), len(body))
        logger.info(
            "refine_shard_flushed",
            contract_id=contract_id,
            split=split.value,
            shard_index=shard_index,
            sample_count=len(buffer),
            bytes=len(body),
        )
