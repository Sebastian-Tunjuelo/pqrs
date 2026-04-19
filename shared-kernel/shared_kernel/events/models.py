"""Pydantic models for domain event payloads (aligned with JSON schemas)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from shared_kernel.value_objects.enums import (
    EstadoClasificacion,
    NivelRiesgo,
    TipoPqrs,
)


class PqrsIngestedPayload(BaseModel):
    """Publicado por ingestion tras normalizar un registro MEData o scraping."""

    event_type: Literal["PqrsIngested"] = "PqrsIngested"
    version: Literal[1] = 1
    occurred_at: datetime = Field(description="Momento del evento en UTC")
    pqrs_id: str = Field(description="UUID v4 del agregado PQRS")
    id_externo: str | None = Field(default=None, description="ID en MEData si existe")
    contenido: str
    fecha_radicado: datetime
    source: Literal["medata_api", "medata_scrape", "medata_dcat"]
    metadata: dict[str, Any] = Field(default_factory=dict)


class PqrsClassifiedPayload(BaseModel):
    """Tras clasificación (ofensivo / entendible / tipo)."""

    event_type: Literal["PqrsClassified"] = "PqrsClassified"
    version: Literal[1] = 1
    occurred_at: datetime
    pqrs_id: str
    estado_clasificacion: EstadoClasificacion
    tipo: TipoPqrs | None = None
    confianza: float | None = Field(default=None, ge=0.0, le=1.0)
    razon_rechazo: str | None = None
    palabras_detectadas: list[str] = Field(default_factory=list)


class PqrsPrioritizedPayload(BaseModel):
    """Tras priorización + SLA Ley 1755."""

    event_type: Literal["PqrsPrioritized"] = "PqrsPrioritized"
    version: Literal[1] = 1
    occurred_at: datetime
    pqrs_id: str
    nivel_riesgo: NivelRiesgo
    sla_dias_habiles: int = Field(ge=1, le=365)
    fecha_limite: date
    factores_riesgo: list[str] = Field(default_factory=list)
    justificacion: str | None = None


class SecretariaRecomendada(BaseModel):
    codigo: str
    nombre: str
    score: float = Field(ge=0.0, le=1.0)
    motivo: str


class PqrsRoutedPayload(BaseModel):
    """Tras recomendación de secretaría(s)."""

    event_type: Literal["PqrsRouted"] = "PqrsRouted"
    version: Literal[1] = 1
    occurred_at: datetime
    pqrs_id: str
    secretarias_recomendadas: list[SecretariaRecomendada]
    es_multidependencia: bool
    secretaria_lider: str
