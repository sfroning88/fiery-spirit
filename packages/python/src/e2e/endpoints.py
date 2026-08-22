"""
Author: Sean Froning
Created Date: 8.21.2026
Centralized route registry and endpoint test factories
"""

import time as Time
from typing import Any, Dict, Optional

import requests

WORKER_PORTS = {
    "backend": 8000,
    "ai": 8001,
}
AUTH_TOKEN = "supersecretpassword"
HEADERS = {"auth-token": AUTH_TOKEN, "Content-Type": "application/json"}

REQUEST_TIMEOUT = (10, 30)


def worker_url(domain: str) -> str:
    """Return localhost URL for the given worker domain"""
    port = WORKER_PORTS.get(domain)
    if port is None:
        raise ValueError(f"Unknown worker domain: {domain}")
    return f"http://localhost:{port}"


BACKEND_URL = worker_url("backend")
AI_URL = worker_url("ai")

# -- Ingest (served by apps/ai) --
INGEST_PATH = "/api/ingest"
INGEST_URL = f"{AI_URL}{INGEST_PATH}"


# -- Model registry (served by apps/backend) --
ML_PATH = "/api/ml"
ML_RELOAD_PATH = f"{ML_PATH}/reload"
ML_RELOAD_URL = f"{BACKEND_URL}{ML_RELOAD_PATH}"


def endpoint_test(
    url: str,
    name: str,
    *,
    method: str = "POST",
    payload: Optional[dict] = None,
    params: Optional[dict] = None,
    extract: Optional[str] = None,
) -> Any:
    """Fire an API endpoint, check success, return extracted field or full data dict"""
    print(f"\n**{name}** {method} {url}")
    if method.upper() == "GET":
        response = requests.get(
            url, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT
        )
    else:
        response = requests.request(
            method,
            url,
            headers=HEADERS,
            json=payload or {},
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
    Time.sleep(1)
    response.raise_for_status()
    data: Dict[str, Any] = response.json()
    if data.get("success") is False:
        raise RuntimeError(f"{name} rejected: {data.get('message')}")
    if extract:
        value = data.get(extract)
        if value is not None:
            print(f"{name} -> {extract}={value}")
        return value
    return data
