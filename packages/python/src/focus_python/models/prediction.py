"""
Author: Sean Froning
Modified Date: 5.11.2026
Class objects for model predictions
"""

from typing import Optional
from ._base_focus import BaseFocus
from ._base_prisma import BasePrisma
from ..enums import PredictionType, PrismaPredictionType, TrainingType


class Prediction(BaseFocus):
    """Normalized model prediction"""

    type: Optional[PredictionType] = None
    result: Optional[float] = None
    feedback_score: Optional[float] = None
    model_type: Optional[TrainingType] = None
    model_batch_id: Optional[str] = None
    property_id: Optional[str] = None


class PrismaPrediction(BasePrisma):
    """Prisma shape for model Prediction"""

    type: str
    result: float
    feedback_score: Optional[float] = None
    model_type: str
    model_batch_id: str
    property_id: str

    @classmethod
    def from_prediction(cls, prediction: Prediction) -> "PrismaPrediction":
        data = prediction.model_dump(mode="python")
        data["type"] = PrismaPredictionType.cast(prediction.type).value
        return cls.model_validate(data)
