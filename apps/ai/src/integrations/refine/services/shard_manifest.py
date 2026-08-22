"""
Author: Sean Froning
Created Date: 8.22.2026
Processing functions for Refine manifest
"""

from typing import Any, Dict, Optional
from fiery_python import (
    Shard,
    TrainingDeformation,
    TrainingDeformationLabel,
    TrainingSplit,
)


class RefineShardManifest:
    """Accumulate split counts, class balance, and shard index for a refine job"""

    def __init__(
        self,
        contract_id: str,
        transform_hash: str,
        deformation: TrainingDeformation,
    ) -> None:
        self._contract_id = contract_id
        self._transform_hash = transform_hash
        self._deformation = deformation
        self._splits: Dict[str, Dict[str, Any]] = {
            split.value: {
                "sample_count": 0,
                "rejected_count": 0,
                "label_counts": {label.value: 0 for label in TrainingDeformationLabel},
                "rejected_label_counts": {
                    label.value: 0 for label in TrainingDeformationLabel
                },
                "shards": [],
            }
            for split in TrainingSplit
        }

    def record_kept(
        self, split: TrainingSplit, label: TrainingDeformationLabel
    ) -> None:
        bucket = self._splits[split.value]
        bucket["sample_count"] += 1
        bucket["label_counts"][label.value] += 1

    def record_reject(
        self,
        split: TrainingSplit,
        label: Optional[TrainingDeformationLabel],
        reason: str,
    ) -> None:
        bucket = self._splits[split.value]
        bucket["rejected_count"] += 1
        if label is not None:
            bucket["rejected_label_counts"][label.value] += 1
        reasons = bucket.setdefault("reject_reasons", {})
        reasons[reason] = reasons.get(reason, 0) + 1

    def record_shard(
        self,
        split: TrainingSplit,
        key: str,
        sample_count: int,
        nbytes: int,
    ) -> None:
        self._splits[split.value]["shards"].append(
            {
                "key": key,
                "sample_count": sample_count,
                "bytes": nbytes,
            }
        )

    def sample_count(self) -> int:
        return sum(bucket["sample_count"] for bucket in self._splits.values())

    def rejected_count(self) -> int:
        return sum(bucket["rejected_count"] for bucket in self._splits.values())

    def shard_count(self) -> int:
        return sum(len(bucket["shards"]) for bucket in self._splits.values())

    def payload(self) -> Dict[str, Any]:
        return {
            "format_version": 1,
            "contract_id": self._contract_id,
            "transform_hash": self._transform_hash,
            "patch_px": self._deformation.patch_px,
            "wrap_rad": str(self._deformation.wrap_rad),
            "normalize": self._deformation.normalize.value,
            "coherence_min": str(self._deformation.coherence_min),
            "sample_count": self.sample_count(),
            "rejected_count": self.rejected_count(),
            "shard_count": self.shard_count(),
            "splits": self._splits,
        }

    def dumps(self) -> bytes:
        return Shard.write_manifest(self.payload())
