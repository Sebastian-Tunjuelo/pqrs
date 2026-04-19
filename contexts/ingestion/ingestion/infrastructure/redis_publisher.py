"""Redis Streams publisher for domain events."""

from __future__ import annotations

import json

from redis import asyncio as redis


class RedisEventPublisher:
    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        self._client = redis.from_url(redis_url, decode_responses=True)

    async def publish(self, stream: str, payload: dict) -> str:
        return await self._client.xadd(stream, {"event": json.dumps(payload)})
