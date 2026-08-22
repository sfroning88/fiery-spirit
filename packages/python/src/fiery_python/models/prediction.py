"""
Author: Sean Froning
Created Date: 8.19.2026
Class objects for Prediction schema
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from ._base_fiery import BaseFiery
from ..enums import (
    TrainingSeismicLabel,
    TrainingDeformationLabel,
)


class PredictionDeformation(BaseFiery):
    """Normalized Prediction Deformation"""

    score: Decimal
    label: TrainingDeformationLabel
    abstained: bool = False
    inferred_at: datetime
    artifact_id: str
    interferogram_id: str

    def prepare_for_storage(self, include_id: bool = False) -> dict:
        """Composite PK table has no id column"""
        return super().prepare_for_storage(include_id=False)


class PredictionSeismic(BaseFiery):
    """Normalized Prediction Seismic"""

    label: TrainingSeismicLabel
    probabilities: List[Decimal]
    latency_ms: Optional[Decimal] = None
    inferred_at: datetime
    artifact_id: str
    seismic_event_id: str

    def prepare_for_storage(self, include_id: bool = False) -> dict:
        """Composite PK table has no id column"""
        return super().prepare_for_storage(include_id=False)
