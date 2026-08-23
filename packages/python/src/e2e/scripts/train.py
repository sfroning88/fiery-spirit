"""
Author: Sean Froning
Created Date: 8.23.2026
Train spawn testing script
"""

from typing import Any, List

from ...fiery_python import TrainingStage

from ..endpoints import TRAIN_URL, endpoint_test
from ..helpers import wait_for_jobs

_JOB_TIMEOUT_SECONDS = 600

_TRAINING_CONTRACT_ID = ""
_TRAINING_VERSION_ID = ""


def run_train_test() -> None:
    """POST /api/train once against LoRA spawn"""
    print("Train integration endpoint test start")

    print(f"\nAttempting train")

    response: Any = endpoint_test(
        TRAIN_URL,
        name=f"train",
        payload={
            "contract_id": _TRAINING_CONTRACT_ID,
            "version_id": _TRAINING_VERSION_ID,
            "stage": TrainingStage.LORA,
        },
    )

    job_ids: List[str] = list(response.get("job_ids") or [])
    if not job_ids:
        raise RuntimeError(f"Train endpoint returned no job_ids")

    print(f"Enqueued {len(job_ids)} train job(s): {job_ids}")

    print(f"\nWaiting for {len(job_ids)} train job(s) to finish...")
    wait_for_jobs(job_ids, timeout=_JOB_TIMEOUT_SECONDS)

    print("\nTrain integration testing complete")
