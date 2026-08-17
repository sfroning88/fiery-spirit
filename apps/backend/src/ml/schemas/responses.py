"""
Author: Sean Froning
Created Date: 5.16.2026
Response models for Models
"""

from pydantic import BaseModel, Field
from typing import List


class ModelResponse(BaseModel):
    """Response model for retrieving prediction from winning model or all models"""

    model_ids: List[str] = Field(
        ...,
        description="List of ids of the loaded models",
        example=["model_1", "model_2", "model_3", "model_4"],
    )
