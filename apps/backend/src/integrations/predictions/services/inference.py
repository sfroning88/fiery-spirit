"""
Author: Sean Froning
Modified Date: 5.21.2026
Processing functions for model inference
"""

from datetime import date
from typing import List, Optional
from focus_python import logging
from focus_python import (
    WINNER_KEY,
    Prediction,
    PredictionType,
    Property,
    TrainingType,
)
from ml import (
    Features,
    model_registry,
)
from .persist import PersistServices

logger = logging.get_logger(__name__)


class InferenceServices:
    """Operations pertaining to model inference"""

    @staticmethod
    def predict(
        property_id: str,
        prediction_type: PredictionType,
        multi_enabled: bool = False,
    ) -> List[Prediction]:
        """Run the latest winning model (or every model in the latest batch) for a property"""
        model_registry.load(
            prediction_type=prediction_type, multi_enabled=multi_enabled
        )
        if not model_registry.is_ready(prediction_type):
            raise RuntimeError("No trained model available")

        prop = PersistServices.fetch_property(property_id)
        if prop is None:
            raise ValueError(f"Property '{property_id}' not found")

        snapshot_reported_at = PersistServices.fetch_latest_snapshot_reported_at(
            property_id
        )
        if snapshot_reported_at is None:
            logger.warning(
                "inference_missing_snapshot_date",
                property_id=property_id,
                detail="Using UTC calendar date for snapshot_date feature",
            )

        if multi_enabled:
            keys = model_registry.loaded_model_types(prediction_type)
            predictions: List[Prediction] = []
            for key in keys:
                try:
                    predictions.append(
                        InferenceServices._run_inference(
                            prop, key, prediction_type, snapshot_reported_at
                        )
                    )
                except Exception as err:
                    logger.warning(
                        "inference_model_failed",
                        property_id=property_id,
                        model_key=key,
                        error=str(err),
                    )
            if not predictions:
                raise RuntimeError("No trained model available")
            return predictions
        return [
            InferenceServices._run_inference(
                prop, WINNER_KEY, prediction_type, snapshot_reported_at
            )
        ]

    @staticmethod
    def _run_inference(
        prop: Property,
        model_key: str,
        prediction_type: PredictionType,
        snapshot_reported_at: Optional[date],
    ) -> Prediction:
        """Single-model inference path: load encoding, build vector, predict, package response"""
        model = model_registry.get(prediction_type, model_key)
        meta = model_registry.get_metadata(prediction_type, model_key)
        msa_encoding = meta.get("msa_encoding")
        if not isinstance(msa_encoding, dict) or not msa_encoding:
            raise RuntimeError(f"Model '{model_key}' missing msa_encoding metadata")
        state_encoding = meta.get("state_encoding")
        if not isinstance(state_encoding, dict) or not state_encoding:
            raise RuntimeError(f"Model '{model_key}' missing state_encoding metadata")
        global_mean = meta.get("global_mean")
        if not isinstance(global_mean, (int, float)):
            raise RuntimeError(f"Model '{model_key}' missing global_mean metadata")

        X = Features.build_predict_vector(
            prop,
            msa_encoding,
            state_encoding,
            float(global_mean),
            snapshot_reported_at,
        )
        nan_cols = X.columns[X.isna().any()].tolist()
        if nan_cols:
            logger.warning(
                "inference_nan_columns",
                property_id=prop.id,
                nan_columns=nan_cols,
                values=X.iloc[0].to_dict(),
            )
        result = float(model.predict(X)[0])

        resolved_type = meta.get("winner_type") or model_key
        logger.info(
            "model_predicted",
            property_id=prop.id,
            model_type=resolved_type,
            batch=meta.get("batch_id"),
            result=round(result, 2),
        )
        return Prediction(
            type=prediction_type,
            result=result,
            model_type=TrainingType(resolved_type),
            model_batch_id=meta.get("batch_id"),
            property_id=prop.id,
        )
