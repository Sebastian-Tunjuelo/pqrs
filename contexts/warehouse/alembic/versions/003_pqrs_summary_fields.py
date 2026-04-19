"""Campos de síntesis en 3 capas para PQRS."""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "003_pqrs_summary_fields"
down_revision = "002_validation_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("ALTER TABLE pqrs ADD COLUMN IF NOT EXISTS summary_lead TEXT;"))
    op.execute(
        text(
            "ALTER TABLE pqrs ADD COLUMN IF NOT EXISTS summary_topics JSONB DEFAULT '[]'::jsonb;"
        )
    )
    op.execute(text("ALTER TABLE pqrs ADD COLUMN IF NOT EXISTS summary_executive TEXT;"))


def downgrade() -> None:
    op.execute(text("ALTER TABLE pqrs DROP COLUMN IF EXISTS summary_executive;"))
    op.execute(text("ALTER TABLE pqrs DROP COLUMN IF EXISTS summary_topics;"))
    op.execute(text("ALTER TABLE pqrs DROP COLUMN IF EXISTS summary_lead;"))
