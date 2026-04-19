"""Agente de síntesis en 3 capas (lead, temas, resumen ejecutivo) vía Ollama JSON."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from classification.infrastructure.ollama_client import OllamaJsonClient, SupportsJsonChat
from classification.infrastructure.paths import summary_prompt_path


def _strip_json_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


class _SummaryLLMRow(BaseModel):
    lead: str = Field(min_length=3)
    temas: list[str] = Field(min_length=1, max_length=12)
    resumen_ejecutivo: str = Field(min_length=20)


@dataclass
class SummaryAgentResult:
    lead: str
    temas: list[str]
    resumen_ejecutivo: str


class SummaryAgent:
    """Genera síntesis estructurada; `pqrs_completa` la añade quien orquesta."""

    def __init__(
        self,
        ollama_client: SupportsJsonChat | None = None,
        system_prompt_path: Path | None = None,
    ) -> None:
        self._ollama = ollama_client or OllamaJsonClient()
        self._prompt_path = system_prompt_path or summary_prompt_path()

    async def execute(self, texto_pqrs: str) -> SummaryAgentResult:
        system = self._prompt_path.read_text(encoding="utf-8")
        raw = await self._ollama.chat_json(system=system, user=texto_pqrs)
        try:
            data = json.loads(_strip_json_fence(raw))
            row = _SummaryLLMRow.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            msg = f"Respuesta de síntesis inválida: {exc}"
            raise ValueError(msg) from exc
        temas = [t.strip() for t in row.temas if t.strip()][:8]
        if not temas:
            raise ValueError("La síntesis no contiene temas válidos")
        return SummaryAgentResult(
            lead=row.lead.strip(),
            temas=temas,
            resumen_ejecutivo=row.resumen_ejecutivo.strip(),
        )
