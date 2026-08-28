"""
Author: Sean Froning
Created Date: 8.28.2026
Inference-side in-memory outcome
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from typing import Dict, Optional
from fiery_python import (
    InferenceAbstainReason,
    TrainingDeformationLabel,
)


class InferenceOutcome(BaseModel):
    """In-memory representation of inference outcome"""

    artifact_id: str
    transform_hash: str
    op_version: int
    threshold_used: Decimal
    abstention_band: Decimal
    abstained: bool = False
    abstained_reason: Optional[InferenceAbstainReason] = None
    latency_ms: Optional[Decimal] = None
    inferred_at: datetime
    probabilities: Dict[str, Decimal]
    label: Optional[TrainingDeformationLabel] = None
    score: Optional[Decimal] = None
    interferogram_id: Optional[str] = None
    volcano_id: Optional[str] = None
