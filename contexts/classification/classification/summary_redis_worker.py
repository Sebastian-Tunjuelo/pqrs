"""Worker: consume Redis Stream `pqrs.summary.jobs`, genera síntesis y persiste en Postgres.

Ejecutar (con Redis, Postgres, Ollama):
  pip install -e \"contexts/classification[worker]\"
  DATABASE_URL=postgresql://pqrs:pqrs@localhost:5433/pqrs \\
  REDIS_URL=redis://localhost:6379/0 \\
  python -m classification.summary_redis_worker
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

import psycopg
from redis import asyncio as redis

from classification.application.summary_agent import SummaryAgent

logger = logging.getLogger(__name__)

STREAM_JOBS = "pqrs.summary.jobs"
RESULT_PREFIX = "pqrs:summary:result:"


def _db_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://pqrs:pqrs@localhost:5433/pqrs?sslmode=disable",
    )


def _load_contenido(pqrs_id: str) -> str | None:
    with psycopg.connect(_db_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT contenido FROM pqrs WHERE id = %s::uuid",
                (pqrs_id,),
            )
            row = cur.fetchone()
            return row[0] if row else None


def _save_summary(pqrs_id: str, lead: str, temas: list[str], ejecutivo: str) -> None:
    topics_json = json.dumps(temas, ensure_ascii=False)
    with psycopg.connect(_db_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE pqrs
                SET summary_lead = %s,
                    summary_topics = %s::jsonb,
                    summary_executive = %s,
                    updated_at = NOW()
                WHERE id = %s::uuid
                """,
                (lead, topics_json, ejecutivo, pqrs_id),
            )
        conn.commit()


async def _process_one(
    r: redis.Redis,
    agent: SummaryAgent,
    pqrs_id: str,
    correlation_id: str,
) -> None:
    contenido = await asyncio.to_thread(_load_contenido, pqrs_id)
    if contenido is None:
        logger.warning("PQRS no encontrada id=%s", pqrs_id)
        await r.setex(
            f"{RESULT_PREFIX}{correlation_id}",
            120,
            json.dumps({"error": "pqrs_not_found"}),
        )
        return

    try:
        out = await agent.execute(contenido)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Fallo SummaryAgent pqrs_id=%s", pqrs_id)
        await r.setex(
            f"{RESULT_PREFIX}{correlation_id}",
            120,
            json.dumps({"error": str(exc)}),
        )
        return

    await asyncio.to_thread(
        _save_summary,
        pqrs_id,
        out.lead,
        out.temas,
        out.resumen_ejecutivo,
    )

    await r.setex(
        f"{RESULT_PREFIX}{correlation_id}",
        120,
        json.dumps({"ok": True, "pqrs_id": pqrs_id}),
    )
    logger.info("Síntesis guardada pqrs_id=%s corr=%s", pqrs_id, correlation_id)


async def run_worker(redis_url: str | None = None) -> None:
    logging.basicConfig(level=logging.INFO)
    url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    r = redis.from_url(url, decode_responses=True)
    agent = SummaryAgent()
    last_id = "0-0"
    logger.info("summary_redis_worker escuchando stream=%s", STREAM_JOBS)
    while True:
        resp = await r.xread({STREAM_JOBS: last_id}, count=1, block=10_000)
        if not resp:
            continue
        for _name, messages in resp:
            for msg_id, fields in messages:
                last_id = msg_id
                pqrs_id = (fields or {}).get("pqrs_id") or ""
                correlation_id = (fields or {}).get("correlation_id") or ""
                if not pqrs_id or not correlation_id:
                    logger.warning("Mensaje incompleto fields=%s", fields)
                    continue
                await _process_one(r, agent, pqrs_id, correlation_id)


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
