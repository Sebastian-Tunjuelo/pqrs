"""Extensión pgvector y embedding en banco_qa."""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "004_banco_qa_pgvector"
down_revision = "003_pqrs_summary_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    op.execute(
        text("ALTER TABLE banco_qa ADD COLUMN IF NOT EXISTS embedding vector(384);")
    )


def downgrade() -> None:
    op.execute(text("ALTER TABLE banco_qa DROP COLUMN IF EXISTS embedding;"))
    # No eliminamos la extensión vector por si otros objetos la usan.
