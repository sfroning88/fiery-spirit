"""
Author: Sean Froning
Modified Date: 5.30.2026
Class definitions for Prisma enums
"""

from __future__ import annotations
from enum import Enum
from .prediction import PredictionType


class PrismaPredictionType(str, Enum):
    CONTROLLABLE_PRD = "controllablePrd"
    OCCUPANCY = "occupancy"
    OPERATING_MARGIN = "operatingMargin"

    @classmethod
    def cast(cls, domain: PredictionType | None) -> PrismaPredictionType:
        if domain is None:
            raise ValueError("prediction type is required")
        return cls[domain.name]
