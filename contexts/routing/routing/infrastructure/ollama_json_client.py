"""Cliente Ollama async para JSON (tie-breaker de ruteo)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import ollama


@runtime_checkable
class SupportsJsonChat(Protocol):
    async def chat_json(self, system: str, user: str) -> str: ...


class OllamaJsonClient:
    def __init__(
        self,
        model: str = "llama3.2:3b",
        host: str | None = None,
        client: Any | None = None,
    ) -> None:
        if client is not None:
            self._client = client
        elif host:
            self._client = ollama.AsyncClient(host=host)
        else:
            self._client = ollama.AsyncClient()
        self._model = model

    async def chat_json(self, system: str, user: str) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        try:
            resp = await self._client.chat(
                model=self._model,
                messages=messages,
                format="json",
            )
        except TypeError:
            resp = await self._client.chat(model=self._model, messages=messages)
        content = resp["message"]["content"]
        if not isinstance(content, str):
            msg = "Respuesta Ollama sin texto"
            raise TypeError(msg)
        return content
