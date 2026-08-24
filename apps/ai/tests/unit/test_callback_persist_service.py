"""
Author: Sean Froning
Created Date: 8.24.2026
Unit tests for CallbackPersistService
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

from fiery_python import (
    MODEL_DB_PAGE_SIZE,
    ModelArtifact,
    ModelMetric,
    ModelMetricName,
    ModelRole,
    ModelTier,
    TrainingPrecision,
    TrainingSplit,
    TrainingStage,
)
from integrations.callback.services.persist_service import CallbackPersistService


def _artifact() -> ModelArtifact:
    return ModelArtifact(
        id="11111111-1111-1111-1111-111111111111",
        tier=ModelTier.CLOUD,
        role=ModelRole.SCREENER,
        stage=TrainingStage.LORA,
        precision=TrainingPrecision.FP32,
        architecture="vit-small",
        param_count=22000000,
        sparsity=Decimal("0"),
        storage_path="cloud/screener/art-1.pkl",
        signature="a" * 64,
        signed_at=datetime(2026, 8, 24, tzinfo=timezone.utc),
        promoted=False,
        session_id="22222222-2222-2222-2222-222222222222",
    )


def test_upsert_artifact_passes_storage_dict():
    artifact = _artifact()
    with patch("integrations.callback.services.persist_service.db_pool.run") as run:
        CallbackPersistService.upsert_artifact(artifact)
    run.assert_called_once()
    params = run.call_args.args[1]
    assert params["id"] == artifact.id
    assert params["tier"] == ModelTier.CLOUD.value
    assert params["role"] == ModelRole.SCREENER.value
    assert params["storage_path"] == "cloud/screener/art-1.pkl"
    assert params["session_id"] == artifact.session_id
    assert params["promoted"] is False


def test_upsert_metrics_execute_values():
    metric = ModelMetric(
        name=ModelMetricName.RECALL,
        split=TrainingSplit.TEST,
        value=Decimal("0.910"),
        artifact_id="11111111-1111-1111-1111-111111111111",
    )
    cursor = MagicMock()
    with (
        patch(
            "integrations.callback.services.persist_service.db_pool.get_cursor"
        ) as get_cursor,
        patch(
            "integrations.callback.services.persist_service.execute_values"
        ) as execute_values,
        patch(
            "integrations.callback.services.persist_service.UPSERT_METRICS.as_string",
            return_value="INSERT",
        ),
        patch(
            "integrations.callback.services.persist_service.UPSERT_METRICS_TEMPLATE.as_string",
            return_value="TEMPLATE",
        ),
    ):
        get_cursor.return_value.__enter__.return_value = cursor
        CallbackPersistService.upsert_metrics([metric])
    execute_values.assert_called_once()
    assert execute_values.call_args.kwargs["page_size"] == MODEL_DB_PAGE_SIZE
    inserted = execute_values.call_args.args[2]
    assert "id" not in inserted[0]
    assert inserted[0]["name"] == ModelMetricName.RECALL.value
    assert inserted[0]["split"] == TrainingSplit.TEST.value
    assert inserted[0]["artifact_id"] == metric.artifact_id
