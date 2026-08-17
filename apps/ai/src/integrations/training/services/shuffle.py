"""
Author: Sean Froning
Created Date: 5.16.2026
Processing functions for snapshot shuffling
"""

import time
from collections import Counter
from datetime import datetime, timezone
from typing import Optional
import numpy as np
from focus_python import (
    FUNCTION_WEIGHT_SPLITS,
    TRAINING_FUNCTION_SPLIT_VERSION,
    TrainingFunction,
    TrainingSplit,
)
from .persist import PersistServices


class ShuffleServices:
    """Operations pertaining to model shuffling"""

    @staticmethod
    def shuffle_snapshot_functions(
        seed: Optional[int] = None,
    ) -> dict:
        """Assign each Property a TrainingFunction, cascade to all its snapshots, and persist the split version"""
        resolved_seed = seed if seed is not None else int(time.time())
        property_ids = PersistServices.fetch_property_ids()
        ids = np.array(property_ids)
        rng = np.random.default_rng(resolved_seed)
        rng.shuffle(ids)

        num = len(ids)
        train_ratio, validate_ratio, test_ratio = FUNCTION_WEIGHT_SPLITS
        train_cut = int(num * train_ratio)
        val_cut = int(num * (train_ratio + validate_ratio))

        assignments: dict[str, TrainingFunction] = {}
        for pid in ids[:train_cut]:
            assignments[pid] = TrainingFunction.TRAIN
        for pid in ids[train_cut:val_cut]:
            assignments[pid] = TrainingFunction.VALIDATE
        for pid in ids[val_cut:]:
            assignments[pid] = TrainingFunction.TEST

        shuffled_at = datetime.now(tz=timezone.utc)

        PersistServices.seed_split_with_functions(
            assignments,
            TrainingSplit(
                version=TRAINING_FUNCTION_SPLIT_VERSION,
                train_ratio=train_ratio,
                validate_ratio=validate_ratio,
                test_ratio=test_ratio,
                shuffled_at=shuffled_at,
            ),
        )

        counts = Counter(func.value for func in assignments.values())
        return {
            "seed": resolved_seed,
            "version": TRAINING_FUNCTION_SPLIT_VERSION,
            "counts": dict(counts),
        }
