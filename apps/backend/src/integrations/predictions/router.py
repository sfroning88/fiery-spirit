"""
Author: Sean Froning
Created Date: 5.9.2026
Core backend API orchestration
"""

from fastapi import APIRouter, Depends, Request
from focus_python import dependency, error, logging
from focus_python import PredictionType, PrismaPrediction
from .schemas import PredictionRequest, PredictionResponse

logger = logging.get_logger(__name__)

router = APIRouter(
    prefix="/api",
    responses={404: {"description": "Not found"}},
)


predictions_available: bool = False
try:
    from .services import InferenceServices

    predictions_available = True
except ImportError as err:
    predictions_available = False
    logger.error("Failed to import Inference", error=str(err))
except Exception as err:
    predictions_available = False
    logger.error("Failed to boot up Predictions", error=str(err))


@router.post(
    "/predict/{prediction_type}", dependencies=[Depends(dependency.get_token_header)]
)
async def model_predict(
    request: Request, prediction_type: PredictionType, payload: PredictionRequest
) -> PredictionResponse:
    """Retrieve controllable PRD prediction(s) from the latest training batch"""
    if not predictions_available:
        raise error("Predictions service unavailable", status_code=503)

    logging.bind_job_context(property_id=payload.property_id)
    try:
        predictions = InferenceServices.predict(
            property_id=payload.property_id,
            prediction_type=prediction_type,
            multi_enabled=payload.multi_enabled,
        )
        return PredictionResponse(
            predictions=[
                PrismaPrediction.from_prediction(pred) for pred in predictions
            ],
        )
    except ValueError as err:
        logger.warning("model_prediction_rejected", error=str(err))
        raise error(str(err), status_code=404)
    except RuntimeError as err:
        logger.error("model_prediction_unavailable", error=str(err))
        raise error(str(err), status_code=503)
    except Exception as err:
        logger.error("model_prediction_failed", error=str(err))
        raise error("Model prediction failed", status_code=500)
    finally:
        logging.unbind_job_context()
