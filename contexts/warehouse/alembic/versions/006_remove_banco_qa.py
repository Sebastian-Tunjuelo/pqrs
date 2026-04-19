"""Elimina la tabla banco_qa (vista Respuestas / Q&A retirada del producto)."""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "006_remove_banco_qa"
down_revision = "005_pqrs_alertas"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS banco_qa CASCADE;"))


def downgrade() -> None:
    op.execute(
        text(
            """
            CREATE TABLE banco_qa (
                id SERIAL PRIMARY KEY,
                pregunta TEXT NOT NULL,
                respuesta TEXT NOT NULL,
                secretaria_codigo VARCHAR(10) REFERENCES dim_secretaria(codigo),
                tags TEXT[],
                veces_consultada INTEGER DEFAULT 0
            );
            """
        )
    )
