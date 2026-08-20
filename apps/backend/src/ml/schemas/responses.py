"""
Author: Sean Froning
Created Date: 8.17.2026
Response models for Models
"""

from typing import Optional
from pydantic import BaseModel
from fiery_python import ModelTier, ModelRole


class ModelResponse(BaseModel):
    """Response model for reloading model registry"""

    tier: ModelTier
    role: ModelRole
    artifact_id: Optional[str] = None
    ready: bool
