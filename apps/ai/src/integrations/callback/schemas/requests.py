"""
Author: Sean Froning
Created Date: 8.24.2026
Request models for Callback
"""

from decimal import Decimal
from pydantic import BaseModel, Field
from typing import List, Optional
from fiery_python import (
    ModelTier,
    ModelRole,
    TrainingPrecision,
    ModelMetric,
)


class CallbackRequest(BaseModel):
    """Request model for receiving train callback"""

    session_id: str
    tier: ModelTier
    role: ModelRole
    precision: TrainingPrecision = Field(default=TrainingPrecision.FP32)
    storage_path: str
    signature: str
    param_count: int
    architecture: str
    sparsity: Decimal = Decimal("0")
    metrics: List[ModelMetric]
    nonce: Optional[str] = None
