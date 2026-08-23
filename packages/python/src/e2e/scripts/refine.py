"""
Author: Sean Froning
Created Date: 8.22.2026
Refine shards testing script
"""

from typing import Any, List

from ..endpoints import REFINE_URL, endpoint_test
from ..helpers import wait_for_jobs

_JOB_TIMEOUT_SECONDS = 600

_TRAINING_CONTRACT_ID = ""


def run_refine_test() -> None:
    """POST /api/refine once against R2 shards"""
    print("Refine integration endpoint test start")

    print(f"\nAttempting refine")

    response: Any = endpoint_test(
        REFINE_URL,
        name=f"refine",
        payload={"contract_id": _TRAINING_CONTRACT_ID},
    )

    job_ids: List[str] = list(response.get("job_ids") or [])
    if not job_ids:
        raise RuntimeError(f"Refine endpoint returned no job_ids")

    print(f"Enqueued {len(job_ids)} refine job(s): {job_ids}")

    print(f"\nWaiting for {len(job_ids)} refine job(s) to finish...")
    wait_for_jobs(job_ids, timeout=_JOB_TIMEOUT_SECONDS)

    print("\nRefine integration testing complete")
