"""
Author: Sean Froning
Created Date: 8.20.2026
Unit tests for ModelStorageServices s3 client
"""

import hashlib
import hmac
import io
from unittest.mock import MagicMock, patch

import joblib
import pytest
from fiery_python import MODEL_BUCKET_NAME, ModelStorageServices

HMAC_META_KEY = "artifact-hmac-sha256"


@pytest.fixture(autouse=True)
def _reset_s3_client():
    previous = ModelStorageServices._client
    ModelStorageServices._client = None
    yield
    ModelStorageServices._client = previous


def test_artifact_hmac_secret_requires_env(monkeypatch):
    monkeypatch.delenv("MODELS_ARTIFACT_HMAC_KEY", raising=False)

    with pytest.raises(RuntimeError, match="MODELS_ARTIFACT_HMAC_KEY"):
        ModelStorageServices._artifact_hmac_secret()


def test_get_client_requires_credentials(monkeypatch):
    monkeypatch.delenv("MODELS_BUCKET_KEY_ID", raising=False)
    monkeypatch.delenv("MODELS_BUCKET_KEY_SECRET", raising=False)

    with pytest.raises(RuntimeError, match="credentials"):
        ModelStorageServices._get_client()


def test_get_client_reuses_singleton(monkeypatch):
    monkeypatch.setenv("MODELS_BUCKET_KEY_ID", "id")
    monkeypatch.setenv("MODELS_BUCKET_KEY_SECRET", "secret")
    monkeypatch.setenv("S3_BUCKET_URL", "https://s3.example")
    fake = MagicMock()

    with patch(
        "fiery_python.services.model_storage.boto3.client", return_value=fake
    ) as boto_client:
        first = ModelStorageServices._get_client()
        second = ModelStorageServices._get_client()

    assert first is fake
    assert second is fake
    boto_client.assert_called_once()


def test_save_uploads_joblib_body_with_hmac_metadata(monkeypatch):
    monkeypatch.setenv("MODELS_ARTIFACT_HMAC_KEY", "unit-secret")
    client = MagicMock()
    payload = {"model": "weights"}

    with patch.object(ModelStorageServices, "_get_client", return_value=client):
        result = ModelStorageServices.save(payload, "cloud/screener/art-1.pkl")

    assert result == "cloud/screener/art-1.pkl"
    kwargs = client.put_object.call_args.kwargs
    assert kwargs["Bucket"] == MODEL_BUCKET_NAME
    assert kwargs["Key"] == "cloud/screener/art-1.pkl"
    assert kwargs["ContentType"] == "application/octet-stream"
    body = kwargs["Body"]
    expected = hmac.new(b"unit-secret", body, hashlib.sha256).hexdigest()
    assert kwargs["Metadata"][HMAC_META_KEY] == expected
    assert joblib.load(io.BytesIO(body)) == payload


def test_load_deserializes_after_hmac_check(monkeypatch):
    monkeypatch.setenv("MODELS_ARTIFACT_HMAC_KEY", "unit-secret")
    payload = {"model": "weights"}
    buf = io.BytesIO()
    joblib.dump(payload, buf)
    body = buf.getvalue()
    sig = hmac.new(b"unit-secret", body, hashlib.sha256).hexdigest()
    client = MagicMock()
    client.get_object.return_value = {
        "Body": io.BytesIO(body),
        "Metadata": {HMAC_META_KEY: sig},
    }

    with patch.object(ModelStorageServices, "_get_client", return_value=client):
        loaded = ModelStorageServices.load("cloud/screener/art-1.pkl")

    assert loaded == payload
    client.get_object.assert_called_once_with(
        Bucket=MODEL_BUCKET_NAME, Key="cloud/screener/art-1.pkl"
    )


def test_load_refuses_missing_hmac_metadata(monkeypatch):
    monkeypatch.setenv("MODELS_ARTIFACT_HMAC_KEY", "unit-secret")
    client = MagicMock()
    client.get_object.return_value = {
        "Body": io.BytesIO(b"pickle"),
        "Metadata": {},
    }

    with patch.object(ModelStorageServices, "_get_client", return_value=client):
        with pytest.raises(RuntimeError, match="missing artifact-hmac-sha256"):
            ModelStorageServices.load("bad.pkl")


def test_load_refuses_hmac_mismatch(monkeypatch):
    monkeypatch.setenv("MODELS_ARTIFACT_HMAC_KEY", "unit-secret")
    buf = io.BytesIO()
    joblib.dump({"model": "weights"}, buf)
    body = buf.getvalue()
    client = MagicMock()
    client.get_object.return_value = {
        "Body": io.BytesIO(body),
        "Metadata": {HMAC_META_KEY: "0" * 64},
    }

    with patch.object(ModelStorageServices, "_get_client", return_value=client):
        with pytest.raises(RuntimeError, match="HMAC verification failed"):
            ModelStorageServices.load("tampered.pkl")
