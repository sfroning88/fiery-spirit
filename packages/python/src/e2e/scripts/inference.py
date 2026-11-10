"""
Author: Sean Froning
Created Date: 8.28.2026
Inference backend testing script
"""

import requests
from typing import Any, Dict, List, Tuple
from ..endpoints import (
    INFERENCE_SINGLE_URL,
    endpoint_test,
)
from ..helpers import (
    random_interferogram_id,
    random_seismic_event_id,
    random_volcano_id,
)
from ...fiery_python import (
    MODEL_REGISTRY_SLOTS,
    ModelRole,
    ModelTier,
    TrainingSignal,
)


def run_inference_test(
    signal: str,
) -> Dict[Tuple[ModelTier, ModelRole], Dict[str, Any]]:
    """POST /api/inference/single per matching registry slot"""
    print("Inference integration endpoint test start")

    print(f"\nAttempting inference signal={signal}")

    if signal not in (
        TrainingSignal.DEFORMATION.value,
        TrainingSignal.SEISMIC.value,
        TrainingSignal.LANGUAGE.value,
    ):
        raise ValueError("inference requires -signal deformation|seismic|language")

    inferred: Dict[Tuple[ModelTier, ModelRole], Dict[str, Any]] = {}
    if signal == TrainingSignal.LANGUAGE.value:
        slots: List[Tuple[ModelTier, ModelRole]] = [
            key
            for key in MODEL_REGISTRY_SLOTS
            if key == (ModelTier.CLOUD, ModelRole.ANALYST)
        ]
        sample_key = "volcano_id"
        sample_id = random_volcano_id()
    elif signal == TrainingSignal.SEISMIC.value:
        slots = [
            key
            for key in MODEL_REGISTRY_SLOTS
            if key
            in (
                (ModelTier.CLOUD, ModelRole.TEACHER),
                (ModelTier.EDGE, ModelRole.STUDENT),
            )
        ]
        sample_key = "seismic_event_id"
        sample_id = random_seismic_event_id()
    else:
        slots = [
            key
            for key in MODEL_REGISTRY_SLOTS
            if key == (ModelTier.CLOUD, ModelRole.SCREENER)
        ]
        sample_key = "interferogram_id"
        sample_id = random_interferogram_id()

    for key in slots:
        tier, role = key
        print(f"\nPredicting with ({tier.value}, {role.value})")
        try:
            response: Dict[str, Any] = endpoint_test(
                INFERENCE_SINGLE_URL,
                name=f"inference_single_{tier.value}_{role.value}",
                payload={
                    "tier": tier.value,
                    "role": role.value,
                    sample_key: sample_id,
                },
            )
        except requests.HTTPError as err:
            print(
                f"WARNING: inference not ready for ({tier.value}, {role.value}): {err}"
            )
            inferred[key] = {"artifact_id": None, "ready": False}
            continue

        artifact_id = response.get("artifact_id")
        result = response.get("result") or {}
        generated_text = (
            result.get("generated_text") if isinstance(result, dict) else None
        )
        ready = bool(artifact_id) and (
            bool(generated_text)
            if signal == TrainingSignal.LANGUAGE.value
            else bool(result)
        )
        if not ready:
            print(
                f"WARNING: inference returned no prediction for "
                f"({tier.value}, {role.value}) artifact_id={artifact_id!r}"
            )
            inferred[key] = {"artifact_id": artifact_id, "ready": False}
            continue

        print(
            f"Inference complete for ({tier.value}, {role.value}) "
            f"artifact={artifact_id} result={result}"
        )
        inferred[key] = {
            "artifact_id": artifact_id,
            "ready": True,
            "generated_text": generated_text,
        }

    print("\nInference integration testing complete")
    return inferred
