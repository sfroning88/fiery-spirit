"""
Author: Sean Froning
Created Date: 8.21.2026
Ingest datasets testing script
"""

from typing import Any, Dict, List
from ..endpoints import INGEST_URL, endpoint_test
from ..helpers import wait_for_jobs
from ...fiery_python import TrainingSampleSource

_DEFORMATION_SOURCES = (
    TrainingSampleSource.HEPHAESTUS,
    TrainingSampleSource.OKADA,
)
_MAX_SAMPLES = 20
_JOB_TIMEOUT_SECONDS = 600


def run_ingest_test() -> None:
    """POST /api/ingest once per deformation sample source"""
    print("Ingest integration endpoint test start")

    all_job_ids: List[str] = []
    for source in _DEFORMATION_SOURCES:
        print(f"\nAttempting ingest for source: {source.value}")

        response: Dict[str, Any] = endpoint_test(
            INGEST_URL,
            name=f"ingest_{source.value}",
            payload={"source": source.value, "max_samples": _MAX_SAMPLES},
        )

        job_ids: List[str] = list(response.get("job_ids") or [])
        if not job_ids:
            raise RuntimeError(
                f"Ingest endpoint returned no job_ids for {source.value}"
            )

        print(f"Enqueued {len(job_ids)} ingest job(s) for {source.value}: {job_ids}")
        all_job_ids.extend(job_ids)

    print(f"\nWaiting for {len(all_job_ids)} ingest job(s) to finish...")
    wait_for_jobs(all_job_ids, timeout=_JOB_TIMEOUT_SECONDS)

    print("\nIngest integration testing complete")
