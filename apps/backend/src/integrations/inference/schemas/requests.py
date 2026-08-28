"""
Author: Sean Froning
Created Date: 8.28.2026
Request models for Inferences
"""

from pydantic import BaseModel
from typing import List, Optional
from fiery_python import ModelTier, ModelRole


class InferenceSingleRequest(BaseModel):
    """Request model for single inference"""

    tier: ModelTier
    role: ModelRole
    interferogram_id: Optional[str] = None
    volcano_id: Optional[str] = None

    def validate_payload(self) -> bool:
        if not self.interferogram_id and not self.volcano_id:
            return False
        if self.interferogram_id and self.volcano_id:
            return False
        return True


class InferenceBatchRequest(BaseModel):
    """Request model for batch inference"""

    tier: ModelTier
    role: ModelRole
    volcano_ids: List[str]
