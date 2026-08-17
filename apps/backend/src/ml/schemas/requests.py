"""
Author: Sean Froning
Modified Date: 5.30.2026
Request models for Models
"""

from pydantic import BaseModel
from focus_python import PredictionType


class ModelRequest(BaseModel):
    """Request model for reloading model registry"""

    prediction_type: PredictionType
    multi_enabled: bool = False
