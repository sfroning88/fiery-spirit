"""
Author: Sean Froning
Created Date: 8.26.2026
Model evaluator testing script
"""

from typing import Any, Dict, List

from ..endpoints import (
    ML_PROMOTE_URL,
    endpoint_test,
)


def run_promote_test() -> List[str]:
    """Simulate CRON: POST /api/ml/promote once"""
    print("Model promote reload (CRON simulation) start")

    print(f"\nRunning post-training evaluation")
    response: Dict[str, Any] = endpoint_test(
        ML_PROMOTE_URL,
        name=f"ml_promote",
        payload={},
    )

    evaluated_models = response.get("evaluated_models")
    artifact_ids: List[str] = []
    if evaluated_models:
        for evaluated_model in evaluated_models:
            if evaluated_model.artifact_id:
                artifact_ids.append(evaluated_model.id)
                print(
                    f"artifact_id={evaluated_model.id!r} promoted={evaluated_model.promoted or False}"
                )

    if not evaluated_models:
        print(f"WARNING: evaluator promotion did not evaluate any artifacts")

    print("\nPost-training evaluation complete")
    return artifact_ids
