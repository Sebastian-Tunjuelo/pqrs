"""Load and validate glossary YAML files used by domain agents."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, TypeAdapter


class NoEntendibleConfig(BaseModel):
    min_caracteres: int = Field(ge=1)
    patrones_rechazo: list[str]


class OfensivoGlossary(BaseModel):
    insultos_directos: list[str]
    amenazas: list[str]
    discriminacion: list[str]
    no_entendible: NoEntendibleConfig


class RiskLevelGlossary(BaseModel):
    CRITICO: dict[str, list[str]] | None = None
    ALTO: dict[str, list[str]] | None = None
    MEDIO: dict[str, list[str]] | None = None
    BAJO: dict[str, list[str]] | None = None


class SecretariaEntry(BaseModel):
    nombre: str
    keywords: list[str]


class MultiDependenciaRule(BaseModel):
    trigger: list[str]
    secretarias: list[str]


class SecretariasRoutingGlossary(BaseModel):
    secretarias: dict[str, SecretariaEntry]
    multidependencias: list[MultiDependenciaRule]


GlossaryKind = Literal[
    "ofensivo",
    "riesgo_poblacional",
    "riesgo_personal",
    "secretarias_routing",
]


def load_glossary(path: str | Path, kind: GlossaryKind) -> Any:
    raw = _read_yaml(path)
    if kind == "ofensivo":
        return OfensivoGlossary.model_validate(raw)
    if kind == "secretarias_routing":
        return SecretariasRoutingGlossary.model_validate(raw)
    return RiskLevelGlossary.model_validate(raw)


def load_glossary_as_dict(path: str | Path, kind: GlossaryKind) -> dict[str, Any]:
    parsed = load_glossary(path=path, kind=kind)
    return TypeAdapter(type(parsed)).dump_python(parsed)


def _read_yaml(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    return yaml.safe_load(p.read_text(encoding="utf-8"))
