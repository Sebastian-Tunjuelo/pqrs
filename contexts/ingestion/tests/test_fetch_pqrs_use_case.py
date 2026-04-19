from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest

from ingestion.application.fetch_pqrs_use_case import FetchPqrsUseCase
from ingestion.domain.raw_pqrs import DataSource, RawPqrs
from ingestion.infrastructure.medata_ckan_client import MedataCkanClient
from ingestion.infrastructure.medata_data_json import MedataDataJsonClient
from ingestion.infrastructure.medata_scraper import MedataScraper


class EmptyDcat(MedataDataJsonClient):
    async def fetch_raw_pqrs(self) -> list[RawPqrs]:
        return []


class FakePublisher:
    def __init__(self) -> None:
        self.published: list[dict] = []

    async def publish(self, stream: str, payload: dict) -> str:
        self.published.append({"stream": stream, "payload": payload})
        return "1-0"


class EmptyScraper(MedataScraper):
    async def fetch_raw_pqrs(self, limit: int = 50) -> list[RawPqrs]:
        return []


@pytest.mark.asyncio
async def test_use_case_publishes_from_ckan() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        body = {
            "success": True,
            "result": {
                "count": 1,
                "results": [
                    {
                        "id": "abc",
                        "notes": "Solicitud de apoyo a emprendimiento",
                        "metadata_created": "2026-01-02T00:00:00Z",
                    }
                ],
            },
        }
        return httpx.Response(200, json=body)

    publisher = FakePublisher()
    ckan_client = MedataCkanClient(
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        page_size=50,
        rate_limit_seconds=0,
    )
    scraper = EmptyScraper(http_client=httpx.AsyncClient())
    use_case = FetchPqrsUseCase(
        ckan_client=ckan_client, scraper=scraper, publisher=publisher, dcat_client=EmptyDcat()
    )

    total = await use_case.execute(since=datetime(2024, 1, 1, tzinfo=UTC))

    assert total == 1
    assert publisher.published[0]["payload"]["event_type"] == "PqrsIngested"
    assert publisher.published[0]["payload"]["source"] == DataSource.MEDATA_API.value


@pytest.mark.asyncio
async def test_use_case_publishes_from_scraper_when_api_fails() -> None:
    def failing_handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"success": False})

    class StubScraper(MedataScraper):
        async def fetch_raw_pqrs(self, limit: int = 50) -> list[RawPqrs]:
            return [
                RawPqrs(
                    id_externo="scrape-1",
                    contenido="PQRS scrape fallback",
                    fecha_radicado=datetime(2026, 2, 1, tzinfo=UTC),
                    source=DataSource.MEDATA_SCRAPE,
                    metadata={"from": "scraper"},
                )
            ]

    publisher = FakePublisher()
    ckan_client = MedataCkanClient(
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(failing_handler))
    )
    use_case = FetchPqrsUseCase(
        ckan_client=ckan_client,
        scraper=StubScraper(http_client=httpx.AsyncClient()),
        publisher=publisher,
        dcat_client=EmptyDcat(),
    )

    total = await use_case.execute(since=datetime(2024, 1, 1, tzinfo=UTC))

    assert total == 1
    assert publisher.published[0]["payload"]["source"] == DataSource.MEDATA_SCRAPE.value


@pytest.mark.asyncio
async def test_use_case_merges_ckan_and_scraper() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        body = {
            "success": True,
            "result": {
                "count": 1,
                "results": [
                    {
                        "id": "ckan-only",
                        "notes": "Dataset PQRS único CKAN",
                        "metadata_created": "2026-03-01T00:00:00Z",
                    }
                ],
            },
        }
        return httpx.Response(200, json=body)

    class StubScraper(MedataScraper):
        async def fetch_raw_pqrs(self, limit: int = 50) -> list[RawPqrs]:
            return [
                RawPqrs(
                    id_externo="scrape-0",
                    contenido="Otro texto desde listado web",
                    fecha_radicado=datetime(2026, 3, 2, tzinfo=UTC),
                    source=DataSource.MEDATA_SCRAPE,
                    metadata={"from": "scraper"},
                )
            ]

    publisher = FakePublisher()
    ckan_client = MedataCkanClient(
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        page_size=50,
        rate_limit_seconds=0,
    )
    use_case = FetchPqrsUseCase(
        ckan_client=ckan_client,
        scraper=StubScraper(http_client=httpx.AsyncClient()),
        publisher=publisher,
        dcat_client=EmptyDcat(),
    )

    total = await use_case.execute(since=datetime(2024, 1, 1, tzinfo=UTC))

    assert total == 2
    sources = {p["payload"]["source"] for p in publisher.published}
    assert sources == {DataSource.MEDATA_API.value, DataSource.MEDATA_SCRAPE.value}
