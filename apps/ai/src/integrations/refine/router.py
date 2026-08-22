"""
Author: Sean Froning
Created Date: 8.22.2026
Core AI API orchestration
"""

from fastapi import APIRouter, Depends, Request
from fiery_python import (
    dependency,
    error,
    logging,
    queue,
    limiter,
)
from fiery_python import (
    TrainingStatus,
    DatasetVersion,
    Transformation,
    BlobStorageServices,
)
from .schemas import RefineRequest, RefineResponse

logger = logging.get_logger(__name__)

router = APIRouter(
    prefix="/api",
    responses={404: {"description": "Not found"}},
)


refine_available: bool = False
try:
    from .background import RefineBackgroundJobs
    from .services import RefinePersistService

    refine_available = True
except ImportError as err:
    refine_available = False
    logger.error("Failed to import Refine", error=str(err))
except Exception as err:
    refine_available = False
    logger.error("Failed to boot up Refine", error=str(err))


@router.post("/refine", dependencies=[Depends(dependency.get_token_header)])
@limiter.limit("3/hour")
async def refine_shards(request: Request, payload: RefineRequest) -> RefineResponse:
    """Refine dataset shards"""
    if not refine_available:
        raise error("Refine service unavailable", status_code=503)

    try:
        deformation = RefinePersistService.select_deformation(payload.contract_id)
        if not deformation:
            logger.error(
                "fetch_deformation_failed",
                contract_id=payload.contract_id,
            )
            raise error("Fetch deformation failed", status_code=500)

        transform_hash = Transformation.transform_hash(deformation)

        version = RefinePersistService.select_version(
            payload.contract_id, transform_hash
        )

        if version and version.status is TrainingStatus.COMPLETED:
            return RefineResponse(
                job_ids=[],
                version_id=version.id,
                transform_hash=transform_hash,
                cached=True,
            )

        if version and version.status in (
            TrainingStatus.PENDING,
            TrainingStatus.EXECUTING,
        ):
            return RefineResponse(
                job_ids=[],
                version_id=version.id,
                transform_hash=transform_hash,
                cached=False,
            )

        if not version:
            manifest_path = BlobStorageServices._manifest_key(
                payload.contract_id, transform_hash
            )
            version = DatasetVersion(
                transform_hash=transform_hash,
                manifest_path=manifest_path,
                shard_count=0,
                sample_count=0,
                status=TrainingStatus.EXECUTING,
                contract_id=payload.contract_id,
            )
            version.id = version.deterministic_id()
            RefinePersistService.upsert_version(version)
        elif version.status is TrainingStatus.FAILED:
            version.status = TrainingStatus.PENDING
            RefinePersistService.upsert_version(version)

        specs = [
            {
                "func": RefineBackgroundJobs.background_refine_shards,
                "args": (payload.contract_id, version.id),
                "job_id": f"refine_source_{payload.contract_id}_{version.id}",
                "job_timeout": 6000,
            }
        ]
        jobs = queue.enqueue_jobs(specs)
        return RefineResponse(
            job_ids=[job.id for job in jobs],
            version_id=version.id,
            transform_hash=transform_hash,
            cached=False,
        )

    except Exception as err:
        logger.error(
            "refine_source_enqueue_failed",
            contract_id=payload.contract_id,
            error=str(err),
        )
        raise error("Refine source failed", status_code=500)
