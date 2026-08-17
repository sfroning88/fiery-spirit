"""
Author: Sean Froning
Modified Date: 5.16.2026
Request models for Training
"""

from pydantic import BaseModel, ConfigDict


class ShuffleRequest(BaseModel):
    """Request model for shuffling training groups (empty body)"""

    model_config = ConfigDict(extra="forbid")


class TrainingRequest(BaseModel):
    """Request model for running training job (empty body)"""

    model_config = ConfigDict(extra="forbid")
