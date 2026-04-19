"""Tests del caso de uso con Ollama mockeado."""

from __future__ import annotations

import json
from datetime import date

import pytest

from prioritization.application.prioritize_use_case import PrioritizePqrsUseCase
from shared_kernel.value_objects.enums import NivelRiesgo, TipoPqrs


class FixedLLM:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    async def chat_json(self, system: str, user: str) -> str:
        return json.dumps(self._payload)


@pytest.mark.asyncio
async def test_merge_subida_por_llm() -> None:
    texto = "Solicitud de información general sobre trámites en la ciudad."
    llm = FixedLLM(
        {
            "nivel_riesgo": "MEDIO",
            "factores_riesgo": ["economico"],
            "justificacion": "Menciona afectación económica leve.",
        }
    )
    uc = PrioritizePqrsUseCase(ollama_client=llm)
    r = await uc.execute(texto, tipo=TipoPqrs.PETICION, fecha_radicado=date(2025, 1, 2))
    assert r.nivel_riesgo == NivelRiesgo.MEDIO
    assert r.sla_dias_habiles == 15


@pytest.mark.asyncio
async def test_glosario_critico_prevalece_sobre_llm_bajo() -> None:
    texto = (
        "Reporto inundación activa en el sector, hay riesgo colectivo y "
        "necesitamos evacuación inmediata en Medellín."
    )
    llm = FixedLLM(
        {
            "nivel_riesgo": "BAJO",
            "factores_riesgo": [],
            "justificacion": "Ignorado por glosario.",
        }
    )
    uc = PrioritizePqrsUseCase(ollama_client=llm)
    r = await uc.execute(texto, tipo=TipoPqrs.DENUNCIA, fecha_radicado=date(2025, 6, 2))
    assert r.nivel_riesgo == NivelRiesgo.CRITICO
    assert r.sla_dias_habiles == 10
