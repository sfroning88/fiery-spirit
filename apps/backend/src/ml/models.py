"""
Author: Sean Froning
Modified Date: 5.30.2026
Inference-side in-memory model
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class LoadedModel(BaseModel):
    """In-memory representation of a loaded sklearn model entry"""

    type: str
    score: float
    rmse: float
    trained_at: datetime
    winner: bool
    batch_id: str
    msa_encoding: Optional[Dict[str, float]] = None
    state_encoding: Optional[Dict[str, float]] = None
    global_mean: Optional[float] = None
    feature_columns: Optional[List[str]] = None
    target_column: Optional[str] = None
    samples: Optional[int] = None
    winner_type: Optional[str] = None


@dataclass
class PredictionTypeRegistry:
    """Structured input to model registry of prediction type"""

    models: Dict[str, Any]
    metadata: Dict[str, LoadedModel]
    batch_id: Optional[str]
    multi_loaded: Optional[bool]
