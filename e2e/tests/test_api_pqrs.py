from __future__ import annotations

import httpx
import pytest


@pytest.mark.e2e
def test_list_pqrs_shape(api_url: str) -> None:
    r = httpx.get(f"{api_url}/api/v1/pqrs?page=1&per_page=5", timeout=15.0)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
