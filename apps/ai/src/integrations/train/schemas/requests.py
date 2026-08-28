"""
Author: Sean Froning
Created Date: 8.23.2026
Request models for Train
"""

from pydantic import BaseModel, AfterValidator
from typing import Annotated
from fiery_python import TrainingStage, SchemaUtils


class TrainRequest(BaseModel):
    """Request model for running train job"""

    contract_id: Annotated[str, AfterValidator(SchemaUtils.valid_uuid)]
    version_id: Annotated[str, AfterValidator(SchemaUtils.valid_uuid)]
    stage: TrainingStage
