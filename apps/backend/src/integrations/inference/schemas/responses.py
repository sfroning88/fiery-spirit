"""
Author: Sean Froning
Created Date: 8.28.2026
Response models for Inferences
"""

from pydantic import BaseModel
from typing import List
from ..models import InferenceOutcome


class InferenceResponse(BaseModel):
    """Response model for retrieving inference"""

    results: List[InferenceOutcome]
    artifact_id: str
    transform_hash: str
