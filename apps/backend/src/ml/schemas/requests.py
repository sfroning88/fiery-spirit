"""
Author: Sean Froning
Created Date: 8.17.2026
Request models for Models
"""

from pydantic import BaseModel
from fiery_python import ModelTier, ModelRole


class ModelRequest(BaseModel):
    """Request model for reloading model registry"""

    tier: ModelTier
    role: ModelRole
