"""Resultado de priorización + SLA."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from shared_kernel.value_objects.enums import NivelRiesgo, TipoPqrs


class PrioritizedPqrs(BaseModel):
    tipo: TipoPqrs
    nivel_riesgo: NivelRiesgo
    sla_dias_habiles: int = Field(ge=1, le=365)
    fecha_limite: date
    factores_riesgo: list[str] = Field(default_factory=list)
    justificacion: str | None = None
    source: str = Field(
        default="prioritizer",
        description="glossary | llm | merged",
    )
