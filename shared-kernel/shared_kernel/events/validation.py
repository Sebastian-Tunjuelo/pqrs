"""Load JSON Schemas from package data and validate payloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

_SCHEMA_CACHE: dict[str, dict[str, Any]] = {}


def _json_dir() -> Path:
    return Path(__file__).resolve().parent / "json"


def event_schema_path(name: str) -> Path:
    """Ruta al fichero JSON Schema empaquetado (p. ej. para tooling externo)."""
    return _json_dir() / f"{_schema_filename(name)}.json"


def _schema_filename(event_name: str) -> str:
    mapping = {
        "PqrsIngested": "pqrs_ingested",
        "PqrsClassified": "pqrs_classified",
        "PqrsPrioritized": "pqrs_prioritized",
        "PqrsRouted": "pqrs_routed",
    }
    if event_name not in mapping:
        msg = f"Unknown event: {event_name}"
        raise KeyError(msg)
    return mapping[event_name]


def load_event_schema(event_name: str) -> dict[str, Any]:
    """Carga y cachea el JSON Schema para ``event_name``."""
    if event_name in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[event_name]
    path = event_schema_path(event_name)
    schema = json.loads(path.read_text(encoding="utf-8"))
    _SCHEMA_CACHE[event_name] = schema
    return schema


def validate_event_payload(event_name: str, payload: dict[str, Any]) -> None:
    """Lanza ``jsonschema.ValidationError`` si el payload no cumple el schema."""
    schema = load_event_schema(event_name)
    validator = Draft202012Validator(
        schema,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )
    validator.validate(payload)
