"""Async CKAN client for MEData endpoints."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import httpx


class MedataCkanClient:
    def __init__(
        self,
        base_url: str = "https://medata.gov.co/api/3/action",
        page_size: int = 50,
        rate_limit_seconds: float = 0.2,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.page_size = page_size
        self.rate_limit_seconds = rate_limit_seconds
        self._http = http_client or httpx.AsyncClient(timeout=20)

    async def package_show(self, dataset_id: str) -> dict:
        resp = await self._http.get(
            f"{self.base_url}/package_show", params={"id": dataset_id}
        )
        resp.raise_for_status()
        payload = resp.json()
        if not payload.get("success"):
            raise RuntimeError(f"CKAN package_show failed for dataset_id={dataset_id}")
        return payload["result"]

    async def iter_package_search(self, query: str = "pqrs") -> AsyncIterator[dict]:
        start = 0
        while True:
            resp = await self._http.get(
                f"{self.base_url}/package_search",
                params={"q": query, "rows": self.page_size, "start": start},
            )
            resp.raise_for_status()
            payload = resp.json()
            if not payload.get("success"):
                raise RuntimeError("CKAN package_search failed")
            result = payload.get("result", {})
            records = result.get("results", [])
            if not records:
                break
            for record in records:
                yield record
            returned = len(records)
            total = int(result.get("count", 0))
            start += returned
            if start >= total:
                break
            await asyncio.sleep(self.rate_limit_seconds)

    async def fetch_all_packages(self, query: str = "pqrs") -> list[dict]:
        return [item async for item in self.iter_package_search(query=query)]
