from __future__ import annotations
import httpx
from telegram_bot.domain.exceptions import PqrsApiError


class OllamaClient:
    """Llama a Ollama directamente para chat libre."""

    def __init__(self, ollama_url: str, model: str = "llama3.2:3b"):
        self._url = ollama_url.rstrip("/")
        self._model = model

    async def mensaje_gestion(
        self,
        mensaje: str,
        historial: list[dict],
        rol: str,
        timeout: float = 60.0,
    ) -> str:
        system = (
            "Eres un asistente institucional de la Alcaldía de Medellín para el sistema PQRS. "
            "Responde en español de forma clara y concisa. "
            f"El usuario tiene rol: {rol}."
        )
        messages = [{"role": "system", "content": system}]
        messages.extend(historial[-10:])
        messages.append({"role": "user", "content": mensaje})

        body = {"model": self._model, "messages": messages, "stream": False}
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(f"{self._url}/api/chat", json=body)
                if r.status_code != 200:
                    raise PqrsApiError(r.status_code, r.text)
                data = r.json()
                return data.get("message", {}).get("content", "Sin respuesta del asistente.")
        except httpx.TimeoutException:
            raise PqrsApiError(504, "Timeout Ollama")
        except httpx.RequestError as e:
            raise PqrsApiError(503, str(e))
