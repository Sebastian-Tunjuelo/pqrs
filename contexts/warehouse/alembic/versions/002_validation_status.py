"""Enum validation_status en pqrs e índice para cola de validación humana."""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "002_validation_status"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        text(
            """
            DO $$ BEGIN
                CREATE TYPE validation_status AS ENUM (
                    'PENDING_VALIDATION',
                    'VALIDATED',
                    'REJECTED_BY_OFFICER',
                    'CORRECTION_REQUESTED'
                );
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END $$;
            """
        )
    )
    op.execute(
        text(
            """
            ALTER TABLE pqrs
            ADD COLUMN IF NOT EXISTS validation_status validation_status
            NOT NULL DEFAULT 'PENDING_VALIDATION';
            """
        )
    )
    op.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_pqrs_validation_status
            ON pqrs(validation_status);
            """
        )
    )
    op.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_pqrs_pending_validation
            ON pqrs (validation_status, estado_clasificacion, fecha_limite)
            WHERE validation_status = 'PENDING_VALIDATION'
              AND estado_clasificacion = 'ACEPTADA';
            """
        )
    )
    op.execute(
        text(
            """
            ALTER TABLE pqrs_historial
            ADD COLUMN IF NOT EXISTS officer_id VARCHAR(200);
            """
        )
    )


def downgrade() -> None:
    op.execute(text("DROP INDEX IF EXISTS idx_pqrs_pending_validation;"))
    op.execute(text("DROP INDEX IF EXISTS idx_pqrs_validation_status;"))
    op.execute(text("ALTER TABLE pqrs_historial DROP COLUMN IF EXISTS officer_id;"))
    op.execute(text("ALTER TABLE pqrs DROP COLUMN IF EXISTS validation_status;"))
    op.execute(text("DROP TYPE IF EXISTS validation_status;"))
