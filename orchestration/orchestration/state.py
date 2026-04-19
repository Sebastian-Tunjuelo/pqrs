"""Estado compartido entre nodos del grafo LangGraph."""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """Campos que fluyen entre ingest → classify → prioritize → route → warehouse | reject."""

    raw_event: dict[str, Any]
    pqrs_id: str
    contenido: str
    fecha_radicado: str
    ingest_meta: dict[str, Any]

    estado_clasificacion: str
    clasificacion_tipo: str | None
    clasificacion_confianza: float | None
    clasificacion_razon: str | None
    clasificacion_source: str | None

    nivel_riesgo: str
    sla_dias_habiles: int
    fecha_limite: str
    priorizacion_justificacion: str | None

    routing_secretaria_lider: str
    routing_es_multidependencia: bool
    routing_matches: list[dict[str, Any]]
    routing_tie_breaker: bool

    warehouse_ok: bool
    pipeline_done: bool
    outcome: str
    error: str
