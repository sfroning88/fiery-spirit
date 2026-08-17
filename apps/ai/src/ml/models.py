"""
Author: Sean Froning
Created Date: 5.14.2026
Training-side in-memory feature engineering and model artifacts
"""

from dataclasses import dataclass
from typing import Any, Dict, List
import pandas as pd
from focus_python import TrainingMSAEncoding


@dataclass
class TrainingFrame:
    """Structured output of feature engineering for a single training run"""

    X: pd.DataFrame
    y: pd.Series
    groups: pd.Series
    msa_id: pd.Series
    msa_encoding: Dict[str, float]
    msa_records: List[TrainingMSAEncoding]
    state_id: pd.Series
    state_encoding: Dict[str, float]
    global_mean: float
    target: str


@dataclass
class ModelPayload:
    """Structured artifact persisted to S3 for a completed training run"""

    model: Any
    msa_encoding: Dict[str, float]
    state_encoding: Dict[str, float]
    global_mean: float
    feature_columns: List[str]
    target_column: str
    prediction_type: str
    score: float
    rmse: float
    samples: int
    trained_at: str
    type: str
    batch_id: str

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "msa_encoding": self.msa_encoding,
            "state_encoding": self.state_encoding,
            "global_mean": self.global_mean,
            "feature_columns": self.feature_columns,
            "target_column": self.target_column,
            "prediction_type": self.prediction_type,
            "score": self.score,
            "rmse": self.rmse,
            "samples": self.samples,
            "trained_at": self.trained_at,
            "type": self.type,
            "batch_id": self.batch_id,
        }
