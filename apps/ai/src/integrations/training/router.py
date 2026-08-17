"""
Author: Sean Froning
Created Date: 5.9.2026
Core AI API orchestration
"""

from fastapi import APIRouter, Depends, Request
from uuid import uuid4
from focus_python import dependency, error, logging, queue, limiter
from focus_python import PredictionType, TRAINING_JOBS
from .schemas import ShuffleRequest, TrainingRequest, ShuffleResponse, TrainingResponse

logger = logging.get_logger(__name__)

router = APIRouter(
    prefix="/api",
    responses={404: {"description": "Not found"}},
)


training_available: bool = False
try:
    from .background import TrainingBackgroundJobs
    from .services import TrainingServices

    training_available = True
except ImportError as err:
    training_available = False
    logger.error("Failed to import Training", error=str(err))
except Exception as err:
    training_available = False
    logger.error("Failed to boot up Training", error=str(err))


@router.post("/shuffle", dependencies=[Depends(dependency.get_token_header)])
@limiter.limit("5/minute")
async def group_shuffle(request: Request, _payload: ShuffleRequest) -> ShuffleResponse:
    """Shuffle snapshots into different TrainingSplit"""
    if not training_available:
        raise error("Training service unavailable", status_code=503)

    job_stamp = uuid4().hex

    try:
        jobs = queue.enqueue_jobs(
            [
                {
                    "func": TrainingBackgroundJobs.background_shuffle_groups,
                    "args": (),
                    "job_id": f"model_shuffling_{job_stamp}",
                    "job_timeout": 3000,
                }
            ]
        )
        return ShuffleResponse(job_id=jobs[0].id)
    except Exception as err:
        logger.error("model_shuffle_enqueue_failed", error=str(err))
        raise error("Model shuffling failed", status_code=500)


@router.post(
    "/train/{prediction_type}", dependencies=[Depends(dependency.get_token_header)]
)
@limiter.limit("3/hour")
async def model_train(
    request: Request, prediction_type: PredictionType, payload: TrainingRequest
) -> TrainingResponse:
    """Train batch of sklearn models by PredictionType"""
    if not training_available:
        raise error("Training service unavailable", status_code=503)

    try:
        batch_id = TrainingServices.create_batch(prediction_type)
    except Exception as err:
        logger.error("training_batch_seed_failed", error=str(err))
        raise error("Model training failed to start", status_code=500)

    try:
        specs = []
        for training_type in TRAINING_JOBS.values():
            specs.append(
                {
                    "func": TrainingBackgroundJobs.background_model_train,
                    "args": (training_type.value, batch_id, prediction_type.value),
                    "job_id": f"model_training_{training_type.value}_{batch_id}",
                    "job_timeout": 6000,
                }
            )
        jobs = queue.enqueue_jobs(specs)
        return TrainingResponse(job_ids=[job.id for job in jobs])
    except Exception as err:
        logger.error("model_training_enqueue_failed", batch=batch_id, error=str(err))
        raise error("Model training failed", status_code=500)
