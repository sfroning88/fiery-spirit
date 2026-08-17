"""
Author: Sean Froning
Created Date: 8.17.2026
Response models for Models
"""

from pydantic import BaseModel, ConfigDict


class ModelResponse(BaseModel):
    """Response model for retrieving predictions (empty body)"""

    model_config = ConfigDict(extra="forbid")
