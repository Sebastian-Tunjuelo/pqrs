"""Classify PQRS: pre-filter + optional Ollama JSON classification."""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from shared_kernel.value_objects.enums import EstadoClasificacion, TipoPqrs

from classification.domain.classified_pqrs import ClassifiedPqrs
from classification.infrastructure.ollama_client import OllamaJsonClient, SupportsJsonChat
from classification.infrastructure.prefilter import (
    check_no_entendible,
    load_no_entendible_config,
    load_offensive_phrases,
    match_offensive_prefilter,
)
from classification.infrastructure.paths import classifier_prompt_path


def _strip_json_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


class _LLMRow(BaseModel):
    tipo: str = Field(pattern=r"^[PQRSD]$")
    es_ofensivo: bool
    es_entendible: bool
    confianza: float = Field(ge=0.0, le=1.0)
    razon: str
    palabras_detectadas: list[str] = Field(default_factory=list)


class ClassifyPqrsUseCase:
    def __init__(
        self,
        ollama_client: SupportsJsonChat | None = None,
        system_prompt_path: Path | None = None,
    ) -> None:
        self._ollama = ollama_client or OllamaJsonClient()
        self._prompt_path = system_prompt_path or classifier_prompt_path()
        self._offensive_cache: list[str] | None = None

    def _offensive_phrases(self) -> list[str]:
        if self._offensive_cache is None:
            self._offensive_cache = load_offensive_phrases()
        return self._offensive_cache

    async def execute(self, texto: str) -> ClassifiedPqrs:
        offensive_hits = match_offensive_prefilter(texto, self._offensive_phrases())
        if offensive_hits:
            return ClassifiedPqrs(
                verdict=EstadoClasificacion.RECHAZADA_OFENSIVO,
                confianza=1.0,
                razon="Coincidencia con glosario ofensivo (pre-filtro).",
                palabras_detectadas=offensive_hits[:20],
                source="prefilter_offensive",
            )

        min_chars, patrones = load_no_entendible_config()
        ne_reasons = check_no_entendible(texto, min_caracteres=min_chars, patrones=patrones)
        if ne_reasons:
            return ClassifiedPqrs(
                verdict=EstadoClasificacion.RECHAZADA_NO_ENTENDIBLE,
                confianza=0.95,
                razon=f"No entendible: {', '.join(ne_reasons)}",
                palabras_detectadas=[],
                source="prefilter_no_entendible",
            )

        system = self._prompt_path.read_text(encoding="utf-8")
        raw = await self._ollama.chat_json(system=system, user=texto)

        try:
            data = json.loads(_strip_json_fence(raw))
            row = _LLMRow.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            return ClassifiedPqrs(
                verdict=EstadoClasificacion.RECHAZADA_NO_ENTENDIBLE,
                confianza=0.0,
                razon=f"Respuesta LLM inválida: {exc}",
                palabras_detectadas=[],
                source="llm",
            )

        if row.es_ofensivo:
            return ClassifiedPqrs(
                verdict=EstadoClasificacion.RECHAZADA_OFENSIVO,
                tipo=TipoPqrs(row.tipo),
                confianza=row.confianza,
                razon=row.razon,
                palabras_detectadas=row.palabras_detectadas,
                source="llm",
            )
        if not row.es_entendible:
            return ClassifiedPqrs(
                verdict=EstadoClasificacion.RECHAZADA_NO_ENTENDIBLE,
                tipo=TipoPqrs(row.tipo),
                confianza=row.confianza,
                razon=row.razon,
                palabras_detectadas=row.palabras_detectadas,
                source="llm",
            )

        return ClassifiedPqrs(
            verdict=EstadoClasificacion.ACEPTADA,
            tipo=TipoPqrs(row.tipo),
            confianza=row.confianza,
            razon=row.razon,
            palabras_detectadas=row.palabras_detectadas,
            source="llm",
        )
