"""
Author: Sean Froning
Created Date: 8.17.2026
Response models for Predictions
"""

from pydantic import BaseModel, ConfigDict


class PredictionResponse(BaseModel):
    """Response model for retrieving prediction"""

    model_config = ConfigDict(extra="forbid")
