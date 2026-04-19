"""CLI entrypoint: python -m ingestion.cli fetch --since 2024-01-01."""

from __future__ import annotations

from datetime import UTC, datetime

import typer

from ingestion.application.fetch_pqrs_use_case import FetchPqrsUseCase
from ingestion.infrastructure.medata_ckan_client import MedataCkanClient
from ingestion.infrastructure.medata_scraper import MedataScraper
from ingestion.infrastructure.redis_publisher import RedisEventPublisher

app = typer.Typer(help="Ingestion context CLI.")


@app.command("fetch")
def fetch_command(since: str = "2024-01-01") -> None:
    since_dt = datetime.fromisoformat(f"{since}T00:00:00").replace(tzinfo=UTC)

    async def _run() -> int:
        use_case = FetchPqrsUseCase(
            ckan_client=MedataCkanClient(),
            scraper=MedataScraper(),
            publisher=RedisEventPublisher(),
        )
        return await use_case.execute(since=since_dt)

    import asyncio

    total = asyncio.run(_run())
    typer.echo(
        f"Published {total} PqrsIngested events (CKAN si responde + scrape portal + data.json DCAT, deduplicado)."
    )


if __name__ == "__main__":
    app()
