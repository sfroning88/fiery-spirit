"""
Author: Sean Froning
Created Date: 8.27.2026
Send callback to apps/ai
"""

import time
import random
from typing import List
from fiery_python import logging
from fiery_python import ModelMetric

logger = logging.get_logger(__name__)

_MAX_CALLBACK_ATTEMPTS = 3


def send_callback(
    spec: dict,
    *,
    storage_path: str,
    signature: str,
    param_count: int,
    architecture: str,
    metrics: List[ModelMetric],
) -> None:
    import hashlib
    import hmac
    import json
    import httpx
    from fiery_python import ModelStorageServices

    callback_url = spec["callback_url"]
    if not callback_url or not isinstance(callback_url, str):
        raise RuntimeError("no_callback_url_in_spec")
    payload = {
        "session_id": spec["session_id"],
        "tier": spec["tier"],
        "role": spec["role"],
        "precision": spec["precision"],
        "storage_path": storage_path,
        "signature": signature,
        "param_count": param_count,
        "architecture": architecture,
        "sparsity": "0",
        "metrics": [metric.model_dump(mode="json") for metric in metrics],
        "nonce": spec.get("nonce") or "",
    }
    canonical = json.dumps(
        {
            "architecture": architecture,
            "nonce": spec.get("nonce") or "",
            "param_count": param_count,
            "precision": spec["precision"],
            "role": spec["role"],
            "session_id": spec["session_id"],
            "signature": signature,
            "sparsity": "0",
            "storage_path": storage_path,
            "tier": spec["tier"],
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    digest = hmac.new(
        ModelStorageServices._artifact_hmac_secret(),
        canonical,
        hashlib.sha256,
    ).hexdigest()
    for attempt in range(_MAX_CALLBACK_ATTEMPTS):
        try:
            response = httpx.post(
                callback_url,
                json=payload,
                headers={"X-Callback-Hmac": digest},
                timeout=30.0,
            )
            response.raise_for_status()
            break
        except Exception as err:
            logger.warning(
                "send_callback_failed",
                spec=spec["session_id"],
                attempt=attempt,
                error=str(err),
            )
            time.sleep(float(random.randint(10, 30)))
