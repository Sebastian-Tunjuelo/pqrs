"""Prioriza PQRS: glosarios + LLM + Ley 1755 + calendario Colombia."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from shared_kernel.value_objects.enums import NivelRiesgo, TipoPqrs

from prioritization.domain.ley_1755 import dias_habiles_sla
from prioritization.domain.prioritized_pqrs import PrioritizedPqrs
from prioritization.infrastructure.calendario_colombia import fecha_limite_dias_habiles
from prioritization.infrastructure.ollama_json_client import OllamaJsonClient, SupportsJsonChat
from prioritization.infrastructure.paths import prioritizer_prompt_path
from prioritization.infrastructure.riesgo_matcher import match_nivel_desde_glosarios


def _strip_json_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


class _LLMPrioridad(BaseModel):
    nivel_riesgo: NivelRiesgo
    factores_riesgo: list[str] = Field(default_factory=list)
    justificacion: str


def _max_nivel(a: NivelRiesgo, b: NivelRiesgo) -> NivelRiesgo:
    order = (NivelRiesgo.BAJO, NivelRiesgo.MEDIO, NivelRiesgo.ALTO, NivelRiesgo.CRITICO)
    return a if order.index(a) >= order.index(b) else b


class PrioritizePqrsUseCase:
    def __init__(
        self,
        ollama_client: SupportsJsonChat | None = None,
        system_prompt_path: Path | None = None,
    ) -> None:
        self._ollama = ollama_client or OllamaJsonClient()
        self._prompt_path = system_prompt_path or prioritizer_prompt_path()

    async def execute(
        self,
        texto: str,
        tipo: TipoPqrs,
        fecha_radicado: date,
    ) -> PrioritizedPqrs:
        nivel_gloss, factores_gloss = match_nivel_desde_glosarios(texto)

        system = self._prompt_path.read_text(encoding="utf-8")
        user_payload = json.dumps(
            {
                "texto": texto,
                "tipo_pqrs": tipo.value,
                "nivel_desde_glosario": nivel_gloss.value,
                "factores_glosario": factores_gloss,
            },
            ensure_ascii=False,
        )
        raw = await self._ollama.chat_json(system=system, user=user_payload)

        try:
            data = json.loads(_strip_json_fence(raw))
            llm_row = _LLMPrioridad.model_validate(data)
        except (json.JSONDecodeError, ValidationError):
            nivel_final = nivel_gloss
            factores = list(factores_gloss)
            justificacion = "Fallback: respuesta LLM inválida; se usa solo glosario."
            source = "glossary"
        else:
            nivel_final = _max_nivel(nivel_gloss, llm_row.nivel_riesgo)
            factores = list({*factores_gloss, *llm_row.factores_riesgo})
            justificacion = llm_row.justificacion
            source = "merged"

        sla = dias_habiles_sla(tipo, nivel_final)
        fecha_lim = fecha_limite_dias_habiles(fecha_radicado, sla)

        return PrioritizedPqrs(
            tipo=tipo,
            nivel_riesgo=nivel_final,
            sla_dias_habiles=sla,
            fecha_limite=fecha_lim,
            factores_riesgo=factores[:30],
            justificacion=justificacion,
            source=source,
        )
