"""
Author: Sean Froning
Created Date: 8.23.2026
Train spawn testing script
"""

from decimal import Decimal
from typing import Any, List
from ..endpoints import TRAIN_URL, endpoint_test
from ..helpers import wait_for_jobs
from ...fiery_python import (
    Transformation,
    TrainingStage,
    TrainingNormalize,
    TrainingDeformation,
    UuidUtils,
)

_JOB_TIMEOUT_SECONDS = 600


def run_train_test() -> None:
    """POST /api/train once against LoRA spawn"""
    print("Train integration endpoint test start")

    print(f"\nAttempting train")

    deformation = TrainingDeformation(
        patch_px=8,
        wrap_rad=Decimal("3.14159"),
        normalize=TrainingNormalize.NONE,
        coherence_min=Decimal("0.300"),
        class_id="ignored-for-hash",
    )
    transform_hash = Transformation.transform_hash(deformation)
    training_contract_id = UuidUtils.deterministic_uuid("deformation", 1)
    dataset_version_id = UuidUtils.deterministic_uuid(
        training_contract_id, transform_hash
    )

    response: Any = endpoint_test(
        TRAIN_URL,
        name=f"train",
        payload={
            "contract_id": training_contract_id,
            "version_id": dataset_version_id,
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
