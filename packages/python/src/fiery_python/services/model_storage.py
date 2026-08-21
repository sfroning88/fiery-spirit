"""
Author: Sean Froning
Created Date: 8.20.2026
S3-backed joblib pickle storage for trained models
"""

import hashlib
import hmac
import io
import os
from typing import Any
import joblib
from ..constants import MODEL_BUCKET_NAME
from ..core import logging, models_s3

logger = logging.get_logger(__name__)

_ARTIFACT_HMAC_META_KEY = "artifact-hmac-sha256"


class ModelStorageServices:
    """S3-backed joblib pickle storage shared across training (writer) and inference (reader)"""

    @staticmethod
    def _artifact_hmac_secret() -> bytes:
        raw = os.environ.get("MODELS_ARTIFACT_HMAC_KEY")
        if not raw:
            raise RuntimeError("MODELS_ARTIFACT_HMAC_KEY is not configured")
        return raw.encode("utf-8")

    @classmethod
    def _artifact_hmac_hex(cls, body: bytes) -> str:
        return hmac.new(cls._artifact_hmac_secret(), body, hashlib.sha256).hexdigest()

    @classmethod
    def save(cls, payload: Any, key: str) -> str:
        """Serialize payload with joblib and upload to s3://{MODEL_BUCKET_NAME}/{key}"""
        buf = io.BytesIO()
        joblib.dump(payload, buf)
        body = buf.getvalue()
        sig = cls._artifact_hmac_hex(body)
        models_s3.put_bytes(
            MODEL_BUCKET_NAME,
            key,
            body,
            content_type="application/octet-stream",
            metadata={_ARTIFACT_HMAC_META_KEY: sig},
        )
        logger.info("model_saved", bucket=MODEL_BUCKET_NAME, key=key, bytes=len(body))
        return key

    @classmethod
    def load(cls, key: str) -> Any:
        """Download .pkl from bucket, verify HMAC metadata, then deserialize with joblib"""
        obj = models_s3.get_object(MODEL_BUCKET_NAME, key)
        stream = obj["Body"]
        try:
            body = stream.read()
        finally:
            stream.close()
        meta = obj.get("Metadata") or {}
        expected = meta.get(_ARTIFACT_HMAC_META_KEY)
        if not expected:
            raise RuntimeError(
                f"Model object {key!r} missing {_ARTIFACT_HMAC_META_KEY} metadata; refusing unsafe load",
            )
        computed = cls._artifact_hmac_hex(body)
        if not hmac.compare_digest(expected, computed):
            raise RuntimeError(f"Model artifact HMAC verification failed for {key!r}")
        logger.info("model_loaded", key=key, bytes=len(body))
        return joblib.load(io.BytesIO(body))
