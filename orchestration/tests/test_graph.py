"""Tests del grafo con casos de uso mockeados (sin Ollama ni Redis)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock

import pytest

from shared_kernel.value_objects.enums import EstadoClasificacion, NivelRiesgo, TipoPqrs

from orchestration.deps import OrchestrationDeps
from orchestration.graph import build_graph


class _FakeClassified:
    def __init__(self, verdict: EstadoClasificacion, tipo: TipoPqrs | None = TipoPqrs.PETICION):
        self.verdict = verdict
        self.tipo = tipo
        self.confianza = 0.9
        self.razon = None
        self.source = "test"


class _FakePrioritized:
    def __init__(self) -> None:
        self.nivel_riesgo = NivelRiesgo.BAJO
        self.sla_dias_habiles = 15
        self.fecha_limite = date(2026, 2, 1)
        self.justificacion = "test"


class _Match:
    def model_dump(self) -> dict:
        return {
            "codigo": "SGH",
            "nombre": "Salud",
            "score": 0.9,
            "motivo": "test",
        }


class _FakeRouting:
    def __init__(self) -> None:
        self.secretarias_recomendadas = [_Match()]
        self.es_multidependencia = False
        self.secretaria_lider = "SGH"
        self.tie_breaker_usado = False


def _ingested_payload() -> dict:
    return {
        "event_type": "PqrsIngested",
        "version": 1,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "pqrs_id": "550e8400-e29b-41d4-a716-446655440000",
        "id_externo": None,
        "contenido": "Solicitud de información sobre vacunación",
        "fecha_radicado": "2026-01-10T10:00:00+00:00",
        "source": "medata_api",
        "metadata": {},
    }


@pytest.mark.asyncio
async def test_pipeline_happy_path() -> None:
    clf = AsyncMock()
    clf.execute.return_value = _FakeClassified(EstadoClasificacion.ACEPTADA)
    pr = AsyncMock()
    pr.execute.return_value = _FakePrioritized()
    rt = AsyncMock()
    rt.execute.return_value = _FakeRouting()
    deps = OrchestrationDeps(
        classify_use_case=clf,
        prioritize_use_case=pr,
        route_use_case=rt,
    )
    app = build_graph(deps)
    out = await app.ainvoke({"raw_event": _ingested_payload()})
    assert out.get("outcome") == "completed"
    assert out.get("warehouse_ok") is True
    assert out.get("validation_status") == "PENDING_VALIDATION"
    assert out.get("routing_secretaria_lider") == "SGH"
    clf.execute.assert_awaited_once()
    pr.execute.assert_awaited_once()
    rt.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_pipeline_reject_offensive() -> None:
    clf = AsyncMock()
    clf.execute.return_value = _FakeClassified(EstadoClasificacion.RECHAZADA_OFENSIVO)
    pr = AsyncMock()
    rt = AsyncMock()
    deps = OrchestrationDeps(
        classify_use_case=clf,
        prioritize_use_case=pr,
        route_use_case=rt,
    )
    app = build_graph(deps)
    out = await app.ainvoke({"raw_event": _ingested_payload()})
    assert out.get("outcome") == "reject"
    assert out.get("warehouse_ok") is False
    clf.execute.assert_awaited_once()
    pr.execute.assert_not_called()
    rt.execute.assert_not_called()
