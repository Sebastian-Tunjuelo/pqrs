"""Consulta de duplicados por ``contenido_hash`` en PostgreSQL."""

from __future__ import annotations

from sqlalchemy import Engine, text


def exists_pqrs_with_hash(engine: Engine, contenido_hash: str) -> bool:
    stmt = text("SELECT 1 FROM pqrs WHERE contenido_hash = :h LIMIT 1")
    with engine.connect() as conn:
        return conn.execute(stmt, {"h": contenido_hash}).first() is not None
