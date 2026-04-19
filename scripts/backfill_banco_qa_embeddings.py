#!/usr/bin/env python3
"""Genera embeddings para filas existentes en banco_qa (one-shot).

Requiere migración 004 (pgvector) y paquete opcional embedding:
  pip install -e \"contexts/banco_qa[embedding]\"

Uso:
  DATABASE_URL=postgresql://pqrs:pqrs@localhost:5433/pqrs?sslmode=disable \\
    python scripts/backfill_banco_qa_embeddings.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "contexts" / "banco_qa"
if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

from banco_qa.infrastructure.embedding import embed_text, vector_literal  # noqa: E402


def main() -> int:
    dsn = os.environ.get(
        "DATABASE_URL",
        "postgresql://pqrs:pqrs@localhost:5433/pqrs?sslmode=disable",
    )
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, pregunta, respuesta FROM banco_qa ORDER BY id"
            )
            rows = cur.fetchall()
        updated = 0
        for bid, pre, res in rows:
            text = f"{pre}\n{res}"
            vec = embed_text(text)
            lit = vector_literal(vec)
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE banco_qa SET embedding = %s::vector WHERE id = %s",
                    (lit, bid),
                )
            updated += 1
        conn.commit()
    print(f"OK: actualizados {updated} registros en banco_qa.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
