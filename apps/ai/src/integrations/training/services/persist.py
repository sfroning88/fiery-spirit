"""
Author: Sean Froning
Modified Date: 5.16.2026
Processing functions for model persistence
"""

import httpx
from datetime import datetime, timezone
from typing import List
from psycopg2.extras import execute_values
from focus_python import db_pool, logging, config
from focus_python.enums import PoolFetch
from focus_python import NumberUtils
from focus_python import (
    TRAINING_JOBS,
    TRAINING_ERROR_MSG_MAX_LENGTH,
    Property,
    PropertySnapshot,
    TrainingBatch,
    TrainingModel,
    TrainingMSAEncoding,
    TrainingSplit,
    TrainingStatus,
    TrainingType,
    TrainingFunction,
)
from ..queries.fetch_properties import QUERY as FETCH_PROPERTIES
from ..queries.fetch_property_ids import QUERY as FETCH_PROPERTY_IDS
from ..queries.fetch_property_snapshots import QUERY as FETCH_PROPERTY_SNAPSHOTS
from ..queries.bulk_update_snapshot_functions import (
    QUERY as BULK_UPDATE_SNAPSHOT_FUNCTIONS,
)
from ..queries.seed_msa_encoding import QUERY as SEED_MSA_ENCODING
from ..queries.seed_batch import QUERY as SEED_BATCH
from ..queries.seed_feature import QUERY as SEED_FEATURE
from ..queries.seed_model import QUERY as SEED_MODEL
from ..queries.seed_split import QUERY as SEED_SPLIT
from ..queries.set_model_executing import QUERY as SET_MODEL_EXECUTING
from ..queries.bump_batch_executing import QUERY as BUMP_BATCH_EXECUTING
from ..queries.set_model_completed import QUERY as SET_MODEL_COMPLETED
from ..queries.set_model_failed import QUERY as SET_MODEL_FAILED
from ..queries.select_batch_by_id import QUERY as SELECT_BATCH_BY_ID
from ..queries.set_batch_failed import QUERY as SET_BATCH_FAILED
from ..queries.set_batch_winner import QUERY as SET_BATCH_WINNER
from ..queries.set_batch_completed import QUERY as SET_BATCH_COMPLETED

logger = logging.get_logger(__name__)

BACKEND_API_URL: str | None = config.get("BACKEND_API_URL")
AUTH_TOKEN: str | None = config.get("AUTH_TOKEN")

if not BACKEND_API_URL or not AUTH_TOKEN:
    raise RuntimeError("BACKEND_API_URL and AUTH_TOKEN must be configured")


class PersistServices:
    """Database persistence for training batches and runs"""

    @staticmethod
    def fetch_properties() -> List[Property]:
        """Pull all property rows and hydrate Property pydantic models"""
        with db_pool.get_cursor() as cursor:
            queryString = FETCH_PROPERTIES.as_string(cursor)
        rows = db_pool.run(queryString, fetch=PoolFetch.ALL)
        return [Property(**row) for row in rows]

    @staticmethod
    def fetch_snapshots() -> List[PropertySnapshot]:
        """Pull all property_snapshot rows and hydrate PropertySnapshot pydantic models"""
        with db_pool.get_cursor() as cursor:
            queryString = FETCH_PROPERTY_SNAPSHOTS.as_string(cursor)
        rows = db_pool.run(queryString, fetch=PoolFetch.ALL)
        return [PropertySnapshot(**row) for row in rows]

    @staticmethod
    def fetch_property_ids() -> List[str]:
        """Pull distinct property IDs"""
        with db_pool.get_cursor() as cursor:
            queryString = FETCH_PROPERTY_IDS.as_string(cursor)
        rows = db_pool.run(queryString, fetch=PoolFetch.ALL)
        return [row["id"] for row in rows]

    @staticmethod
    def seed_split_with_functions(
        assignments: dict[str, TrainingFunction],
        split: TrainingSplit,
    ) -> None:
        """Atomically bulk-update snapshot functions and upsert the TrainingSplit record"""
        records = [(pid, func.value) for pid, func in assignments.items()]
        if not records:
            logger.warning("bulk_update_records_was_empty")
            return
        with db_pool.get_cursor() as cursor:
            execute_values(
                cursor, BULK_UPDATE_SNAPSHOT_FUNCTIONS.as_string(cursor), records
            )
            cursor.execute(
                SEED_SPLIT.as_string(cursor),
                (
                    split.version,
                    split.train_ratio,
                    split.validate_ratio,
                    split.test_ratio,
                    split.shuffled_at,
                ),
            )

    @staticmethod
    def seed_batch(batch: TrainingBatch) -> None:
        """Insert TrainingBatch + TrainingFeature + pending TrainingModel rows atomically"""
        if not batch.feature:
            raise ValueError("seed_batch requires batch.feature")
        feature = batch.feature
        now = datetime.now(tz=timezone.utc)
        with db_pool.get_cursor() as cursor:
            cursor.execute(
                SEED_BATCH.as_string(cursor),
                (
                    batch.id,
                    TrainingStatus.PENDING.value,
                    batch.samples,
                    batch.split_seed,
                    batch.prediction_type.value,
                    batch.split_version_id,
                ),
            )
            cursor.execute(
                SEED_FEATURE.as_string(cursor),
                (
                    batch.id,
                    feature.columns,
                    feature.target,
                    feature.schema_version,
                ),
            )
            for training_type in TRAINING_JOBS.values():
                cursor.execute(
                    SEED_MODEL.as_string(cursor),
                    (training_type.value, TrainingStatus.PENDING.value, now, batch.id),
                )

    @staticmethod
    def seed_msa_encodings(batch_id: str, records: List[TrainingMSAEncoding]) -> None:
        """Bulk insert MSA mean-target encoding rows for a batch"""
        with db_pool.get_cursor() as cursor:
            for record in records:
                cursor.execute(
                    SEED_MSA_ENCODING.as_string(cursor),
                    (batch_id, record.msa_id, record.mean_target, record.sample_count),
                )

    @staticmethod
    def set_model_executing(training_type: TrainingType, batch_id: str) -> None:
        """Move a pending TrainingModel row into executing state"""
        with db_pool.get_cursor() as cursor:
            queryString = SET_MODEL_EXECUTING.as_string(cursor)
        db_pool.run(
            queryString,
            (TrainingStatus.EXECUTING.value, training_type.value, batch_id),
        )

    @staticmethod
    def bump_batch_executing(batch_id: str) -> None:
        """Move TrainingBatch from pending → executing the first time a worker starts"""
        with db_pool.get_cursor() as cursor:
            queryString = BUMP_BATCH_EXECUTING.as_string(cursor)
        db_pool.run(
            queryString,
            (TrainingStatus.EXECUTING.value, batch_id, TrainingStatus.PENDING.value),
        )

    @staticmethod
    def set_model_completed(model: TrainingModel) -> None:
        """Persist successful training run metrics + storage location"""
        with db_pool.get_cursor() as cursor:
            queryString = SET_MODEL_COMPLETED.as_string(cursor)
        db_pool.run(
            queryString,
            (
                TrainingStatus.COMPLETED.value,
                NumberUtils.clamp_decimal(float(model.r2_score), 6, 4),
                (
                    NumberUtils.clamp_decimal(float(model.train_score), 6, 4)
                    if model.train_score is not None
                    else None
                ),
                (
                    NumberUtils.clamp_decimal(float(model.validate_score), 6, 4)
                    if model.validate_score is not None
                    else None
                ),
                float(model.rmse),
                model.storage_path,
                model.trained_at,
                model.type.value,
                model.batch_id,
            ),
        )

    @staticmethod
    def set_model_failed(model: TrainingModel) -> None:
        """Mark a training run as failed and capture the error for debugging"""
        truncated = (model.error_message or "")[:TRAINING_ERROR_MSG_MAX_LENGTH]
        with db_pool.get_cursor() as cursor:
            queryString = SET_MODEL_FAILED.as_string(cursor)
        db_pool.run(
            queryString,
            (TrainingStatus.FAILED.value, truncated, model.type.value, model.batch_id),
        )

    @staticmethod
    def finalize_batch(batch_id: str) -> None:
        """Resolve batch terminal state + winner based on child model rows"""
        models = PersistServices._fetch_batch_models(batch_id)
        outcome = PersistServices._resolve_batch_outcome(models)

        if outcome == TrainingStatus.FAILED:
            PersistServices._fail_batch(batch_id, models)
            return

        if outcome != TrainingStatus.COMPLETED:
            return

        winner = PersistServices._pick_winner(models)
        PersistServices._complete_batch(batch_id, winner)

    @staticmethod
    def _fetch_batch_models(batch_id: str) -> List[TrainingModel]:
        """Fetch all model rows for a batch and hydrate into TrainingModel objects"""
        with db_pool.get_cursor() as cursor:
            query_string = SELECT_BATCH_BY_ID.as_string(cursor)
        rows = db_pool.run(query_string, (batch_id,), fetch=PoolFetch.ALL)
        return [TrainingModel(**row) for row in rows]

    @staticmethod
    def _resolve_batch_outcome(models: List[TrainingModel]) -> TrainingStatus:
        """Return FAILED if any model failed, COMPLETED if all types completed, EXECUTING otherwise"""
        statuses = {model.status for model in models}
        if TrainingStatus.FAILED in statuses:
            return TrainingStatus.FAILED
        expected_types = {training_type for training_type in TrainingType}
        completed_types = {
            model.type for model in models if model.status == TrainingStatus.COMPLETED
        }
        if expected_types.issubset(completed_types):
            return TrainingStatus.COMPLETED
        return TrainingStatus.EXECUTING

    @staticmethod
    def _pick_winner(models: List[TrainingModel]) -> TrainingModel:
        """Return the completed model with the highest score"""
        return max(
            (model for model in models if model.status == TrainingStatus.COMPLETED),
            key=lambda model: float(model.r2_score or 0),
        )

    @staticmethod
    def _fail_batch(batch_id: str, models: List[TrainingModel]) -> None:
        """Persist FAILED terminal state for a batch and log"""
        statuses = [model.status.value for model in models if model.status]
        with db_pool.get_cursor() as cursor:
            fail_string = SET_BATCH_FAILED.as_string(cursor)
        db_pool.run(
            fail_string,
            (TrainingStatus.FAILED.value, batch_id, TrainingStatus.FAILED.value),
        )
        logger.warning("training_batch_failed", batch=batch_id, statuses=statuses)

    @staticmethod
    def _notify_backend_reload(batch_id: str) -> None:
        """Fire-and-forget POST to backend /api/ml/reload after a new winner is committed"""
        if BACKEND_API_URL is None or AUTH_TOKEN is None:
            logger.warning("notify_backend_reload_skipped_no_config", batch=batch_id)
            return

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{BACKEND_API_URL}/api/ml/reload",
                    headers={
                        "auth-token": AUTH_TOKEN,
                        "Content-Type": "application/json",
                    },
                    json={},
                )
                response.raise_for_status()
                logger.info(
                    "notify_backend_reload_sent",
                    batch=batch_id,
                    status=response.status_code,
                )
        except Exception as err:
            logger.warning(
                "notify_backend_reload_failed", batch=batch_id, error=str(err)
            )

    @staticmethod
    def _complete_batch(batch_id: str, winner: TrainingModel) -> None:
        """Persist winner + COMPLETED terminal state for a batch and log"""
        with db_pool.get_cursor() as cursor:
            cursor.execute(
                SET_BATCH_WINNER.as_string(cursor), (winner.type.value, batch_id)
            )
            cursor.execute(
                SET_BATCH_COMPLETED.as_string(cursor),
                (TrainingStatus.COMPLETED.value, batch_id),
            )
        logger.info(
            "training_batch_completed",
            batch=batch_id,
            winner=winner.type.value,
            score=float(winner.r2_score or 0),
        )
        PersistServices._notify_backend_reload(batch_id)
