"""
Author: Sean Froning
Created Date: 8.28.2026
Type declarations for Training schema
"""

from typing import Optional, Tuple
from ..models import (
    TrainingHyperparameterPretrain,
    TrainingHyperparameterLoraVisual,
    TrainingHyperparameterLoraLanguage,
    TrainingHyperparameterDistill,
    TrainingHyperparameterPrune,
    TrainingHyperparameterQuantize,
    TrainingTargetModules,
)

TrainingHyperparameter = Tuple[
    Optional[TrainingHyperparameterPretrain],
    Optional[Tuple[TrainingHyperparameterLoraVisual, TrainingTargetModules]],
    Optional[Tuple[TrainingHyperparameterLoraLanguage, TrainingTargetModules]],
    Optional[TrainingHyperparameterDistill],
    Optional[TrainingHyperparameterPrune],
    Optional[TrainingHyperparameterQuantize],
]
