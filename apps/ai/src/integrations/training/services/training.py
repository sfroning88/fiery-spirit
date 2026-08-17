"""
Author: Sean Froning
Modified Date: 5.16.2026
Processing functions for model training
"""

import uuid
from datetime import datetime, timezone
from typing import Tuple
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator
from sklearn.ensemble import (
    GradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.linear_model import (
    LinearRegression,
    Ridge,
    Lasso,
    ElasticNet,
)
from sklearn.svm import SVR
from sklearn.metrics import (
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import (
    GroupKFold,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    StandardScaler,
)
from xgboost import XGBRegressor
from focus_python import logging
from focus_python import (
    FEATURE_COLUMNS,
    MSA_FEATURE_COLUMN,
    STATE_FEATURE_COLUMN,
    ModelStorageServices,
    TRAINING_FEATURE_SCHEMA_VERSION,
    TRAINING_FUNCTION_SPLIT_VERSION,
    TRAINING_SPLIT_SEED,
    TRAINING_MIN_SPLIT_SAMPLES,
    TRAINING_RIDGE_ALPHA,
    TRAINING_LASSO_ALPHA,
    TRAINING_ELASTICNET_L1_RATIO,
    TRAINING_N_ESTIMATORS,
    TRAINING_SVR_KERNEL,
    TRAINING_SVR_C,
    TRAINING_SVR_EPSILON,
    TRAINING_SVR_GAMMA,
    TRAINING_SVR_DEGREE,
    TRAINING_SVR_COEF0,
    TRAINING_SVR_SHRINKING,
    TRAINING_SVR_TOL,
    TRAINING_SVR_CACHE_SIZE,
    TRAINING_SVR_MAX_ITER,
    TRAINING_SVR_SCALER_WITH_MEAN,
    TRAINING_SVR_SCALER_WITH_STD,
    TRAINING_XGB_N_ESTIMATORS,
    TRAINING_XGB_MAX_DEPTH,
    TRAINING_XGB_LEARNING_RATE,
    TRAINING_XGB_MIN_CHILD_WEIGHT,
    TRAINING_XGB_SUBSAMPLE,
    TRAINING_XGB_COLSAMPLE_BYTREE,
    TRAINING_XGB_COLSAMPLE_BYLEVEL,
    TRAINING_XGB_COLSAMPLE_BYNODE,
    TRAINING_XGB_REG_ALPHA,
    TRAINING_XGB_REG_LAMBDA,
    TRAINING_XGB_GAMMA,
    TRAINING_XGB_TREE_METHOD,
    TRAINING_XGB_N_JOBS,
    PredictionType,
    TrainingFunction,
    TrainingBatch,
    TrainingFeature,
    TrainingModel,
    TrainingStatus,
    TrainingType,
)
from ml import Features, ModelPayload, TrainingFrame
from .persist import PersistServices

logger = logging.get_logger(__name__)


class TrainingServices:
    """Operations pertaining to model training"""

    @staticmethod
    def create_batch(
        prediction_type: PredictionType = PredictionType.CONTROLLABLE_PRD,
    ) -> str:
        """Build feature contract + persist seeded training"""
        properties = PersistServices.fetch_properties()
        snapshots = PersistServices.fetch_snapshots()
        if not properties:
            raise ValueError("No properties available for training")
        if not snapshots:
            raise ValueError("No snapshots available for training")

        batch_id = str(uuid.uuid4())
        frame = Features.build_training_dataframe(
            properties, snapshots, prediction_type, TrainingFunction.TRAIN
        )
        if len(frame.X) == 0:
            raise ValueError("No training samples available for batch")
        batch = TrainingServices._build_batch(frame, batch_id, prediction_type)

        PersistServices.seed_batch(batch)
        PersistServices.seed_msa_encodings(batch_id, frame.msa_records)
        logger.info(
            "training_batch_seeded",
            batch=batch_id,
            prediction_type=prediction_type.value,
            target=frame.target,
            samples=batch.samples,
            columns=batch.feature.columns,
        )
        return batch_id

    @staticmethod
    def run_training_job(
        training_type: TrainingType,
        batch_id: str,
        prediction_type: PredictionType = PredictionType.CONTROLLABLE_PRD,
    ) -> None:
        """Train a single sklearn model for the given type + batch"""
        logger.info(
            "training_started",
            type=training_type.value,
            prediction_type=prediction_type.value,
            batch=batch_id,
        )
        try:
            PersistServices.bump_batch_executing(batch_id)
            PersistServices.set_model_executing(training_type, batch_id)

            properties = PersistServices.fetch_properties()
            snapshots = PersistServices.fetch_snapshots()
            frame = Features.build_training_dataframe(
                properties, snapshots, prediction_type, TrainingFunction.TRAIN
            )

            estimator = TrainingServices._build_estimator(training_type)
            model, score, train_score, rmse = TrainingServices._train_and_score(
                estimator, frame.X, frame.y, frame.groups, frame.msa_id, frame.state_id
            )

            validate_score = TrainingServices._score_on_function(
                model,
                properties,
                snapshots,
                prediction_type,
                TrainingFunction.VALIDATE,
                frame.msa_encoding,
                frame.state_encoding,
            )
            logger.info(
                "training_scored",
                type=training_type.value,
                r2=round(score, 4),
                train_r2=round(train_score, 4),
                val_r2=round(validate_score, 4) if validate_score is not None else None,
                rmse=round(rmse, 2),
                samples=len(frame.X),
            )

            storage_path = TrainingServices._save_model(
                TrainingServices._build_storage_payload(
                    model, frame, score, rmse, training_type, batch_id, prediction_type
                ),
                batch_id,
                training_type,
            )
            PersistServices.set_model_completed(
                TrainingModel(
                    type=training_type,
                    batch_id=batch_id,
                    r2_score=score,
                    train_score=train_score,
                    validate_score=validate_score,
                    rmse=rmse,
                    storage_path=storage_path,
                    trained_at=datetime.now(tz=timezone.utc),
                )
            )
        except Exception as err:
            TrainingServices._handle_job_failure(training_type, batch_id, err)
            raise

        try:
            PersistServices.finalize_batch(batch_id)
        except Exception as err:
            logger.error("training_finalize_failed", batch=batch_id, error=str(err))

        logger.info(
            "training_completed",
            type=training_type.value,
            batch=batch_id,
            r2=round(score, 4),
        )

    @staticmethod
    def _build_batch(
        frame: TrainingFrame, batch_id: str, prediction_type: PredictionType
    ) -> TrainingBatch:
        """Construct a seeded TrainingBatch with its feature contract from a TrainingFrame"""
        return TrainingBatch(
            id=batch_id,
            status=TrainingStatus.PENDING,
            samples=len(frame.X),
            split_seed=TRAINING_SPLIT_SEED,
            prediction_type=prediction_type,
            split_version_id=TRAINING_FUNCTION_SPLIT_VERSION,
            feature=TrainingFeature(
                batch_id=batch_id,
                columns=list(FEATURE_COLUMNS),
                target=frame.target,
                schema_version=TRAINING_FEATURE_SCHEMA_VERSION,
            ),
        )

    @staticmethod
    def _build_storage_payload(
        model: BaseEstimator,
        frame: TrainingFrame,
        score: float,
        rmse: float,
        training_type: TrainingType,
        batch_id: str,
        prediction_type: PredictionType,
    ) -> ModelPayload:
        """Construct the artifact payload to be persisted to S3"""
        return ModelPayload(
            model=model,
            msa_encoding=frame.msa_encoding,
            state_encoding=frame.state_encoding,
            global_mean=frame.global_mean,
            feature_columns=list(FEATURE_COLUMNS),
            target_column=frame.target,
            prediction_type=prediction_type.value,
            score=score,
            rmse=rmse,
            samples=len(frame.X),
            trained_at=datetime.now(tz=timezone.utc).isoformat(),
            type=training_type.value,
            batch_id=batch_id,
        )

    @staticmethod
    def _save_model(
        payload: ModelPayload, batch_id: str, training_type: TrainingType
    ) -> str:
        """Serialize and upload a ModelPayload to S3; returns storage path"""
        key = f"{batch_id}/{training_type.value}.pkl"
        return ModelStorageServices.save(payload.to_dict(), key)

    @staticmethod
    def _handle_job_failure(
        training_type: TrainingType, batch_id: str, error: Exception
    ) -> None:
        """Persist model failure and attempt batch finalization after a job error"""
        logger.exception(
            "training_job_failed",
            type=training_type.value,
            batch=batch_id,
            error=str(error),
        )
        try:
            PersistServices.set_model_failed(
                TrainingModel(
                    type=training_type,
                    batch_id=batch_id,
                    error_message=str(error),
                )
            )
        except Exception as inner:
            logger.error(
                "training_failure_persist_failed", batch=batch_id, error=str(inner)
            )
        try:
            PersistServices.finalize_batch(batch_id)
        except Exception as inner:
            logger.error("training_finalize_failed", batch=batch_id, error=str(inner))

    @staticmethod
    def _build_estimator(training_type: TrainingType) -> BaseEstimator:
        """Map TrainingType enum to a fresh sklearn estimator instance"""
        if training_type == TrainingType.LINEAR:
            return LinearRegression()
        if training_type == TrainingType.RIDGE:
            return Ridge(alpha=TRAINING_RIDGE_ALPHA, random_state=TRAINING_SPLIT_SEED)
        if training_type == TrainingType.FOREST:
            return RandomForestRegressor(
                n_estimators=TRAINING_N_ESTIMATORS,
                random_state=TRAINING_SPLIT_SEED,
                n_jobs=-1,
            )
        if training_type == TrainingType.GBM:
            return GradientBoostingRegressor(
                n_estimators=TRAINING_N_ESTIMATORS,
                random_state=TRAINING_SPLIT_SEED,
            )
        if training_type == TrainingType.LASSO:
            return Lasso(
                alpha=TRAINING_LASSO_ALPHA,
                random_state=TRAINING_SPLIT_SEED,
            )
        if training_type == TrainingType.ELASTICNET:
            return ElasticNet(
                alpha=TRAINING_LASSO_ALPHA,
                l1_ratio=TRAINING_ELASTICNET_L1_RATIO,
                random_state=TRAINING_SPLIT_SEED,
            )
        if training_type == TrainingType.SVR:
            return Pipeline(
                [
                    (
                        "scaler",
                        StandardScaler(
                            with_mean=TRAINING_SVR_SCALER_WITH_MEAN,
                            with_std=TRAINING_SVR_SCALER_WITH_STD,
                        ),
                    ),
                    (
                        "svr",
                        SVR(
                            kernel=TRAINING_SVR_KERNEL,
                            degree=TRAINING_SVR_DEGREE,
                            gamma=TRAINING_SVR_GAMMA,
                            coef0=TRAINING_SVR_COEF0,
                            tol=TRAINING_SVR_TOL,
                            C=TRAINING_SVR_C,
                            epsilon=TRAINING_SVR_EPSILON,
                            shrinking=TRAINING_SVR_SHRINKING,
                            cache_size=TRAINING_SVR_CACHE_SIZE,
                            max_iter=TRAINING_SVR_MAX_ITER,
                        ),
                    ),
                ]
            )
        if training_type == TrainingType.XGBOOST:
            return XGBRegressor(
                n_estimators=TRAINING_XGB_N_ESTIMATORS,
                max_depth=TRAINING_XGB_MAX_DEPTH,
                learning_rate=TRAINING_XGB_LEARNING_RATE,
                min_child_weight=TRAINING_XGB_MIN_CHILD_WEIGHT,
                subsample=TRAINING_XGB_SUBSAMPLE,
                colsample_bytree=TRAINING_XGB_COLSAMPLE_BYTREE,
                colsample_bylevel=TRAINING_XGB_COLSAMPLE_BYLEVEL,
                colsample_bynode=TRAINING_XGB_COLSAMPLE_BYNODE,
                reg_alpha=TRAINING_XGB_REG_ALPHA,
                reg_lambda=TRAINING_XGB_REG_LAMBDA,
                gamma=TRAINING_XGB_GAMMA,
                tree_method=TRAINING_XGB_TREE_METHOD,
                random_state=TRAINING_SPLIT_SEED,
                n_jobs=TRAINING_XGB_N_JOBS,
            )
        raise ValueError(f"Unsupported training type: {training_type}")

    @staticmethod
    def _train_and_score(
        estimator: BaseEstimator, X, y, groups, msa_id, state_id
    ) -> Tuple[BaseEstimator, float, float, float]:
        """Group-aware 5-fold CV; returns model + mean test R², mean train R², mean RMSE"""
        n_folds = 5
        if len(X) < TRAINING_MIN_SPLIT_SAMPLES or groups.nunique() < n_folds:
            return TrainingServices._fit_and_score_full(estimator, X, y)

        splitter = GroupKFold(n_splits=n_folds)
        test_scores, train_scores, rmses = [], [], []
        for train_indices, test_indices in splitter.split(X, y, groups=groups):
            X_train = X.iloc[train_indices].copy()
            X_test = X.iloc[test_indices].copy()
            y_train, y_test = y.iloc[train_indices], y.iloc[test_indices]
            fold_mean = float(y_train.mean())

            TrainingServices._apply_fold_target_encoding(
                X_train,
                X_test,
                msa_id,
                train_indices,
                test_indices,
                y_train,
                fold_mean,
                MSA_FEATURE_COLUMN,
            )
            TrainingServices._apply_fold_target_encoding(
                X_train,
                X_test,
                state_id,
                train_indices,
                test_indices,
                y_train,
                fold_mean,
                STATE_FEATURE_COLUMN,
            )

            estimator.fit(X_train, y_train)
            test_scores.append(float(r2_score(y_test, estimator.predict(X_test))))
            train_scores.append(float(r2_score(y_train, estimator.predict(X_train))))
            rmses.append(
                float(np.sqrt(mean_squared_error(y_test, estimator.predict(X_test))))
            )
        estimator.fit(X, y)
        return (
            estimator,
            float(np.mean(test_scores)),
            float(np.mean(train_scores)),
            float(np.mean(rmses)),
        )

    @staticmethod
    def _apply_fold_target_encoding(
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        id_series: pd.Series,
        train_indices,
        test_indices,
        y_train: pd.Series,
        fold_mean: float,
        column: str,
    ) -> None:
        """Compute mean-target encoding from the train split and apply to both halves in-place"""
        ids_train = id_series.iloc[train_indices]
        ids_test = id_series.iloc[test_indices]
        encoding = (
            pd.Series(y_train.values, index=ids_train.values)
            .groupby(level=0)
            .mean()
            .to_dict()
        )
        X_train[column] = ids_train.map(encoding).fillna(fold_mean).values
        X_test[column] = ids_test.map(encoding).fillna(fold_mean).values

    @staticmethod
    def _fit_and_score_full(
        estimator: BaseEstimator, X, y
    ) -> Tuple[BaseEstimator, float, float, float]:
        """Fit on full dataset and score in-sample; used when split is not viable"""
        estimator.fit(X, y)
        predictions = estimator.predict(X)
        score = float(r2_score(y, predictions))
        rmse = float(np.sqrt(mean_squared_error(y, predictions)))
        return estimator, score, score, rmse

    @staticmethod
    def _score_on_function(
        model: BaseEstimator,
        properties,
        snapshots,
        prediction_type: PredictionType,
        function: TrainingFunction,
        msa_encoding,
        state_encoding,
    ) -> float | None:
        """Score a fitted model against a held-out function split; returns None if no data"""
        try:
            frame = Features.build_training_dataframe(
                properties,
                snapshots,
                prediction_type,
                function,
                msa_encoding,
                state_encoding,
            )
            return float(r2_score(frame.y, model.predict(frame.X)))
        except Exception as err:
            logger.warning(
                "training_validation_scoring_failed",
                function=function.value,
                error=str(err),
            )
            return None
