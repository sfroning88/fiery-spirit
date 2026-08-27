"""
Author: Sean Froning
Created Date: 8.27.2026
Unit tests for trainer callback
"""

import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fiery_python import (
    ModelMetric,
    ModelMetricName,
    ModelRole,
    ModelTier,
    TrainingPrecision,
    TrainingSplit,
)
from src.callback import send_callback


def _metrics() -> list[ModelMetric]:
    return [
        ModelMetric(
            name=ModelMetricName.RECALL,
            split=TrainingSplit.TEST,
            value=Decimal("0.910"),
            artifact_id="art-1",
        )
    ]


def _spec(**overrides) -> dict:
    data = {
        "session_id": "sess-1",
        "tier": ModelTier.CLOUD.value,
        "role": ModelRole.SCREENER.value,
        "precision": TrainingPrecision.FP32.value,
        "callback_url": "https://ai.example/api/callback/train",
        "nonce": "nonce-1",
    }
    data.update(overrides)
    return data


def test_send_callback_raises_when_url_missing():
    with pytest.raises(RuntimeError, match="no_callback_url_in_spec"):
        send_callback(
            _spec(callback_url=""),
            storage_path="cloud/screener/sess-1.pkl",
            signature="b" * 64,
            param_count=10,
            architecture="vit-small",
            metrics=_metrics(),
        )


def test_send_callback_posts_hmac_header():
    secret = b"unit-secret"
    response = MagicMock()
    canonical = json.dumps(
        {
            "architecture": "vit-small",
            "nonce": "nonce-1",
            "param_count": 10,
            "precision": TrainingPrecision.FP32.value,
            "role": ModelRole.SCREENER.value,
            "session_id": "sess-1",
            "signature": "b" * 64,
            "sparsity": "0",
            "storage_path": "cloud/screener/sess-1.pkl",
            "tier": ModelTier.CLOUD.value,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    digest = hmac.new(secret, canonical, hashlib.sha256).hexdigest()
    with (
        patch(
            "fiery_python.ModelStorageServices._artifact_hmac_secret",
            return_value=secret,
        ),
        patch("httpx.post", return_value=response) as post,
    ):
        send_callback(
            _spec(),
            storage_path="cloud/screener/sess-1.pkl",
            signature="b" * 64,
            param_count=10,
            architecture="vit-small",
            metrics=_metrics(),
        )
    post.assert_called_once()
    kwargs = post.call_args.kwargs
    assert kwargs["headers"]["X-Callback-Hmac"] == digest
    assert kwargs["json"]["session_id"] == "sess-1"
    assert kwargs["json"]["storage_path"] == "cloud/screener/sess-1.pkl"
    response.raise_for_status.assert_called_once()


def test_send_callback_retries_then_succeeds():
    secret = b"unit-secret"
    failed = MagicMock()
    failed.raise_for_status.side_effect = RuntimeError("down")
    ok = MagicMock()
    with (
        patch(
            "fiery_python.ModelStorageServices._artifact_hmac_secret",
            return_value=secret,
        ),
        patch("httpx.post", side_effect=[failed, ok]) as post,
        patch("src.callback.time.sleep") as sleep,
    ):
        send_callback(
            _spec(),
            storage_path="cloud/screener/sess-1.pkl",
            signature="b" * 64,
            param_count=10,
            architecture="vit-small",
            metrics=_metrics(),
        )
    assert post.call_count == 2
    sleep.assert_called_once()
    ok.raise_for_status.assert_called_once()
