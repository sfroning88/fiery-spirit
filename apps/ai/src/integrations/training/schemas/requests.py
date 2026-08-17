"""
Author: Sean Froning
Created Date: 8.17.2026
Request models for Training
"""

from pydantic import BaseModel, ConfigDict


class TrainingRequest(BaseModel):
    """Request model for running training job (empty body)"""

    model_config = ConfigDict(extra="forbid")
