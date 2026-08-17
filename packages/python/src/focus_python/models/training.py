"""
Author: Sean Froning
Modified Date: 5.30.2026
Class objects for training runs
"""

from datetime import datetime
from typing import List, Optional
from ._base_focus import BaseFocus
from ..enums import PredictionType, TrainingType, TrainingStatus


class TrainingMSAEncoding(BaseFocus):
    """Normalized model training msa encoding"""

    mean_target: Optional[float] = None
    sample_count: Optional[int] = None
    msa_id: Optional[str] = None
    batch_id: Optional[str] = None


class TrainingFeature(BaseFocus):
    """Normalized model training feature"""

    columns: Optional[List[str]] = None
    target: Optional[str] = None
    schema_version: Optional[int] = None
    batch_id: Optional[str] = None


class TrainingSplit(BaseFocus):
    """Normalized model training split"""

    version: Optional[int] = None
    train_ratio: Optional[float] = None
    validate_ratio: Optional[float] = None
    test_ratio: Optional[float] = None
    shuffled_at: Optional[datetime] = None


class TrainingBatch(BaseFocus):
    """Normalized model training batch"""

    status: Optional[TrainingStatus] = None
    samples: Optional[int] = None
    split_seed: Optional[int] = None
    prediction_type: Optional[PredictionType] = None
    split_version_id: Optional[int] = None
    feature: Optional[TrainingFeature] = None


class TrainingModel(BaseFocus):
    """Normalized model training run"""

    type: Optional[TrainingType] = None
    status: Optional[TrainingStatus] = None
    r2_score: Optional[float] = None
    train_score: Optional[float] = None
    validate_score: Optional[float] = None
    rmse: Optional[float] = None
    winner: Optional[bool] = None
    storage_path: Optional[str] = None
    trained_at: Optional[datetime] = None
    error_message: Optional[str] = None
    batch_id: Optional[str] = None
