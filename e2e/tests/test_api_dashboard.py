from __future__ import annotations

import httpx
import pytest


@pytest.mark.e2e
def test_dashboard_metricas(api_url: str) -> None:
    r = httpx.get(f"{api_url}/api/v1/dashboard/metricas", timeout=15.0)
    assert r.status_code == 200
    data = r.json()
    assert "total_pqrs" in data
    assert "por_nivel_riesgo" in data
