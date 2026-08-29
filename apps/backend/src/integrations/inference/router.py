"""
Author: Sean Froning
Created Date: 8.29.2026
Core backend API orchestration
"""

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from fiery_python import dependency, error, logging
from .schemas import (
    InferenceSingleRequest,
    # InferenceBatchRequest,
    InferenceResponse,
)

logger = logging.get_logger(__name__)

router = APIRouter(
    prefix="/api",
    responses={404: {"description": "Not found"}},
)


inference_available: bool = False
try:
    from .services import InferenceServingOrchestrator

    inference_available = True
except ImportError as err:
    inference_available = False
    logger.error("Failed to import Inference", error=str(err))
except Exception as err:
    inference_available = False
    logger.error("Failed to boot up Inferences", error=str(err))


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
        volcano_id=(
            payload.volcano_id or payload.interferogram_id or payload.seismic_event_id
        )
    )
    try:
        return await run_in_threadpool(InferenceServingOrchestrator.run, payload)
    except error:
        raise
    except NotImplementedError:
        logger.warning("model_inference_unsupported")
        raise error("(CLOUD, SCREENER) / (CLOUD, TEACHER) / (EDGE, STUDENT)")
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
