"""
Author: Sean Froning
Created Date: 8.23.2026
Processing functions for Train jobs
"""

from typing import Any, Dict, Optional
from fiery_python import config, error
from fiery_python import (
    DatasetVersion,
    ModelTier,
    ModelRole,
    TrainingPrecision,
    TrainingTargetModules,
    TrainingHyperparameterLora,
    TrainingSession,
)


class TrainJobSpec:
    """Build training job Modal kwargs for GPU training"""

    @staticmethod
    def build_lora_job_spec(
        session: TrainingSession,
        version: DatasetVersion,
        modules: TrainingTargetModules,
        lora: TrainingHyperparameterLora,
        nonce: str,
    ) -> Optional[Dict[str, Any]]:
        ai_api_url = config.get_required("ai_api_url")
        if not ai_api_url or not isinstance(ai_api_url, str):
            raise error("AI_API_URL not configured")
        return {
            "session_id": session.id,
            "contract_id": session.contract_id,
            "version_id": session.version_id,
            "signal": session.signal.value,
            "stage": session.stage.value,
            "samples": session.samples,
            "seed": session.seed,
            "git_sha": session.git_sha,
            "shard_prefix": f"{version.contract_id}/{version.transform_hash}/",
            "manifest_path": version.manifest_path,
            "lora": {
                "id": lora.id,
                "rank": lora.rank,
                "alpha": lora.alpha,
                "dropout": lora.dropout,
                "epochs": lora.epochs,
                "learning_rate": lora.learning_rate,
                "target_modules": {
                    "query": modules.query,
                    "key": modules.key,
                    "value": modules.value,
                    "output": modules.output,
                },
            },
            "callback_url": f"{ai_api_url.rstrip('/')}/api/callback/train",
            "nonce": nonce,
            "tier": ModelTier.CLOUD.value,
            "role": ModelRole.SCREENER.value,
            "precision": TrainingPrecision.FP32.value,
        }
