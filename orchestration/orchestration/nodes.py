"""Nodos del pipeline: ingest → classify → (reject | prioritize → route → warehouse)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from shared_kernel.events.models import PqrsIngestedPayload
from shared_kernel.value_objects.enums import EstadoClasificacion, TipoPqrs

from orchestration.state import AgentState

if TYPE_CHECKING:
    from orchestration.deps import OrchestrationDeps


def _after_classify(state: AgentState) -> Literal["reject", "continue"]:
    v = state.get("estado_clasificacion") or ""
    if v in (
        EstadoClasificacion.RECHAZADA_OFENSIVO.value,
        EstadoClasificacion.RECHAZADA_NO_ENTENDIBLE.value,
    ):
        return "reject"
    return "continue"


async def ingest_node(state: AgentState) -> dict[str, Any]:
    raw = state.get("raw_event")
    if not raw:
        raise ValueError("raw_event es obligatorio")
    ev = PqrsIngestedPayload.model_validate(raw)
    return {
        "pqrs_id": ev.pqrs_id,
        "contenido": ev.contenido,
        "fecha_radicado": ev.fecha_radicado.isoformat(),
        "ingest_meta": dict(ev.metadata),
    }


def make_classify_node(deps: OrchestrationDeps):
    async def _node(state: AgentState) -> dict[str, Any]:
        uc = deps.classify_use_case
        if uc is None:
            raise RuntimeError("classify_use_case no configurado")
        texto = state.get("contenido") or ""
        r = await uc.execute(texto)
        return {
            "estado_clasificacion": r.verdict.value,
            "clasificacion_tipo": r.tipo.value if r.tipo else None,
            "clasificacion_confianza": r.confianza,
            "clasificacion_razon": r.razon,
            "clasificacion_source": r.source,
        }

    return _node


def make_prioritize_node(deps: OrchestrationDeps):
    async def _node(state: AgentState) -> dict[str, Any]:
        uc = deps.prioritize_use_case
        if uc is None:
            raise RuntimeError("prioritize_use_case no configurado")
        texto = state.get("contenido") or ""
        tipo_raw = state.get("clasificacion_tipo")
        tipo = TipoPqrs(tipo_raw) if tipo_raw else TipoPqrs.PETICION
        fr = state.get("fecha_radicado")
        if not fr:
            raise ValueError("fecha_radicado ausente")
        fecha_radicado = datetime.fromisoformat(fr.replace("Z", "+00:00")).date()
        pr = await uc.execute(texto, tipo, fecha_radicado)
        return {
            "nivel_riesgo": pr.nivel_riesgo.value,
            "sla_dias_habiles": pr.sla_dias_habiles,
            "fecha_limite": pr.fecha_limite.isoformat(),
            "priorizacion_justificacion": pr.justificacion,
        }

    return _node


def make_route_node(deps: OrchestrationDeps):
    async def _node(state: AgentState) -> dict[str, Any]:
        uc = deps.route_use_case
        if uc is None:
            raise RuntimeError("route_use_case no configurado")
        texto = state.get("contenido") or ""
        rd = await uc.execute(texto)
        matches = [m.model_dump() for m in rd.secretarias_recomendadas]
        return {
            "routing_secretaria_lider": rd.secretaria_lider,
            "routing_es_multidependencia": rd.es_multidependencia,
            "routing_matches": matches,
            "routing_tie_breaker": rd.tie_breaker_usado,
        }

    return _node


async def reject_node(state: AgentState) -> dict[str, Any]:
    return {
        "pipeline_done": True,
        "outcome": "reject",
        "warehouse_ok": False,
    }


async def warehouse_node(state: AgentState) -> dict[str, Any]:
    # Persistencia OLAP vía job batch / API; el grafo solo marca etapa.
    _ = state.get("pqrs_id")
    return {
        "warehouse_ok": True,
        "pipeline_done": True,
        "outcome": "completed",
    }


__all__ = [
    "_after_classify",
    "ingest_node",
    "make_classify_node",
    "make_prioritize_node",
    "make_route_node",
    "reject_node",
    "warehouse_node",
]
