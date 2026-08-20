"""
Author: Sean Froning
Created Date: 8.17.2026
Request models for Predictions
"""

from pydantic import BaseModel, ConfigDict


class PredictionRequest(BaseModel):
    """Request model for retrieving prediction"""

    model_config = ConfigDict(extra="forbid")
