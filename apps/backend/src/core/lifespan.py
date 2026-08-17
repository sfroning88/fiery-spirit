"""
Author: Sean Froning
Created Date: 8.17.2026
Lifespan events for FastAPI app
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fiery_python import db_pool, logging, queue
from fiery_python import PREDICTION_TARGETS
from ml import model_registry

logger = logging.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    queue.get_connection()
    prediction_types = list(PREDICTION_TARGETS.keys())
    with ThreadPoolExecutor(max_workers=len(prediction_types)) as executor:
        futures = {
            executor.submit(model_registry.load, prediction_type): prediction_type
            for prediction_type in prediction_types
        }
        for future in as_completed(futures):
            prediction_type = futures[future]
            try:
                future.result()
            except Exception as err:
                logger.warning(
                    "warmup_skipped",
                    prediction_type=prediction_type.value,
                    error=str(err),
                )
    app.state.db_pool = db_pool
    app.state.queue = queue
    app.state.model_registry = model_registry

    yield

    logger.info("Application shutdown")
    queue.close()
    db_pool.close()
