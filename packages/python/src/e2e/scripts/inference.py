"""
Author: Sean Froning
Created Date: 8.28.2026
Inference backend testing script
"""

from typing import Any, Dict, Tuple

import requests

from ..endpoints import (
    INFERENCE_SINGLE_URL,
    endpoint_test,
)
from ...fiery_python import (
    MODEL_REGISTRY_SLOTS,
    ModelRole,
    ModelTier,
)

_INFERENCE_INTERFEROGRAM_ID = ""


def run_inference_test() -> Dict[Tuple[ModelTier, ModelRole], Dict[str, Any]]:
    """POST /api/inference/single per (tier, role) registry slot"""
    print("Inference integration endpoint test start")

    if not _INFERENCE_INTERFEROGRAM_ID:
        raise RuntimeError("Set _INFERENCE_INTERFEROGRAM_ID before running inference")

    inferred: Dict[Tuple[ModelTier, ModelRole], Dict[str, Any]] = {}
    for key in MODEL_REGISTRY_SLOTS:
        tier, role = key
        print(f"\nPredicting with ({tier.value}, {role.value})")
        try:
            response: Dict[str, Any] = endpoint_test(
                INFERENCE_SINGLE_URL,
                name=f"inference_single_{tier.value}_{role.value}",
                payload={
                    "tier": tier.value,
                    "role": role.value,
                    "interferogram_id": _INFERENCE_INTERFEROGRAM_ID,
                },
            )
        except requests.HTTPError as err:
            print(
                f"WARNING: inference not ready for ({tier.value}, {role.value}): {err}"
            )
            inferred[key] = {"artifact_id": None, "ready": False}
            continue

        artifact_id = response.get("artifact_id")
        results = response.get("results") or []
        if not artifact_id or not results:
            print(
                f"WARNING: inference returned no prediction for "
                f"({tier.value}, {role.value}) artifact_id={artifact_id!r}"
            )
            inferred[key] = {"artifact_id": artifact_id, "ready": False}
            continue

        print(
            f"Inference complete for ({tier.value}, {role.value}) "
            f"artifact={artifact_id} results={len(results)}"
        )
        inferred[key] = {"artifact_id": artifact_id, "ready": True}

    print("\nInference integration testing complete")
    return inferred
