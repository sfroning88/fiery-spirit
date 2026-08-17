"""
Author: Sean Froning
Created Date: 5.9.2026
S3-backed joblib pickle storage for trained models
"""

import hashlib
import hmac
import io
import os
import threading
from typing import Any, Optional
import boto3
import joblib
from botocore.client import (
    Config as BotoConfig,
)
from ..constants import TRAINING_MODEL_BUCKET
from ..core import logging

logger = logging.get_logger(__name__)

_ARTIFACT_HMAC_META_KEY = "artifact-hmac-sha256"


class ModelStorageServices:
    """S3-backed joblib pickle storage shared across training (writer) and inference (reader)"""

    _lock = threading.Lock()
    _client: Optional[Any] = None

    @classmethod
    def _get_client(cls) -> Any:
        """Lazy singleton boto3 client to s3 models"""
        if cls._client is not None:
            return cls._client
        with cls._lock:
            if cls._client is None:
                key_id = os.environ.get("MODELS_BUCKET_KEY_ID")
                key_secret = os.environ.get("MODELS_BUCKET_KEY_SECRET")
                if not key_id or not key_secret:
                    raise RuntimeError("Models bucket credentials not configured")
                cls._client = boto3.client(
                    "s3",
                    endpoint_url=os.environ.get("S3_BUCKET_URL"),
                    region_name=os.environ.get("S3_BUCKET_REGION") or "us-east-1",
                    aws_access_key_id=key_id,
                    aws_secret_access_key=key_secret,
                    config=BotoConfig(
                        signature_version="s3v4", retries={"max_attempts": 3}
                    ),
                )
        return cls._client

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
        """Serialize payload with joblib and upload to s3://{TRAINING_MODEL_BUCKET}/{key}"""
        buf = io.BytesIO()
        joblib.dump(payload, buf)
        body = buf.getvalue()
        sig = cls._artifact_hmac_hex(body)
        cls._get_client().put_object(
            Bucket=TRAINING_MODEL_BUCKET,
            Key=key,
            Body=body,
            ContentType="application/octet-stream",
            Metadata={_ARTIFACT_HMAC_META_KEY: sig},
        )
        logger.info(
            "model_saved", bucket=TRAINING_MODEL_BUCKET, key=key, bytes=len(body)
        )
        return key

    @classmethod
    def load(cls, key: str) -> Any:
        """Download .pkl from bucket, verify HMAC metadata, then deserialize with joblib"""
        obj = cls._get_client().get_object(Bucket=TRAINING_MODEL_BUCKET, Key=key)
        body = obj["Body"].read()
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
