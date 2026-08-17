"""
Author: Sean Froning
Created Date: 5.9.2026
Request models for Predictions
"""

from pydantic import BaseModel, Field, AfterValidator
from typing import Annotated
from focus_python import SchemaUtils


class PredictionRequest(BaseModel):
    """Request model for retrieving prediction from winning model or all models"""

    property_id: Annotated[str, AfterValidator(SchemaUtils.valid_uuid)] = Field(
        ...,
        description="Property to retrieve prediction for",
        example="00000000-0000-0000-0000-000000000000",
    )
    multi_enabled: bool = Field(
        default=False,
        description="If true, returns predictions from every model in the latest batch; otherwise returns the winner only",
    )
