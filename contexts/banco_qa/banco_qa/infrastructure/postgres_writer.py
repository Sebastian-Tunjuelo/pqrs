"""Escritura masiva en `banco_qa` (reemplazo completo en una transacción)."""

from __future__ import annotations

from collections.abc import Sequence

import psycopg

from banco_qa.domain.catalog import QaEntry


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
        return len(entries)
