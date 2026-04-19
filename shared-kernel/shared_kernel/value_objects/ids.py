"""Strongly typed identifiers (NewType wrappers)."""

from __future__ import annotations

import re
from typing import NewType
from uuid import UUID

PqrsId = NewType("PqrsId", str)
CiudadanoId = NewType("CiudadanoId", str)
SecretariaCodigo = NewType("SecretariaCodigo", str)

_SECRETARIA_RE = re.compile(r"^[A-Z0-9]{2,10}$")


def parse_pqrs_id(value: str) -> PqrsId:
    """Normaliza y valida UUID v1–v5 en string."""
    s = value.strip()
    UUID(s)  # raises ValueError if invalid
    return PqrsId(s.lower())


def parse_ciudadano_id(value: str) -> CiudadanoId:
    """Identificador anonimizado o interno de ciudadano (no vacío)."""
    s = value.strip()
    if not s:
        msg = "CiudadanoId cannot be empty"
        raise ValueError(msg)
    return CiudadanoId(s)


def parse_secretaria_codigo(value: str) -> SecretariaCodigo:
    """Código corto en mayúsculas (p. ej. SDE, DAGRD)."""
    s = value.strip().upper()
    if not _SECRETARIA_RE.match(s):
        msg = f"Invalid SecretariaCodigo: {value!r}"
        raise ValueError(msg)
    return SecretariaCodigo(s)
