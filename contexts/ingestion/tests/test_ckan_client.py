from __future__ import annotations

import json

import httpx
import pytest

from ingestion.infrastructure.medata_ckan_client import MedataCkanClient


@pytest.mark.asyncio
async def test_package_search_paginates() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        start = int(request.url.params.get("start", "0"))
        calls.append(start)
        results = [{"id": f"id-{start + i}", "notes": "pqrs"} for i in range(2)]
        if start >= 4:
            results = []
        body = {"success": True, "result": {"count": 4, "results": results}}
        return httpx.Response(200, content=json.dumps(body))

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    ckan = MedataCkanClient(http_client=client, page_size=2, rate_limit_seconds=0)
    data = await ckan.fetch_all_packages(query="pqrs")

    assert len(data) == 4
    assert calls == [0, 2]
