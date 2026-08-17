"""
Author: Sean Froning
Modified Date: 5.30.2026
Class definitions for Prediction enums
"""

from enum import Enum


class PredictionType(str, Enum):
    """Prediction scope enumeration"""

    CONTROLLABLE_PRD = "controllable_prd"
    OCCUPANCY = "occupancy"
    OPERATING_MARGIN = "operating_margin"
