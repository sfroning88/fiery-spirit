"""
Author: Sean Froning
Created Date: 8.17.2026
Train Sklearn testing script
"""

from typing import Any, Dict, List

from ..endpoints import (
    AI_URL,
    SHUFFLE_URL,
    TRAIN_PATH,
    build_testing_url,
    endpoint_test,
)
from ...fiery_python import PREDICTION_TARGETS
from ..helpers import wait_for_jobs


def run_training_tests() -> None:
    """Shuffle snapshots into function groups, then train each prediction type"""
    print("Training integration endpoint test start")

    shuffle_response: Dict[str, Any] = endpoint_test(
        SHUFFLE_URL,
        name="shuffle",
    )

    shuffle_job_id: str = shuffle_response.get("job_id") or ""
    if not shuffle_job_id:
        raise RuntimeError("Shuffle endpoint returned no job_id")

    print(f"Enqueued shuffle job: {shuffle_job_id}")
    wait_for_jobs([shuffle_job_id], timeout=120)

    all_job_ids: List[str] = []
    for prediction_type in PREDICTION_TARGETS.keys():
        print(f"\nAttempting training for prediction type: {prediction_type.value}")

        response: Dict[str, Any] = endpoint_test(
            build_testing_url(prediction_type.value, AI_URL, TRAIN_PATH),
            name=f"train_{prediction_type.value}",
        )

        job_ids: List[str] = list(response.get("job_ids") or [])
        if not job_ids:
            raise RuntimeError(
                f"Training endpoint returned no job_ids for {prediction_type.value}"
            )

        print(
            f"Enqueued {len(job_ids)} training job(s) for {prediction_type.value}: "
            f"{job_ids}"
        )
        all_job_ids.extend(job_ids)

    print(f"\nWaiting for {len(all_job_ids)} training job(s) to finish...")
    wait_for_jobs(all_job_ids, timeout=600)

    print("\nTraining integration testing complete")
