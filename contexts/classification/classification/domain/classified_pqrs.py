"""Classified PQRS aggregate read model."""

from __future__ import annotations

from pydantic import BaseModel, Field

from shared_kernel.value_objects.enums import EstadoClasificacion, TipoPqrs

ClassificationVerdict = EstadoClasificacion


class ClassifiedPqrs(BaseModel):
    """Resultado de clasificar contenido de una PQRS."""

    verdict: EstadoClasificacion
    tipo: TipoPqrs | None = None
    confianza: float | None = Field(default=None, ge=0.0, le=1.0)
    razon: str | None = None
    palabras_detectadas: list[str] = Field(default_factory=list)
    source: str = Field(
        default="llm",
        description="prefilter_offensive | prefilter_no_entendible | llm",
    )
