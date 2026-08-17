"""
Author: Sean Froning
Modified Date: 5.16.2026
Class definitions for Training enums
"""

from enum import Enum


class TrainingType(str, Enum):
    """Training model enumeration"""

    LINEAR = "linear"
    RIDGE = "ridge"
    FOREST = "forest"
    GBM = "gbm"
    XGBOOST = "xgboost"
    LASSO = "lasso"
    SVR = "svr"
    ELASTICNET = "elasticnet"


class TrainingStatus(str, Enum):
    """Training status enumeration"""

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrainingFunction(str, Enum):
    """Training function enumeration"""

    TRAIN = "train"
    VALIDATE = "validate"
    TEST = "test"
