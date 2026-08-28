"""
Author: Sean Froning
Created Date: 8.28.2026
Core backend API orchestration
"""

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from fiery_python import dependency, error, logging
from fiery_python import ModelTier, ModelRole, BlobStorageServices
from .schemas import (
    InferenceSingleRequest,
    # InferenceBatchRequest,
    InferenceResponse,
)
from .models import InferenceOutcome

logger = logging.get_logger(__name__)

router = APIRouter(
    prefix="/api",
    responses={404: {"description": "Not found"}},
)


inference_available: bool = False
try:
    from .services import InferenceServingWaiter
    from .services import InferencePersistService

    inference_available = True
except ImportError as err:
    inference_available = False
    logger.error("Failed to import Inference", error=str(err))
except Exception as err:
    inference_available = False
    logger.error("Failed to boot up Inferences", error=str(err))


def _run_single(payload: InferenceSingleRequest) -> InferenceResponse:
    key = (payload.tier, payload.role)
    if key != (ModelTier.CLOUD, ModelRole.SCREENER):
        raise NotImplementedError
    interferogram = InferencePersistService.select_interferogram(
        (payload.interferogram_id, payload.volcano_id)
    )
    if not interferogram:
        raise error("No interferogram was found")
    if not interferogram.id:
        interferogram.id = interferogram.deterministic_id()
    if not interferogram.id:
        raise error("Invalid interferogram_id")
    body = BlobStorageServices.get_unrefined(interferogram.storage_path)
    sample = InferencePersistService.load_npz(body)
    inference_deformation, probabilities = InferenceServingWaiter.run(
        key, sample, interferogram.id
    )
    InferencePersistService.upsert_deformation(inference_deformation)
    outcome = InferenceOutcome(
        artifact_id=inference_deformation.artifact_id,
        transform_hash=inference_deformation.transform_hash,
        op_version=inference_deformation.op_version,
        threshold_used=inference_deformation.threshold_used,
        abstention_band=inference_deformation.abstention_band,
        abstained=inference_deformation.abstained,
        abstained_reason=inference_deformation.abstained_reason,
        latency_ms=inference_deformation.latency_ms,
        inferred_at=inference_deformation.inferred_at,
        probabilities=probabilities,
        label=inference_deformation.label,
        score=inference_deformation.score,
        interferogram_id=payload.interferogram_id or interferogram.id,
        volcano_id=payload.volcano_id or interferogram.volcano_id,
    )
    return InferenceResponse(
        results=[outcome],
        artifact_id=outcome.artifact_id,
        transform_hash=outcome.transform_hash,
    )


@router.post("/inference/single", dependencies=[Depends(dependency.get_token_header)])
async def single_inference(
    request: Request, payload: InferenceSingleRequest
) -> InferenceResponse:
    """Retrieve inference from the promoted model (if available)"""
    if not inference_available:
        raise error("Inferences service unavailable", status_code=503)

    if not payload.validate_payload():
        raise error("Payload is malformed", status_code=400)

    logging.bind_job_context(
        volcano_id=(payload.volcano_id or payload.interferogram_id)
    )
    try:
        return await run_in_threadpool(_run_single, payload)
    except error:
        raise
    except NotImplementedError:
        logger.warning("model_inference_unsupported")
        raise error("Only (CLOUD, SCREENER) is supported")
    except ValueError as err:
        logger.warning("model_inference_rejected", error=str(err))
        raise error(str(err), status_code=404)
    except RuntimeError as err:
        logger.error("model_inference_unavailable", error=str(err))
        raise error(str(err), status_code=503)
    except Exception as err:
        logger.error("model_inference_failed", error=str(err))
        raise error("Model inference failed", status_code=500)
    finally:
        logging.unbind_job_context()
