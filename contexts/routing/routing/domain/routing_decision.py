"""Decisiones de enrutamiento PQRS → secretaría(s)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SecretariaMatch(BaseModel):
    codigo: str
    nombre: str
    score: float = Field(ge=0.0, le=1.0)
    motivo: str


class RoutingDecision(BaseModel):
    secretarias_recomendadas: list[SecretariaMatch]
    es_multidependencia: bool
    secretaria_lider: str
    tie_breaker_usado: bool = False
