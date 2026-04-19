from __future__ import annotations

import httpx
import pytest


@pytest.mark.e2e
def test_health_json(api_url: str) -> None:
    r = httpx.get(f"{api_url}/api/v1/health", timeout=10.0)
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") in ("ok", "degraded")
    assert "postgres" in body and "redis" in body and "ollama" in body
