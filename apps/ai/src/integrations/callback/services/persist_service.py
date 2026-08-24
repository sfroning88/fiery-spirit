"""
Author: Sean Froning
Created Date: 8.24.2026
Operations pertaining to Callback persistence
"""

from psycopg2.extras import execute_values
from typing import List
from fiery_python import db_pool, logging
from fiery_python import (
    MODEL_DB_PAGE_SIZE,
    ModelArtifact,
    ModelMetric,
)
from ..queries.upsert_model_artifact import QUERY as UPSERT_ARTIFACT
from ..queries.upsert_model_metrics import (
    QUERY as UPSERT_METRICS,
    TEMPLATE as UPSERT_METRICS_TEMPLATE,
)

logger = logging.get_logger(__name__)


class CallbackPersistService:
    """Persist artifact, metrics"""

    @staticmethod
    def upsert_artifact(artifact: ModelArtifact) -> None:
        db_pool.run(
            UPSERT_ARTIFACT,
            artifact.prepare_for_storage(include_id=True),
        )

    @staticmethod
    def upsert_metrics(metrics: List[ModelMetric]) -> None:
        insert_values = [
            metric.prepare_for_storage(include_id=False) for metric in metrics
        ]
        with db_pool.get_cursor() as cursor:
            execute_values(
                cursor,
                UPSERT_METRICS.as_string(cursor),
                insert_values,
                template=UPSERT_METRICS_TEMPLATE.as_string(cursor),
                page_size=MODEL_DB_PAGE_SIZE,
            )
