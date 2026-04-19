"""Embeddings locales (sentence-transformers all-MiniLM-L6-v2, dim 384)."""

from __future__ import annotations

_model = None


def _load_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_text(text: str) -> list[float]:
    """Vector normalizado (coseno) listo para pgvector."""
    m = _load_model()
    v = m.encode(text.strip(), normalize_embeddings=True)
    return [float(x) for x in v.tolist()]


def vector_literal(values: list[float]) -> str:
    """Literal textual para cast `::vector` en SQL."""
    inner = ",".join(f"{x:.8f}" for x in values)
    return f"[{inner}]"
