"""
Author: Sean Froning
Created Date: 8.23.2026
Processing functions for Train spawning
"""

import secrets
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from fiery_python import error, logging
from fiery_python import TrainingStatus, TrainingSession
from .job_spec import TrainJobSpec
from .persist_service import TrainPersistService

logger = logging.get_logger(__name__)


class TrainModalSpawn:
    """Build training job Modal kwargs for GPU training"""

    @classmethod
    def run(cls, session_id: str) -> str:
        """Load session payload and manage session status; return Modal call id"""
        session = TrainPersistService.select_session(session_id)
        if not session:
            raise error("No Training Session found")
        version = TrainPersistService.select_version(session.version_id)
        if not version or version.status is not TrainingStatus.COMPLETED:
            cls._fail_spawn(session, "[system] no dataset version is ready")
            raise error("No Dataset Version found or is ready")
        hyperparameters = TrainPersistService.select_lora(
            session.hyperparameter_lora_id
        )
        if not hyperparameters:
            cls._fail_spawn(session, "[system] no LoRA hyperparameters found")
            raise error("No LoRA Hyperparameters found")
        lora, modules = hyperparameters
        session.status = TrainingStatus.EXECUTING
        session.started_at = datetime.now(timezone.utc)
        TrainPersistService.upsert_session(session)
        nonce = secrets.token_hex(16)
        spec = TrainJobSpec.build_lora_job_spec(session, version, modules, lora, nonce)
        if not spec:
            cls._fail_spawn(session, "[system] no job spec was built")
            raise error("No job spec was built")
        call_id, error_message = cls._spawn_modal_function(spec)
        if not call_id:
            cls._fail_spawn(session, error_message or "[system] uncaught spawn error")
            raise error("Modal spawn failed")
        return call_id

    @staticmethod
    def _spawn_modal_function(
        spec: Dict[str, Any],
    ) -> Tuple[Optional[str], Optional[str]]:
        """Non-blocking spawn; return Modal call id or error_message"""
        try:
            import modal

            fn = modal.Function.from_name("fiery-trainer", "train_deformation")
            call = fn.spawn(spec)
            call_id = getattr(call, "object_id", None) or str(call)
            return call_id, None
        except ImportError:
            logger.warning("import_modal_function_failed")
            return None, "[system] import modal function failed"
        except Exception as err:
            logger.warning("spawn_modal_function_failed", error=str(err))
            return None, str(err)

    @staticmethod
    def _fail_spawn(session: TrainingSession, error_message: str) -> None:
        session.status = TrainingStatus.FAILED
        session.finished_at = datetime.now(timezone.utc)
        session.error_message = error_message
        TrainPersistService.upsert_session(session)
