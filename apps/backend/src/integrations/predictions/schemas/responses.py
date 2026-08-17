"""
Author: Sean Froning
Created Date: 5.9.2026
Response models for Predictions
"""

from pydantic import BaseModel
from typing import List
from focus_python import PrismaPrediction


class PredictionResponse(BaseModel):
    """Response model for retrieving prediction from winning model or all models"""

    predictions: List[PrismaPrediction]
