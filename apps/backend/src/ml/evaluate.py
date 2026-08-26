"""
Author: Sean Froning
Created Date: 8.26.2026
Operations pertaining to ML promotion
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from fiery_python import db_pool, logging
from fiery_python import (
    PoolFetch,
    MODEL_REGISTRY_SLOTS,
    MODEL_DB_FETCH_SIZE,
    ModelTier,
    ModelRole,
    ModelMetricName,
    TrainingSplit,
    TrainingPrecision,
    ModelArtifact,
    ModelMetric,
    ModelBudget,
)
from .models import EvaluatedModel
from .queries.select_challenger_artifacts import QUERY as SELECT_CHALLENGER_ARTIFACTS
from .queries.select_incumbent_artifact import QUERY as SELECT_INCUMBENT_ARTIFACT
from .queries.select_model_metrics import QUERY as SELECT_METRICS
from .queries.upsert_model_artifact import QUERY as UPSERT_ARTIFACT
from .queries.upsert_model_budget import QUERY as UPSERT_BUDGET

logger = logging.get_logger(__name__)

_BYTES_PER_PARAM = {
    TrainingPrecision.FP32: 4,
    TrainingPrecision.FP16: 2,
    TrainingPrecision.INT8: 1,
}
_EDGE_FLASH_BUDGET_KB = Decimal("256")
_EDGE_PEAK_RAM_BUDGET_KB = Decimal("256")
_EDGE_MACS_BUDGET = 50_000_000


class _ModelEvaluator:
    """Evaluate challenger artifacts against incumbents"""

    @classmethod
    def run(cls) -> List[EvaluatedModel]:
        """Evaluate unpromoted challengers and persist any promotions"""
        evaluated_models: List[EvaluatedModel] = []
        challengers = cls._fetch_challengers(MODEL_DB_FETCH_SIZE)
        incumbents = {key: cls._fetch_incumbent(key) for key in MODEL_REGISTRY_SLOTS}
        incumbent_metrics = {
            incumbent.id: cls._fetch_metrics(incumbent.id, MODEL_DB_FETCH_SIZE)
            for key, incumbent in incumbents.items()
            if incumbents[key] and incumbent.id
        }
        evaluated_at = datetime.now(timezone.utc)
        for challenger in challengers:
            challenger.id = challenger.id or challenger.deterministic_id()
            if not challenger.id:
                continue
            promoted = False
            promoted_at = None
            denied_reason = None
            try:
                key = (challenger.tier, challenger.role)
                if key not in MODEL_REGISTRY_SLOTS:
                    denied_reason = "Challenger not in model registry slots"
                else:
                    incumbent = incumbents.get(key)
                    metrics_to_beat: List[ModelMetric] = []
                    if incumbent and incumbent.id:
                        metrics_to_beat = incumbent_metrics.get(incumbent.id) or []
                    if cls._gate_check(challenger, metrics_to_beat):
                        if cls._budget_check(challenger, evaluated_at):
                            promoted = True
                            promoted_at = evaluated_at
                            if (
                                incumbent
                                and incumbent.id
                                and incumbent.id != challenger.id
                            ):
                                incumbent.promoted = False
                                incumbent.promoted_at = None
                                cls._upsert_artifact(incumbent)
                            challenger.promoted = True
                            challenger.promoted_at = evaluated_at
                            cls._upsert_artifact(challenger)
                        else:
                            denied_reason = "Failed to pass edge device budget"
                    else:
                        denied_reason = "Failed to beat incumbent model"
            except Exception as err:
                logger.warning(
                    "model_evaluator_failed",
                    artifact_id=challenger.id,
                    error=str(err),
                )
                denied_reason = str(err)
            evaluated_models.append(
                EvaluatedModel(
                    artifact_id=challenger.id,
                    tier=challenger.tier,
                    role=challenger.role,
                    evaluated_at=evaluated_at,
                    promoted=promoted,
                    promoted_at=promoted_at,
                    denied_reason=denied_reason,
                    ready=False,
                )
            )
        return evaluated_models

    @classmethod
    def _gate_check(
        cls,
        challenger: ModelArtifact,
        metrics_to_beat: List[ModelMetric],
    ) -> bool:
        key = (challenger.tier, challenger.role)
        if not challenger.id:
            return False
        challenger_metrics = cls._fetch_metrics(challenger.id, MODEL_DB_FETCH_SIZE)
        if not challenger_metrics:
            return False
        match key:
            case (ModelTier.CLOUD, ModelRole.SCREENER):
                primary, secondary = (
                    ModelMetricName.RECALL,
                    ModelMetricName.ABSTENTION_RATE,
                )
            case (ModelTier.CLOUD, ModelRole.TEACHER):
                primary, secondary = ModelMetricName.MACRO_F1_SCORE, None
            case (ModelTier.EDGE, ModelRole.STUDENT):
                primary, secondary = ModelMetricName.ACCURACY, None
            case _:
                return False
        challenger_primary = cls._metric_value(challenger_metrics, primary)
        if challenger_primary is None:
            return False
        if not metrics_to_beat:
            return True
        primary_metric_to_beat = cls._metric_value(metrics_to_beat, primary)
        if primary_metric_to_beat is None:
            return True
        if challenger_primary < primary_metric_to_beat:
            return False
        if challenger_primary > primary_metric_to_beat:
            return True
        if secondary is None:
            return False
        challenger_secondary = cls._metric_value(challenger_metrics, secondary)
        if challenger_secondary is None:
            return False
        secondary_metric_to_beat = cls._metric_value(metrics_to_beat, secondary)
        if secondary_metric_to_beat is None:
            return True
        return challenger_secondary < secondary_metric_to_beat

    @staticmethod
    def _metric_value(
        metrics: List[ModelMetric],
        name: ModelMetricName,
    ) -> Optional[Decimal]:
        preferred = (
            TrainingSplit.HOLDOUT,
            TrainingSplit.TEST,
            TrainingSplit.VALIDATE,
        )
        by_split = {
            metric.split: metric.value for metric in metrics if metric.name is name
        }
        for split in preferred:
            if split in by_split:
                return by_split[split]
        return None

    @classmethod
    def _budget_check(cls, challenger: ModelArtifact, checked_at: datetime) -> bool:
        if (challenger.tier, challenger.role) != (ModelTier.EDGE, ModelRole.STUDENT):
            return True
        if not challenger.id:
            return False
        bytes_per = _BYTES_PER_PARAM.get(challenger.precision, 4)
        kept_sparsity = Decimal("1") - Decimal(str(challenger.sparsity or 0))
        param_count = Decimal(challenger.param_count or 0)
        flash_kb = param_count * Decimal(bytes_per) * kept_sparsity / Decimal("1024")
        peak_ram_kb = flash_kb
        macs = int(param_count * kept_sparsity)
        passed = (
            flash_kb <= _EDGE_FLASH_BUDGET_KB
            and peak_ram_kb <= _EDGE_PEAK_RAM_BUDGET_KB
            and macs <= _EDGE_MACS_BUDGET
        )
        budget = ModelBudget(
            flash_kb=flash_kb,
            flash_budget_kb=_EDGE_FLASH_BUDGET_KB,
            peak_ram_kb=peak_ram_kb,
            peak_ram_budget_kb=_EDGE_PEAK_RAM_BUDGET_KB,
            macs=macs,
            macs_budget=_EDGE_MACS_BUDGET,
            passed=passed,
            checked_at=checked_at,
            artifact_id=challenger.id,
        )
        cls._upsert_budget(budget)
        return passed

    @staticmethod
    def _fetch_challengers(limit: int = MODEL_DB_FETCH_SIZE) -> List[ModelArtifact]:
        rows = db_pool.run(
            SELECT_CHALLENGER_ARTIFACTS,
            (limit,),
            fetch=PoolFetch.ALL,
            error_event="fetch_model_artifacts_failed",
        )
        if not rows:
            logger.warning("fetch_model_artifacts_empty")
            return []
        artifacts: List[ModelArtifact] = []
        for row in rows:
            artifacts.append(
                ModelArtifact(
                    id=row.get("id"),
                    tier=row.get("tier"),
                    role=row.get("role"),
                    stage=row.get("stage"),
                    precision=row.get("precision"),
                    architecture=row.get("architecture"),
                    param_count=row.get("param_count"),
                    sparsity=row.get("sparsity"),
                    storage_path=row.get("storage_path"),
                    signature=row.get("signature"),
                    signed_at=row.get("signed_at"),
                    promoted=row.get("promoted"),
                    promoted_at=row.get("promoted_at"),
                    session_id=row.get("session_id"),
                    parent_id=row.get("parent_id"),
                )
            )
        return artifacts

    @staticmethod
    def _fetch_incumbent(key: Tuple[ModelTier, ModelRole]) -> Optional[ModelArtifact]:
        tier, role = key
        row = db_pool.run(
            SELECT_INCUMBENT_ARTIFACT,
            (tier, role),
            fetch=PoolFetch.ONE,
            error_event="fetch_model_artifact_failed",
        )
        if not row:
            logger.warning("fetch_model_artifact_empty", tier=tier, role=role)
            return None
        return ModelArtifact(
            id=row.get("id"),
            tier=tier,
            role=role,
            stage=row.get("stage"),
            precision=row.get("precision"),
            architecture=row.get("architecture"),
            param_count=row.get("param_count"),
            sparsity=row.get("sparsity"),
            storage_path=row.get("storage_path"),
            signature=row.get("signature"),
            signed_at=row.get("signed_at"),
            promoted=row.get("promoted"),
            promoted_at=row.get("promoted_at"),
            session_id=row.get("session_id"),
            parent_id=row.get("parent_id"),
        )

    @staticmethod
    def _fetch_metrics(
        artifact_id: str, limit: int = MODEL_DB_FETCH_SIZE
    ) -> List[ModelMetric]:
        rows = db_pool.run(
            SELECT_METRICS,
            (artifact_id, limit),
            fetch=PoolFetch.ALL,
            error_event="fetch_model_metrics_failed",
        )
        if not rows:
            logger.warning("fetch_model_metrics_empty")
            return []
        metrics: List[ModelMetric] = []
        for row in rows:
            metrics.append(
                ModelMetric(
                    name=row.get("name"),
                    split=row.get("split"),
                    value=row.get("value"),
                    artifact_id=artifact_id,
                )
            )
        return metrics

    @staticmethod
    def _upsert_artifact(artifact: ModelArtifact) -> None:
        db_pool.run(
            UPSERT_ARTIFACT,
            artifact.prepare_for_storage(include_id=True),
        )

    @staticmethod
    def _upsert_budget(budget: ModelBudget) -> None:
        db_pool.run(
            UPSERT_BUDGET,
            budget.prepare_for_storage(include_id=True),
        )


model_evaluator = _ModelEvaluator()
