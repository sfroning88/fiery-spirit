"""
Author: Sean Froning
Created Date: 8.22.2026
Background functions for Refine
"""

from fiery_python import logging
from .services import RefineShardWriter

logger = logging.get_logger(__name__)


class RefineBackgroundJobs:
    """Operations for background jobs from Refine"""

    @staticmethod
    def background_refine_shards(contract_id: str, version_id: str) -> None:
        """Background: Refine shards from storage"""
        logging.bind_job_context(session_id=contract_id)
        try:
            sample_count = RefineShardWriter.run(contract_id, version_id)
            logger.info(
                "refine_shards_job_completed",
                contract_id=contract_id,
                version_id=version_id,
                sample_count=sample_count,
            )
        except Exception as err:
            logger.error(
                "refine_shards_job_failed",
                contract_id=contract_id,
                version_id=version_id,
                error=str(err),
            )
            raise
        finally:
            logging.unbind_job_context()
