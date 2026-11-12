"""
Author: Sean Froning
Created Date: 8.28.2026
Operations pertaining to Train persistence
"""

from typing import Dict, Optional, Tuple, assert_never
from fiery_python import db_pool, logging
from fiery_python import (
    PoolFetch,
    DatasetVersion,
    ModelArtifact,
    TrainingSignal,
    TrainingStage,
    TrainingTargetModules,
    TrainingHyperparameterPretrain,
    TrainingHyperparameterLoraVisual,
    TrainingHyperparameterLoraLanguage,
    TrainingHyperparameterDistill,
    TrainingHyperparameterPrune,
    TrainingHyperparameterQuantize,
    TrainingContract,
    TrainingSession,
    TrainingHyperparameter,
)
from ..queries.select_training_contract import QUERY as SELECT_CONTRACT
from ..queries.select_dataset_version import QUERY as SELECT_VERSION
from ..queries.select_model_artifact import QUERY as SELECT_ARTIFACT
from ..queries.select_hyperparameter_pretrain import QUERY as SELECT_PRETRAIN
from ..queries.select_hyperparameter_lora_visual import QUERY as SELECT_LORA_VISUAL
from ..queries.select_hyperparameter_lora_language import QUERY as SELECT_LORA_LANGUAGE
from ..queries.select_hyperparameter_distill import QUERY as SELECT_DISTILL
from ..queries.select_hyperparameter_prune import QUERY as SELECT_PRUNE
from ..queries.select_hyperparameter_quantize import QUERY as SELECT_QUANTIZE
from ..queries.select_training_session import QUERY as SELECT_SESSION
from ..queries.upsert_target_modules import QUERY as UPSERT_MODULES
from ..queries.upsert_hyperparameter_pretrain import QUERY as UPSERT_PRETRAIN
from ..queries.upsert_hyperparameter_lora_visual import QUERY as UPSERT_LORA_VISUAL
from ..queries.upsert_hyperparameter_lora_language import QUERY as UPSERT_LORA_LANGUAGE
from ..queries.upsert_hyperparameter_distill import QUERY as UPSERT_DISTILL
from ..queries.upsert_hyperparameter_prune import QUERY as UPSERT_PRUNE
from ..queries.upsert_hyperparameter_quantize import QUERY as UPSERT_QUANTIZE
from ..queries.upsert_training_session import QUERY as UPSERT_SESSION

logger = logging.get_logger(__name__)

_MODAL_SPAWNABLE_FUNCTIONS: Dict[TrainingStage, str] = {
    TrainingStage.PRETRAIN: "pretrain_teacher",
    TrainingStage.LORA_VISUAL: "lora_visual_screener",
    TrainingStage.LORA_LANGUAGE: "lora_language_analyst",
    TrainingStage.DISTILL: "distill_student",
    TrainingStage.PRUNE: "prune_student",
    TrainingStage.QUANTIZE: "quantize_student",
}


class TrainPersistService:
    """Configure hyperparams; persist session; select session, version, hyperparams"""

    @staticmethod
    def configure_hyperparameters(
        session: TrainingSession, signal: TrainingSignal
    ) -> None:
        if signal is TrainingSignal.DEFORMATION:
            modules = TrainingTargetModules()
            modules.id = modules.deterministic_id()
            lora_visual = TrainingHyperparameterLoraVisual(target_modules_id=modules.id)
            lora_visual.id = lora_visual.deterministic_id()
            hyperparameters = TrainPersistService.select_lora_visual(lora_visual.id)
            if hyperparameters:
                lora_visual, _modules = hyperparameters
            else:
                TrainPersistService.upsert_lora_visual(lora_visual, modules)
            session.hyperparameter_lora_visual_id = lora_visual.id
        elif signal is TrainingSignal.SEISMIC:
            if session.stage is TrainingStage.PRETRAIN:
                pretrain = TrainingHyperparameterPretrain()
                pretrain.id = pretrain.deterministic_id()
                hyperparameters = TrainPersistService.select_pretrain(pretrain.id)
                if hyperparameters:
                    pretrain = hyperparameters
                else:
                    TrainPersistService.upsert_pretrain(pretrain)
                session.hyperparameter_pretrain_id = pretrain.id
            elif session.stage is TrainingStage.DISTILL:
                distill = TrainingHyperparameterDistill(student_architecture="cnn_tiny")
                distill.id = distill.deterministic_id()
                hyperparameters = TrainPersistService.select_distill(distill.id)
                if hyperparameters:
                    distill = hyperparameters
                else:
                    TrainPersistService.upsert_distill(distill)
                session.hyperparameter_distill_id = distill.id
            elif session.stage is TrainingStage.PRUNE:
                prune = TrainingHyperparameterPrune()
                prune.id = prune.deterministic_id()
                hyperparameters = TrainPersistService.select_prune(prune.id)
                if hyperparameters:
                    prune = hyperparameters
                else:
                    TrainPersistService.upsert_prune(prune)
                session.hyperparameter_prune_id = prune.id
            elif session.stage is TrainingStage.QUANTIZE:
                quantize = TrainingHyperparameterQuantize()
                quantize.id = quantize.deterministic_id()
                hyperparameters = TrainPersistService.select_quantize(quantize.id)
                if hyperparameters:
                    quantize = hyperparameters
                else:
                    TrainPersistService.upsert_quantize(quantize)
                session.hyperparameter_quantize_id = quantize.id
            else:
                assert_never(session.stage)
        elif signal is TrainingSignal.LANGUAGE:
            modules = TrainingTargetModules()
            modules.id = modules.deterministic_id()
            lora_language = TrainingHyperparameterLoraLanguage(
                target_modules_id=modules.id
            )
            lora_language.id = lora_language.deterministic_id()
            hyperparameters = TrainPersistService.select_lora_language(lora_language.id)
            if hyperparameters:
                lora_language, _modules = hyperparameters
            else:
                TrainPersistService.upsert_lora_language(lora_language, modules)
            session.hyperparameter_lora_language_id = lora_language.id
        else:
            assert_never(signal)
        return session

    @staticmethod
    def select_hyperparameters(
        session: TrainingSession,
    ) -> Tuple[Optional[TrainingHyperparameter], str]:
        fn_name = _MODAL_SPAWNABLE_FUNCTIONS[session.stage]
        packed: Optional[TrainingHyperparameter] = None
        match session.stage:
            case TrainingStage.PRETRAIN:
                row = (
                    TrainPersistService.select_pretrain(
                        session.hyperparameter_pretrain_id
                    )
                    if session.hyperparameter_pretrain_id
                    else None
                )
                packed = (row, None, None, None, None, None) if row else None
            case TrainingStage.LORA_VISUAL:
                row = (
                    TrainPersistService.select_lora_visual(
                        session.hyperparameter_lora_visual_id
                    )
                    if session.hyperparameter_lora_visual_id
                    else None
                )
                packed = (None, row, None, None, None, None) if row else None
            case TrainingStage.LORA_LANGUAGE:
                row = (
                    TrainPersistService.select_lora_language(
                        session.hyperparameter_lora_language_id
                    )
                    if session.hyperparameter_lora_language_id
                    else None
                )
                packed = (None, None, row, None, None, None) if row else None
            case TrainingStage.DISTILL:
                row = (
                    TrainPersistService.select_distill(
                        session.hyperparameter_distill_id
                    )
                    if session.hyperparameter_distill_id
                    else None
                )
                packed = (None, None, None, row, None, None) if row else None
            case TrainingStage.PRUNE:
                row = (
                    TrainPersistService.select_prune(session.hyperparameter_prune_id)
                    if session.hyperparameter_prune_id
                    else None
                )
                packed = (None, None, None, None, row, None) if row else None
            case TrainingStage.QUANTIZE:
                row = (
                    TrainPersistService.select_quantize(
                        session.hyperparameter_quantize_id
                    )
                    if session.hyperparameter_quantize_id
                    else None
                )
                packed = (None, None, None, None, None, row) if row else None
            case _:
                assert_never(session.stage)
        return packed, fn_name

    @staticmethod
    def select_contract(contract_id: str) -> Optional[TrainingContract]:
        row = db_pool.run(
            SELECT_CONTRACT,
            (contract_id,),
            fetch=PoolFetch.ONE,
            error_event="fetch_training_contract_failed",
        )
        if not row:
            logger.warning("fetch_training_contract_empty", contract_id=contract_id)
            return None
        return TrainingContract(
            id=row.get("id"),
            signal=row.get("signal"),
            notes=row.get("notes"),
            version=row.get("version"),
            seismic_id=row.get("seismic_id"),
            deformation_id=row.get("deformation_id"),
            language_id=row.get("language_id"),
        )

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
    def select_artifact(artifact_id: str) -> Optional[ModelArtifact]:
        row = db_pool.run(
            SELECT_ARTIFACT,
            (artifact_id,),
            fetch=PoolFetch.ONE,
            error_event="fetch_model_artifact_failed",
        )
        if not row:
            logger.warning("fetch_model_artifact_empty", artifact_id=artifact_id)
            return None
        return ModelArtifact(
            id=artifact_id,
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

    @staticmethod
    def select_pretrain(
        pretrain_id: str,
    ) -> Optional[TrainingHyperparameterPretrain]:
        row = db_pool.run(
            SELECT_PRETRAIN,
            (pretrain_id,),
            fetch=PoolFetch.ONE,
            error_event="fetch_training_hyperparameter_pretrain_failed",
        )
        if not row:
            logger.warning(
                "fetch_training_hyperparameter_pretrain_empty",
                pretrain_id=pretrain_id,
            )
            return None
        return TrainingHyperparameterPretrain(
            id=pretrain_id,
            epochs=row.get("epochs"),
            batch_size=row.get("batch_size"),
            learning_rate=row.get("learning_rate"),
            optimizer=row.get("optimizer"),
            weight_decay=row.get("weight_decay"),
            lr_schedule=row.get("lr_schedule"),
            seed=row.get("seed"),
        )

    @staticmethod
    def select_lora_visual(
        lora_visual_id: str,
    ) -> Optional[Tuple[TrainingHyperparameterLoraVisual, TrainingTargetModules]]:
        row = db_pool.run(
            SELECT_LORA_VISUAL,
            (lora_visual_id,),
            fetch=PoolFetch.ONE,
            error_event="fetch_training_hyperparameter_lora_visual_failed",
        )
        if not row:
            logger.warning(
                "fetch_training_hyperparameter_lora_visual_empty",
                lora_visual_id=lora_visual_id,
            )
            return None
        return TrainingHyperparameterLoraVisual(
            id=lora_visual_id,
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
    def select_lora_language(
        lora_language_id: str,
    ) -> Optional[Tuple[TrainingHyperparameterLoraLanguage, TrainingTargetModules]]:
        row = db_pool.run(
            SELECT_LORA_LANGUAGE,
            (lora_language_id,),
            fetch=PoolFetch.ONE,
            error_event="fetch_training_hyperparameter_lora_language_failed",
        )
        if not row:
            logger.warning(
                "fetch_training_hyperparameter_lora_language_empty",
                lora_language_id=lora_language_id,
            )
            return None
        return TrainingHyperparameterLoraLanguage(
            id=lora_language_id,
            rank=row.get("rank"),
            alpha=row.get("alpha"),
            dropout=row.get("dropout"),
            epochs=row.get("epochs"),
            learning_rate=row.get("learning_rate"),
            gradient_accumulation_steps=row.get("gradient_accumulation_steps"),
            target_modules_id=row.get("target_modules_id"),
        ), TrainingTargetModules(
            id=row.get("target_modules_id"),
            query=row.get("query"),
            key=row.get("key"),
            value=row.get("value"),
            output=row.get("output"),
        )

    @staticmethod
    def select_distill(
        distill_id: str,
    ) -> Optional[TrainingHyperparameterDistill]:
        row = db_pool.run(
            SELECT_DISTILL,
            (distill_id,),
            fetch=PoolFetch.ONE,
            error_event="fetch_training_hyperparameter_distill_failed",
        )
        if not row:
            logger.warning(
                "fetch_training_hyperparameter_distill_empty",
                distill_id=distill_id,
            )
            return None
        return TrainingHyperparameterDistill(
            id=distill_id,
            temperature=row.get("temperature"),
            alpha=row.get("alpha"),
            epochs=row.get("epochs"),
            batch_size=row.get("batch_size"),
            learning_rate=row.get("learning_rate"),
            student_architecture=row.get("student_architecture"),
        )

    @staticmethod
    def select_prune(prune_id: str) -> Optional[TrainingHyperparameterPrune]:
        row = db_pool.run(
            SELECT_PRUNE,
            (prune_id,),
            fetch=PoolFetch.ONE,
            error_event="fetch_training_hyperparameter_prune_failed",
        )
        if not row:
            logger.warning(
                "fetch_training_hyperparameter_prune_empty",
                prune_id=prune_id,
            )
            return None
        return TrainingHyperparameterPrune(
            id=prune_id,
            target_sparsity=row.get("target_sparsity"),
            iterations=row.get("iterations"),
            sparsity_schedule=row.get("sparsity_schedule"),
            finetune_epochs_per_iter=row.get("finetune_epochs_per_iter"),
            pruning_criterion=row.get("pruning_criterion"),
        )

    @staticmethod
    def select_quantize(
        quantize_id: str,
    ) -> Optional[TrainingHyperparameterQuantize]:
        row = db_pool.run(
            SELECT_QUANTIZE,
            (quantize_id,),
            fetch=PoolFetch.ONE,
            error_event="fetch_training_hyperparameter_quantize_failed",
        )
        if not row:
            logger.warning(
                "fetch_training_hyperparameter_quantize_empty",
                quantize_id=quantize_id,
            )
            return None
        return TrainingHyperparameterQuantize(
            id=quantize_id,
            method=row.get("method"),
            precision=row.get("precision"),
            calibration_samples=row.get("calibration_samples"),
            accuracy_drop_threshold=row.get("accuracy_drop_threshold"),
            qat_epochs=row.get("qat_epochs"),
            qat_learning_rate=row.get("qat_learning_rate"),
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
            hyperparameter_lora_visual_id=row.get("hyperparameter_lora_visual_id"),
            hyperparameter_lora_language_id=row.get("hyperparameter_lora_language_id"),
            hyperparameter_distill_id=row.get("hyperparameter_distill_id"),
            hyperparameter_prune_id=row.get("hyperparameter_prune_id"),
            hyperparameter_quantize_id=row.get("hyperparameter_quantize_id"),
            contract_id=row.get("contract_id"),
            version_id=row.get("version_id"),
        )

    @staticmethod
    def upsert_pretrain(pretrain: TrainingHyperparameterPretrain) -> None:
        db_pool.run(
            UPSERT_PRETRAIN,
            pretrain.prepare_for_storage(include_id=True),
        )

    @staticmethod
    def upsert_lora_visual(
        lora_visual: TrainingHyperparameterLoraVisual, modules: TrainingTargetModules
    ) -> None:
        db_pool.run(
            UPSERT_MODULES,
            modules.prepare_for_storage(include_id=True),
        )
        db_pool.run(
            UPSERT_LORA_VISUAL,
            lora_visual.prepare_for_storage(include_id=True),
        )

    @staticmethod
    def upsert_lora_language(
        lora_language: TrainingHyperparameterLoraLanguage,
        modules: TrainingTargetModules,
    ) -> None:
        db_pool.run(
            UPSERT_MODULES,
            modules.prepare_for_storage(include_id=True),
        )
        db_pool.run(
            UPSERT_LORA_LANGUAGE,
            lora_language.prepare_for_storage(include_id=True),
        )

    @staticmethod
    def upsert_distill(distill: TrainingHyperparameterDistill) -> None:
        db_pool.run(
            UPSERT_DISTILL,
            distill.prepare_for_storage(include_id=True),
        )

    @staticmethod
    def upsert_prune(prune: TrainingHyperparameterPrune) -> None:
        db_pool.run(
            UPSERT_PRUNE,
            prune.prepare_for_storage(include_id=True),
        )

    @staticmethod
    def upsert_quantize(quantize: TrainingHyperparameterQuantize) -> None:
        db_pool.run(
            UPSERT_QUANTIZE,
            quantize.prepare_for_storage(include_id=True),
        )

    @staticmethod
    def upsert_session(session: TrainingSession) -> None:
        db_pool.run(
            UPSERT_SESSION,
            session.prepare_for_storage(include_id=True),
        )
