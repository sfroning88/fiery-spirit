"""
Author: Sean Froning
Modified Date: 5.30.2026
Definitions for prediction structures
"""

from typing import Dict
from ..enums import PredictionType

WINNER_KEY = "winner"
PREDICTION_TARGETS: Dict[PredictionType, str] = {
    PredictionType.CONTROLLABLE_PRD: "controllable_prd",
    PredictionType.OCCUPANCY: "occupancy",
    PredictionType.OPERATING_MARGIN: "operating_margin",
}
PREDICTION_TABLE = ("ai", "prediction")
PREDICTION_TYPE_ENUM = ("ai", "prediction_type")
