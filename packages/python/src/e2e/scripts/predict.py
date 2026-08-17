"""
Author: Sean Froning
Modified Date: 5.21.2026
Predict from models testing script
"""

from typing import Any, Dict, List, Optional

from ..endpoints import (
    BACKEND_URL,
    ML_RELOAD_URL,
    PREDICT_PATH,
    build_testing_url,
    endpoint_test,
)
from ...focus_python import PREDICTION_TARGETS, PredictionType, PrismaPredictionType
from ..helpers import PREDICT_PRESET_PATH, load_preset_lines


def _parse_preset(lines: List[str]) -> Dict[str, str]:
    """Parse KEY=VALUE preset lines into a dict (later values win)"""
    out: Dict[str, str] = {}
    for ln in lines:
        if "=" not in ln:
            continue
        key, value = ln.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def run_reload_test(multi_enabled: bool = False) -> Dict[PredictionType, List[str]]:
    """Simulate CRON: POST /api/ml/reload per prediction type and collect model_ids"""
    print("Model registry reload (CRON simulation) start")

    model_ids_by_type: Dict[PredictionType, List[str]] = {}
    for prediction_type in PREDICTION_TARGETS.keys():
        print(f"\nReloading registry for prediction type: {prediction_type.value}")
        response: Dict[str, Any] = endpoint_test(
            ML_RELOAD_URL,
            name=f"ml_reload_{prediction_type.value}",
            payload={
                "prediction_type": prediction_type.value,
                "multi_enabled": multi_enabled,
            },
        )

        model_ids: List[str] = list(response.get("model_ids") or [])
        if not model_ids:
            print(
                f"WARNING: registry reload returned no model_ids for "
                f"{prediction_type.value} — predict step will be skipped"
            )
        else:
            print(
                f"Registry reloaded for {prediction_type.value} with "
                f"{len(model_ids)} model(s): {model_ids}"
            )
        model_ids_by_type[prediction_type] = model_ids

    print("\nModel registry reload complete")
    return model_ids_by_type


def _load_predict_preset() -> tuple[str, bool]:
    """Parse preset and return (property_id, multi_enabled)"""
    preset = _parse_preset(load_preset_lines(PREDICT_PRESET_PATH))
    property_id = preset.get("property_id")
    if not property_id:
        raise RuntimeError(f"property_id missing from {PREDICT_PRESET_PATH}")
    multi_enabled = preset.get("multi_enabled", "false").lower() == "true"
    return property_id, multi_enabled


def run_prediction_tests(
    model_ids_by_type: Optional[Dict[PredictionType, List[str]]] = None,
) -> None:
    """Hit backend /predict/{type} for each loaded target and assert response shape"""
    print("Prediction integration endpoint test start")

    property_id, multi_enabled = _load_predict_preset()
    model_ids_by_type = model_ids_by_type or {}

    attempted = 0
    for prediction_type in PREDICTION_TARGETS.keys():
        model_ids = model_ids_by_type.get(prediction_type) or []
        if not model_ids:
            print(
                f"\nSkipping prediction type {prediction_type.value}: "
                "no models loaded for this target"
            )
            continue

        expected_type = PrismaPredictionType.cast(prediction_type).value
        print(
            f"\nAttempting prediction type: {prediction_type.value} "
            f"(expected response type={expected_type!r})"
        )

        response: Dict[str, Any] = endpoint_test(
            build_testing_url(prediction_type.value, BACKEND_URL, PREDICT_PATH),
            name=f"predict_{prediction_type.value}",
            payload={
                "property_id": property_id,
                "multi_enabled": multi_enabled,
            },
        )

        predictions: List[Dict[str, Any]] = list(response.get("predictions") or [])
        if not predictions:
            raise RuntimeError(
                f"Prediction endpoint returned no predictions for {prediction_type.value}"
            )

        attempted += 1

        if multi_enabled:
            returned_types = {pred.get("modelType") for pred in predictions}
            expected_model_types = set(model_ids)
            missing = sorted(expected_model_types - returned_types)
            if missing:
                print(
                    f"WARNING: multi-model response for {prediction_type.value} "
                    "is missing types listed by registry reload "
                    f"(inference skipped or failed for): {missing}"
                )

        if not multi_enabled and len(predictions) != 1:
            raise RuntimeError(
                f"Expected 1 prediction for {prediction_type.value} (single-winner mode), "
                f"got {len(predictions)}"
            )

        for pred in predictions:
            if pred.get("propertyId") != property_id:
                raise RuntimeError(
                    f"Prediction propertyId mismatch: {pred.get('propertyId')} != {property_id}"
                )
            if pred.get("result") is None:
                raise RuntimeError(f"Prediction missing result: {pred}")
            if pred.get("type") != expected_type:
                raise RuntimeError(
                    f"Prediction type mismatch for {prediction_type.value}: "
                    f"expected {expected_type!r}, got {pred.get('type')!r}"
                )
            if not pred.get("modelType"):
                raise RuntimeError(f"Prediction missing modelType: {pred}")
            if not pred.get("modelBatchId"):
                raise RuntimeError(f"Prediction missing modelBatchId: {pred}")

        print(
            f"Got {len(predictions)} prediction(s) for type {prediction_type.value} "
            f"on property {property_id}"
        )
        for pred in predictions:
            print(f"  - {pred.get('modelType')}: {round(float(pred['result']), 2)}")

    if attempted == 0:
        raise RuntimeError(
            "No prediction types were exercised — reload produced no model_ids for any target"
        )

    print("\nPrediction integration testing complete")
