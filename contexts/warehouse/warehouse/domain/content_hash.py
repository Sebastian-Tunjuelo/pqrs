"""Hash de contenido normalizado para deduplicación (SHA-256)."""

from __future__ import annotations

import hashlib


def compute_contenido_hash(contenido: str) -> str:
    """Misma normalización que ingestion: minúsculas y espacios colapsados."""
    normalized = " ".join(contenido.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
