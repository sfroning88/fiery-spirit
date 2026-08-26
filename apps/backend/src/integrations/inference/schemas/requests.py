"""
Author: Sean Froning
Created Date: 8.17.2026
Request models for Inferences
"""

from pydantic import BaseModel, ConfigDict


class InferenceRequest(BaseModel):
    """Request model for retrieving prediction"""

    model_config = ConfigDict(extra="forbid")
