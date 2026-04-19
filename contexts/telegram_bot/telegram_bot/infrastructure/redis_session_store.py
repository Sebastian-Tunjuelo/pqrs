from __future__ import annotations
import json
from datetime import datetime
from typing import Optional
import redis.asyncio as aioredis
from telegram_bot.domain.models import UserProfile, IngresoState


class RedisSessionStore:
    def __init__(self, redis_url: str):
        self._redis = aioredis.from_url(redis_url, decode_responses=True)

    async def get_user(self, chat_id: int) -> Optional[UserProfile]:
        data = await self._redis.hgetall(f"bot:user:{chat_id}")
        if not data:
            return None
        return UserProfile.from_dict(data)

    async def save_user(self, profile: UserProfile) -> None:
        await self._redis.hset(f"bot:user:{profile.chat_id}", mapping=profile.to_dict())

    async def get_all_funcionarios(self) -> list[UserProfile]:
        keys = await self._redis.keys("bot:user:*")
        result = []
        for key in keys:
            data = await self._redis.hgetall(key)
            if data and data.get("rol") == "funcionario":
                result.append(UserProfile.from_dict(data))
        return result

    async def get_session(self, chat_id: int) -> list[dict]:
        items = await self._redis.lrange(f"bot:session:{chat_id}", 0, -1)
        return [json.loads(i) for i in items]

    async def append_session(self, chat_id: int, message: dict) -> None:
        key = f"bot:session:{chat_id}"
        await self._redis.rpush(key, json.dumps(message, ensure_ascii=False))
        # Mantener solo los últimos 10
        length = await self._redis.llen(key)
        if length > 10:
            await self._redis.ltrim(key, length - 10, -1)

    async def clear_session(self, chat_id: int) -> None:
        await self._redis.delete(f"bot:session:{chat_id}")

    async def get_ingreso(self, chat_id: int) -> Optional[IngresoState]:
        data = await self._redis.hgetall(f"bot:ingreso:{chat_id}")
        if not data:
            return None
        return IngresoState.from_dict(data)

    async def save_ingreso(self, state: IngresoState) -> None:
        key = f"bot:ingreso:{state.chat_id}"
        await self._redis.hset(key, mapping=state.to_dict())
        await self._redis.expire(key, 900)

    async def clear_ingreso(self, chat_id: int) -> None:
        await self._redis.delete(f"bot:ingreso:{chat_id}")

    async def alerta_ya_enviada(self, pqrs_id: str, fecha: str) -> bool:
        val = await self._redis.get(f"bot:alerta_enviada:{pqrs_id}:{fecha}")
        return val is not None

    async def marcar_alerta_enviada(self, pqrs_id: str, fecha: str) -> None:
        key = f"bot:alerta_enviada:{pqrs_id}:{fecha}"
        await self._redis.set(key, "1", ex=86400)

    async def esta_bloqueado(self, chat_id: int) -> bool:
        val = await self._redis.get(f"bot:registro_bloqueado:{chat_id}")
        return val is not None

    async def bloquear(self, chat_id: int) -> None:
        key = f"bot:registro_bloqueado:{chat_id}"
        await self._redis.set(key, datetime.utcnow().isoformat(), ex=600)

    async def incrementar_intentos(self, chat_id: int) -> int:
        """Incrementa intentos fallidos en el perfil. Retorna el nuevo valor."""
        key = f"bot:user:{chat_id}"
        val = await self._redis.hget(key, "intentos_fallidos")
        new_val = int(val or "0") + 1
        await self._redis.hset(key, "intentos_fallidos", str(new_val))
        return new_val

    async def reset_intentos(self, chat_id: int) -> None:
        await self._redis.hset(f"bot:user:{chat_id}", "intentos_fallidos", "0")

    async def close(self) -> None:
        await self._redis.aclose()
