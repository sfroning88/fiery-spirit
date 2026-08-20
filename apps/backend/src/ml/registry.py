"""
Author: Sean Froning
Created Date: 8.20.2026
Inference-side cache of trained models
"""

import threading
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple
from fiery_python import db_pool, logging, SyncLazyResource
from fiery_python import (
    PoolFetch,
    MODEL_REGISTRY_SLOTS,
    ModelTier,
    ModelRole,
    TrainingStage,
    TrainingPrecision,
    ModelStorageServices,
)
from .models import LoadedModel, ArtifactRegistry
from .queries.select_promoted_artifact import QUERY as SELECT_PROMOTED_ARTIFACT

logger = logging.get_logger(__name__)


class _RegistrySlot:
    """Per-key cache slot with lazy empty state and explicit invalidation"""

    def __init__(self) -> None:
        self._state = SyncLazyResource(self._empty_registry)

    @staticmethod
    def _empty_registry() -> ArtifactRegistry:
        return ArtifactRegistry(
            model=None,
            metadata=None,
            artifact_id=None,
        )

    def get(self) -> ArtifactRegistry:
        return self._state.get()

    def reset(self) -> None:
        self._state.reset()


class _ModelRegistry:
    """In-memory cache of trained model keyed by (tier, role)"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._slots: Dict[Tuple[ModelTier, ModelRole], _RegistrySlot] = {
            (tier, role): _RegistrySlot() for tier, role in MODEL_REGISTRY_SLOTS
        }

    def _slot(self, key: Tuple[ModelTier, ModelRole]) -> _RegistrySlot:
        slot = self._slots.get(key)
        if slot is None:
            slot = _RegistrySlot()
            self._slots[key] = slot
        return slot

    def load(
        self,
        key: Tuple[ModelTier, ModelRole],
        force: bool = False,
    ) -> None:
        """Pull model into the cache"""
        try:
            tier, role = key
            artifact_id = None
            row = self._fetch_promoted_artifact(key)
            if row:
                artifact_id = str(row.get("id")) if row.get("id") else None
        except Exception as err:
            logger.error("registry_lookup_failed", error=str(err))
            raise RuntimeError(f"Model registry lookup failed: {str(err)}")

        if not artifact_id:
            logger.info("registry_no_promoted_artifact")
            with self._lock:
                self._slot(key).reset()
            return

        with self._lock:
            slot = self._slot(key)
            reg = slot.get()
            already_current = artifact_id == reg.artifact_id
            if not force and already_current:
                logger.debug("registry_already_current", artifact=artifact_id)
                return

            entry, model = self._load_model_entry(row, artifact_id)
            if not entry or not model:
                logger.warning(
                    "registry_load_failed_keeping_cached",
                    tier=tier.value,
                    role=role.value,
                    candidate=artifact_id,
                    cached=reg.artifact_id,
                )
                return

            slot.reset()
            reg = slot.get()
            reg.model = model
            reg.metadata = entry
            reg.artifact_id = artifact_id
            logger.info(
                "registry_loaded",
                artifact=artifact_id,
                tier=tier.value,
                role=role.value,
            )

    def get(self, key: Tuple[ModelTier, ModelRole]) -> Any:
        """Return cached model artifact or raise if missing"""
        with self._lock:
            artifact = self._slot(key).get().model
        if artifact is None:
            tier, role = key
            raise RuntimeError(
                f"Model artifact not loaded for ({tier.value}, {role.value})"
            )
        return artifact

    def get_metadata(self, key: Tuple[ModelTier, ModelRole]) -> Dict[str, Any]:
        """Return cached metadata"""
        with self._lock:
            entry = self._slot(key).get().metadata
        return entry.model_dump() if entry else {}

    def is_ready(self, key: Tuple[ModelTier, ModelRole]) -> bool:
        """True if a promoted artifact is currently cached"""
        with self._lock:
            return self._slot(key).get().model is not None

    def reset(self) -> None:
        """Drop all cached slots so the next load rebuilds from the database"""
        with self._lock:
            for slot in self._slots.values():
                slot.reset()

    def _load_model_entry(
        self, row: Dict[str, Any], artifact_id: str
    ) -> tuple[Optional[LoadedModel], Optional[Any]]:
        """Load one S3 artifact; returns (LoadedModel, artifact) or (None, None) on failure"""
        storage_path = str(row.get("storage_path")) if row.get("storage_path") else None
        if not storage_path:
            logger.error("missing required storage_path")
            return None, None
        try:
            payload = ModelStorageServices.load(storage_path)
        except Exception as err:
            logger.error(
                "registry_load_failed",
                key=storage_path,
                error=str(err),
            )
            return None, None
        entry = LoadedModel(
            tier=ModelTier(row.get("tier")),
            role=ModelRole(row.get("role")),
            stage=TrainingStage(row.get("stage")),
            precision=TrainingPrecision(row.get("precision")),
            architecture=str(row.get("architecture")),
            param_count=int(row.get("param_count")),
            sparsity=Decimal(row.get("sparsity")),
            artifact_id=artifact_id,
            promoted_at=row.get("promoted_at"),
            parent_id=str(row.get("parent_id")) if row.get("parent_id") else None,
        )
        artifact = payload.get("model")
        if artifact is None:
            logger.error(
                "registry_payload_missing_model",
                key=storage_path,
            )
            return None, None
        return entry, artifact

    @staticmethod
    def _fetch_promoted_artifact(
        key: Tuple[ModelTier, ModelRole],
    ) -> Optional[Dict[str, Any]]:
        """Return the promoted artifact or None"""
        tier, role = key
        with db_pool.get_cursor() as cursor:
            query = SELECT_PROMOTED_ARTIFACT.as_string(cursor)
        return db_pool.run(
            query,
            (tier.value, role.value),
            fetch=PoolFetch.ONE,
        )


model_registry = _ModelRegistry()
