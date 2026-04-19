"""Alertas de vencimiento y cola de notificaciones."""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "005_pqrs_alertas"
down_revision = "004_banco_qa_pgvector"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        text(
            """
            CREATE TABLE pqrs_alertas (
                id BIGSERIAL PRIMARY KEY,
                pqrs_id UUID NOT NULL REFERENCES pqrs(id) ON DELETE CASCADE,
                tipo VARCHAR(40) NOT NULL,
                mensaje TEXT,
                activa BOOLEAN NOT NULL DEFAULT true,
                creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )
    )
    op.execute(
        text(
            """
            CREATE UNIQUE INDEX uq_pqrs_alerta_proximo_activa
            ON pqrs_alertas (pqrs_id)
            WHERE tipo = 'PROXIMO_VENCIMIENTO' AND activa = true;
            """
        )
    )
    op.execute(text("CREATE INDEX idx_pqrs_alertas_activa ON pqrs_alertas(activa);"))


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS pqrs_alertas CASCADE;"))
