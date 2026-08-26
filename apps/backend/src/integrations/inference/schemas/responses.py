"""
Author: Sean Froning
Created Date: 8.17.2026
Response models for Inferences
"""

from pydantic import BaseModel, ConfigDict


class InferenceResponse(BaseModel):
    """Response model for retrieving prediction"""

    model_config = ConfigDict(extra="forbid")
