"""
Author: Sean Froning
Created Date: 8.23.2026
Operations pertaining to Train persistence
"""

from typing import Optional, Tuple
from fiery_python import db_pool, logging
from fiery_python import (
    PoolFetch,
    DatasetVersion,
    TrainingTargetModules,
    TrainingHyperparameterLora,
    TrainingSession,
)
from ..queries.select_dataset_version import QUERY as SELECT_VERSION
from ..queries.select_hyperparameter_lora import QUERY as SELECT_LORA
from ..queries.select_training_session import QUERY as SELECT_SESSION
from ..queries.upsert_target_modules import QUERY as UPSERT_MODULES
from ..queries.upsert_hyperparameter_lora import QUERY as UPSERT_LORA
from ..queries.upsert_training_session import QUERY as UPSERT_SESSION

logger = logging.get_logger(__name__)


class TrainPersistService:
    """Persist session; select session, version, hyperparameters"""

    @staticmethod
    def select_version(version_id: str) -> Optional[DatasetVersion]:
        row = db_pool.run(
            SELECT_VERSION,
            (version_id,),
            fetch=PoolFetch.ONE,
            error_event="fetch_dataset_version_failed",
        )
        if not row:
            logger.warning("fetch_dataset_version_empty", version_id=version_id)
            return None
        return DatasetVersion(
            id=version_id,
            transform_hash=row.get("transform_hash"),
            manifest_path=row.get("manifest_path"),
            shard_count=row.get("shard_count"),
            sample_count=row.get("sample_count"),
            status=row.get("status"),
            contract_id=row.get("contract_id"),
        )

    @staticmethod
    def select_lora(
        lora_id: str,
    ) -> Optional[Tuple[TrainingHyperparameterLora, TrainingTargetModules]]:
        row = db_pool.run(
            SELECT_LORA,
            (lora_id,),
            fetch=PoolFetch.ONE,
            error_event="fetch_training_hyperparameter_lora_failed",
        )
        if not row:
            logger.warning("fetch_training_hyperparameter_lora_empty", lora_id=lora_id)
            return None
        return TrainingHyperparameterLora(
            id=lora_id,
            rank=row.get("rank"),
            alpha=row.get("alpha"),
            dropout=row.get("dropout"),
            epochs=row.get("epochs"),
            learning_rate=row.get("learning_rate"),
            target_modules_id=row.get("target_modules_id"),
        ), TrainingTargetModules(
            id=row.get("target_modules_id"),
            query=row.get("query"),
            key=row.get("key"),
            value=row.get("value"),
            output=row.get("output"),
        )

    @staticmethod
    def select_session(session_id: str) -> Optional[TrainingSession]:
        row = db_pool.run(
            SELECT_SESSION,
            (session_id,),
            fetch=PoolFetch.ONE,
            error_event="fetch_training_session_failed",
        )
        if not row:
            logger.warning("fetch_training_session_empty", session_id=session_id)
            return None
        return TrainingSession(
            id=session_id,
            signal=row.get("signal"),
            stage=row.get("stage"),
            status=row.get("status"),
            samples=row.get("samples"),
            seed=row.get("seed"),
            git_sha=row.get("git_sha"),
            git_url=row.get("git_url"),
            started_at=row.get("started_at"),
            finished_at=row.get("finished_at"),
            error_message=row.get("error_message"),
            hyperparameter_pretrain_id=row.get("hyperparameter_pretrain_id"),
            hyperparameter_lora_id=row.get("hyperparameter_lora_id"),
            hyperparameter_distill_id=row.get("hyperparameter_distill_id"),
            hyperparameter_prune_id=row.get("hyperparameter_prune_id"),
            hyperparameter_quantize_id=row.get("hyperparameter_quantize_id"),
            contract_id=row.get("contract_id"),
            version_id=row.get("version_id"),
        )

    @staticmethod
    def upsert_lora(
        lora: TrainingHyperparameterLora, modules: TrainingTargetModules
    ) -> None:
        db_pool.run(
            UPSERT_MODULES,
            modules.prepare_for_storage(include_id=True),
        )
        db_pool.run(
            UPSERT_LORA,
            lora.prepare_for_storage(include_id=True),
        )

    @staticmethod
    def upsert_session(session: TrainingSession) -> None:
        db_pool.run(
            UPSERT_SESSION,
            session.prepare_for_storage(include_id=True),
        )
