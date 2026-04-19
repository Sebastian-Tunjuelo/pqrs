"""Consumidor Redis Streams del evento PqrsIngested → grafo LangGraph."""

from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any

from redis import asyncio as redis

from orchestration.deps import OrchestrationDeps, default_deps
from orchestration.graph import build_graph

logger = logging.getLogger(__name__)

STREAM_INGESTED = "pqrs.events.ingested"
STREAM_DLQ = "pqrs.events.dlq"
GROUP_NAME = "orchestration"
MAX_ATTEMPTS = 3


async def _ensure_group(r: redis.Redis) -> None:
    try:
        await r.xgroup_create(STREAM_INGESTED, GROUP_NAME, id="0", mkstream=True)
    except redis.ResponseError as e:
        if "BUSYGROUP" not in str(e).upper():
            raise


async def _handle_one(
    r: redis.Redis,
    app: Any,
    msg_id: str,
    fields: dict[str, str],
) -> None:
    raw = fields.get("event")
    if not raw:
        raise ValueError("mensaje sin campo 'event'")
    payload = json.loads(raw)
    last_err: BaseException | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            await app.ainvoke({"raw_event": payload})
            await r.xack(STREAM_INGESTED, GROUP_NAME, msg_id)
            logger.info("procesado ok msg_id=%s pqrs_id=%s", msg_id, payload.get("pqrs_id"))
            return
        except BaseException as exc:  # noqa: BLE001 — DLQ captura cualquier fallo del pipeline
            last_err = exc
            logger.warning(
                "intento %s/%s fallido msg_id=%s: %s",
                attempt,
                MAX_ATTEMPTS,
                msg_id,
                exc,
            )
    err_text = repr(last_err) if last_err else "unknown"
    dlq_body = {
        "original_stream": STREAM_INGESTED,
        "original_id": msg_id,
        "event": raw,
        "error": err_text,
        "attempts": str(MAX_ATTEMPTS),
    }
    await r.xadd(STREAM_DLQ, dlq_body)
    await r.xack(STREAM_INGESTED, GROUP_NAME, msg_id)
    logger.error("enviado a DLQ msg_id=%s error=%s", msg_id, err_text)


async def run_worker(
    redis_url: str | None = None,
    deps: OrchestrationDeps | None = None,
    consumer_name: str | None = None,
) -> None:
    logging.basicConfig(level=logging.INFO)
    url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    consumer = consumer_name or os.environ.get("ORCH_CONSUMER_NAME") or f"worker-{uuid.uuid4().hex[:8]}"
    r = redis.from_url(url, decode_responses=True)
    await _ensure_group(r)
    app = build_graph(deps)
    logger.info("worker listo stream=%s group=%s consumer=%s", STREAM_INGESTED, GROUP_NAME, consumer)
    while True:
        resp = await r.xreadgroup(
            GROUP_NAME,
            consumer,
            {STREAM_INGESTED: ">"},
            count=1,
            block=5000,
        )
        if not resp:
            continue
        for _stream, messages in resp:
            for msg_id, fields in messages:
                await _handle_one(r, app, msg_id, fields)


def main() -> None:
    import asyncio

    asyncio.run(run_worker())
