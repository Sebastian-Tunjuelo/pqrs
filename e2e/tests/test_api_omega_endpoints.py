from __future__ import annotations

import httpx
import pytest


@pytest.mark.e2e
def test_pending_validation_list(api_url: str) -> None:
    r = httpx.get(f"{api_url}/api/v1/pqrs/pending-validation?page=1&per_page=3", timeout=15.0)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "total" in data


@pytest.mark.e2e
def test_alertas_list(api_url: str) -> None:
    r = httpx.get(f"{api_url}/api/v1/alertas", timeout=15.0)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.e2e
def test_validate_patch_roundtrip(api_url: str) -> None:
    r0 = httpx.get(f"{api_url}/api/v1/pqrs/pending-validation?page=1&per_page=1", timeout=15.0)
    assert r0.status_code == 200
    items = r0.json().get("items") or []
    if not items:
        pytest.skip("Sin PQRS pendientes de validación en la BD de prueba")
    pid = items[0]["id"]
    r = httpx.patch(
        f"{api_url}/api/v1/pqrs/{pid}/validate",
        json={
            "action": "VALIDATE",
            "officer_id": "e2e-bot",
        },
        timeout=15.0,
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("validation_status") == "VALIDATED"
