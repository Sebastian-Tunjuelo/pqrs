"""Orchestrates API fetch -> fallback scrape -> normalize -> publish event."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

from pydantic import ValidationError
from shared_kernel.events import PqrsIngestedPayload

from ingestion.domain.raw_pqrs import DataSource, RawPqrs
from ingestion.infrastructure.medata_ckan_client import MedataCkanClient
from ingestion.infrastructure.medata_scraper import MedataScraper
from ingestion.infrastructure.redis_publisher import RedisEventPublisher


class FetchPqrsUseCase:
    def __init__(
        self,
        ckan_client: MedataCkanClient,
        scraper: MedataScraper,
        publisher: RedisEventPublisher,
        stream_name: str = "pqrs.events.ingested",
    ) -> None:
        self.ckan_client = ckan_client
        self.scraper = scraper
        self.publisher = publisher
        self.stream_name = stream_name

    async def execute(self, since: datetime | None = None) -> int:
        raw_items = await self._fetch_with_fallback()
        published = 0
        for raw in raw_items:
            if since and raw.fecha_radicado < since:
                continue
            event = self._to_event(raw)
            await self.publisher.publish(self.stream_name, event.model_dump(mode="json"))
            published += 1
        return published

    async def _fetch_with_fallback(self) -> list[RawPqrs]:
        try:
            packages = await self.ckan_client.fetch_all_packages(query="pqrs")
            return [self._normalize_ckan_record(record) for record in packages]
        except Exception:
            return await self.scraper.fetch_raw_pqrs()

    def _normalize_ckan_record(self, record: dict) -> RawPqrs:
        text = (
            record.get("notes")
            or record.get("title")
            or record.get("name")
            or "PQRS sin contenido"
        )
        raw_date = record.get("metadata_created")
        fecha = datetime.fromisoformat(raw_date.replace("Z", "+00:00")) if raw_date else datetime.now(UTC)
        try:
            return RawPqrs(
                id_externo=record.get("id"),
                contenido=text.strip(),
                fecha_radicado=fecha,
                source=DataSource.MEDATA_API,
                metadata={"dataset_name": record.get("name"), "organization": record.get("organization")},
            )
        except ValidationError:
            return RawPqrs(
                id_externo=record.get("id"),
                contenido="PQRS sin contenido",
                fecha_radicado=fecha,
                source=DataSource.MEDATA_API,
                metadata={"normalization_error": True},
            )

    @staticmethod
    def _to_event(raw: RawPqrs) -> PqrsIngestedPayload:
        normalized_text = " ".join(raw.contenido.lower().split())
        content_hash = sha256(normalized_text.encode("utf-8")).hexdigest()
        return PqrsIngestedPayload(
            occurred_at=datetime.now(UTC),
            pqrs_id=str(uuid4()),
            id_externo=raw.id_externo,
            contenido=raw.contenido,
            fecha_radicado=raw.fecha_radicado,
            source=raw.source.value,
            metadata={**raw.metadata, "contenido_hash": content_hash},
        )
