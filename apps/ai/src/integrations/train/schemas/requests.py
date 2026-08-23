"""
Author: Sean Froning
Created Date: 8.23.2026
Request models for Train
"""

from pydantic import BaseModel
from fiery_python import TrainingStage


class TrainRequest(BaseModel):
    """Request model for running train job"""

    contract_id: str
    version_id: str
    stage: TrainingStage
