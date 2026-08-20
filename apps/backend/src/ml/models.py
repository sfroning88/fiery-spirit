"""
Author: Sean Froning
Created Date: 8.20.2026
Inference-side in-memory model
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Any
from pydantic import BaseModel
from fiery_python import (
    ModelTier,
    ModelRole,
    TrainingStage,
    TrainingPrecision,
)


class LoadedModel(BaseModel):
    """In-memory representation of a loaded model artifact"""

    tier: ModelTier
    role: ModelRole
    stage: TrainingStage
    precision: TrainingPrecision
    architecture: str
    param_count: int
    sparsity: Decimal
    artifact_id: str
    promoted_at: datetime
    metrics: Dict[str, Decimal] = {}
    preprocessing: Dict[str, Any] = {}
    parent_id: Optional[str] = None


@dataclass
class ArtifactRegistry:
    """Structured input to model registry of (tier, role)"""

    model: Optional[Any]
    metadata: Optional[LoadedModel]
    artifact_id: Optional[str]
