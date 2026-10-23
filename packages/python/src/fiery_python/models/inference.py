"""
Author: Sean Froning
Created Date: 8.27.2026
Class objects for Inference schema
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from ._base_fiery import BaseFiery
from ..enums import (
    InferenceAbstainReason,
    TrainingDeformationLabel,
    TrainingSeismicLabel,
    TrainingLanguageLabel,
)
from ..utils import UuidUtils


class InferenceDeformation(BaseFiery):
    """Normalized Inference Deformation"""

    score: Optional[Decimal] = None
    label: Optional[TrainingDeformationLabel] = None
    threshold_used: Decimal
    abstention_band: Decimal
    abstained: bool = False
    abstained_reason: Optional[InferenceAbstainReason] = None
    transform_hash: str
    op_version: int
    latency_ms: Optional[Decimal] = None
    inferred_at: datetime
    artifact_id: str
    interferogram_id: str

    def prepare_for_storage(self, include_id: bool = False) -> dict:
        """Composite PK table has no id column"""
        return super().prepare_for_storage(include_id=False)


class InferenceSeismic(BaseFiery):
    """Normalized Inference Seismic"""

    label: Optional[TrainingSeismicLabel] = None
    probabilities: List[Decimal]
    class_order: List[TrainingSeismicLabel]
    threshold_used: Decimal
    abstention_band: Decimal
    abstained: bool = False
    abstained_reason: Optional[InferenceAbstainReason] = None
    transform_hash: str
    op_version: int
    latency_ms: Optional[Decimal] = None
    inferred_at: datetime
    artifact_id: str
    seismic_event_id: str

    def prepare_for_storage(self, include_id: bool = False) -> dict:
        """Composite PK table has no id column"""
        return super().prepare_for_storage(include_id=False)


class InferenceLanguage(BaseFiery):
    """Normalized Inference Language"""

    label: Optional[TrainingLanguageLabel] = None
    probabilities: List[Decimal]
    class_order: List[TrainingLanguageLabel]
    threshold_used: Decimal
    abstention_band: Decimal
    abstained: bool = False
    abstained_reason: Optional[InferenceAbstainReason] = None
    generated_text: str
    latency_ms: Optional[Decimal] = None
    inferred_at: datetime
    artifact_id: str
    volcano_id: str

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from (artifact_id, volcano_id, inferred_at)"""
        if not self.artifact_id or not self.volcano_id or not self.inferred_at:
            return None
        return UuidUtils.deterministic_uuid(
            self.artifact_id, self.volcano_id, self.inferred_at
        )


class InferenceFeedback(BaseFiery):
    """Normalized Inference Feedback"""

    agreed: bool
    corrected_deformation: Optional[TrainingDeformationLabel] = None
    corrected_seismic: Optional[TrainingSeismicLabel] = None
    corrected_language: Optional[TrainingLanguageLabel] = None
    note: Optional[str] = None
    interferogram_id: Optional[str] = None
    seismic_event_id: Optional[str] = None
    language_id: Optional[str] = None
    user_id: Optional[str] = None
    artifact_id: str

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from artifact_id and sample_id or language_id"""
        if not self.artifact_id:
            return None
        if self.interferogram_id and not self.seismic_event_id and not self.language_id:
            return UuidUtils.deterministic_uuid(
                self.artifact_id, self.interferogram_id, self.user_id
            )
        if not self.interferogram_id and self.seismic_event_id and not self.language_id:
            return UuidUtils.deterministic_uuid(
                self.artifact_id, self.seismic_event_id, self.user_id
            )
        if not self.interferogram_id and not self.seismic_event_id and self.language_id:
            return UuidUtils.deterministic_uuid(
                self.artifact_id, self.language_id, self.user_id
            )
        return None
