"""Escritura masiva en `banco_qa` (reemplazo completo en una transacción)."""

from __future__ import annotations

from collections.abc import Sequence

import psycopg

from banco_qa.domain.catalog import QaEntry

try:
    from banco_qa.infrastructure.embedding import embed_text, vector_literal
except ImportError:
    embed_text = None  # type: ignore[assignment,misc]
    vector_literal = None  # type: ignore[assignment,misc]


class PostgresBancoQaWriter:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def replace_all(self, entries: Sequence[QaEntry]) -> int:
        """Vacía `banco_qa` e inserta las entradas. Devuelve filas insertadas."""
        with psycopg.connect(self._dsn) as conn:
            with conn.transaction():
                conn.execute("DELETE FROM banco_qa")
                for e in entries:
                    conn.execute(
                        """
                        INSERT INTO banco_qa (pregunta, respuesta, secretaria_codigo, tags)
                        VALUES (%(p)s, %(r)s, %(s)s, %(t)s)
                        """,
                        {
                            "p": e.pregunta,
                            "r": e.respuesta,
                            "s": e.secretaria_codigo,
                            "t": e.tags if e.tags else None,
                        },
                    )
                if embed_text is not None and vector_literal is not None:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT id, pregunta, respuesta FROM banco_qa ORDER BY id"
                        )
                        for bid, pre, res in cur.fetchall():
                            vec = embed_text(f"{pre}\n{res}")
                            lit = vector_literal(vec)
                            cur.execute(
                                "UPDATE banco_qa SET embedding = %s::vector WHERE id = %s",
                                (lit, bid),
                            )
        return len(entries)
