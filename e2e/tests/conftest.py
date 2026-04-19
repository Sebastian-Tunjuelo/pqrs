from __future__ import annotations

import os

import httpx
import pytest


@pytest.fixture(scope="session")
def api_url() -> str:
    base = os.environ.get("E2E_API_URL", "http://127.0.0.1:8080").rstrip("/")
    try:
        r = httpx.get(f"{base}/api/v1/health", timeout=5.0)
        r.raise_for_status()
    except Exception as exc:  # noqa: BLE001 — skip amplio para entornos sin API
        pytest.skip(f"API no disponible en {base}: {exc}")
    return base
