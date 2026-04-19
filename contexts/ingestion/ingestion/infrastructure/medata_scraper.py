"""Fallback scraper for MEData pages when CKAN API is unavailable."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
from bs4 import BeautifulSoup

from ingestion.domain.raw_pqrs import DataSource, RawPqrs


class MedataScraper:
    def __init__(
        self,
        datasets_url: str = "https://medata.gov.co/dataset",
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.datasets_url = datasets_url
        self._http = http_client or httpx.AsyncClient(timeout=20)

    async def fetch_raw_pqrs(self, limit: int = 50) -> list[RawPqrs]:
        response = await self._http.get(self.datasets_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        cards = soup.select("article.dataset-content, div.dataset-item, li.dataset-item")
        items: list[RawPqrs] = []

        for idx, card in enumerate(cards[:limit]):
            title = card.select_one("h3, h2, .dataset-heading, a")
            excerpt = card.select_one("p, .notes, .dataset-description")
            title_text = title.get_text(strip=True) if title else "PQRS sin titulo"
            excerpt_text = excerpt.get_text(strip=True) if excerpt else title_text
            items.append(
                RawPqrs(
                    id_externo=f"scrape-{idx}",
                    contenido=excerpt_text,
                    fecha_radicado=datetime.now(UTC),
                    source=DataSource.MEDATA_SCRAPE,
                    metadata={"title": title_text, "scraped": True},
                )
            )
        return items
