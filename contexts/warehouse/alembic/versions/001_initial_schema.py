"""Esquema inicial OLTP (PostGIS) según ARCHITECTURE §9.1."""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    statements = [
        'CREATE EXTENSION IF NOT EXISTS postgis;',
        'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";',
        """
        CREATE TABLE dim_secretaria (
            codigo VARCHAR(10) PRIMARY KEY,
            nombre TEXT NOT NULL,
            activa BOOLEAN DEFAULT true
        );
        """,
        """
        CREATE TABLE dim_territorio (
            id SERIAL PRIMARY KEY,
            tipo VARCHAR(20) CHECK (tipo IN ('COMUNA','CORREGIMIENTO')),
            codigo VARCHAR(10) UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            geometria geometry(MultiPolygon, 4326)
        );
        """,
        """
        CREATE TABLE pqrs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            id_externo VARCHAR(100) UNIQUE,
            tipo CHAR(1) CHECK (tipo IN ('P','Q','R','S','D')),
            contenido TEXT NOT NULL,
            contenido_hash VARCHAR(64),
            fecha_radicado TIMESTAMPTZ NOT NULL,
            fecha_limite DATE,
            estado_clasificacion VARCHAR(30) NOT NULL,
            estado_gestion VARCHAR(20) DEFAULT 'PENDIENTE',
            nivel_riesgo VARCHAR(10),
            territorio_id INTEGER REFERENCES dim_territorio(id),
            punto_geo geometry(Point, 4326),
            confianza_clasificacion NUMERIC(3,2),
            razon_rechazo TEXT,
            metadata JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        """
        CREATE UNIQUE INDEX uq_pqrs_contenido_hash
        ON pqrs (contenido_hash)
        WHERE contenido_hash IS NOT NULL;
        """,
        """
        CREATE TABLE pqrs_secretaria (
            pqrs_id UUID REFERENCES pqrs(id) ON DELETE CASCADE,
            secretaria_codigo VARCHAR(10) REFERENCES dim_secretaria(codigo),
            es_lider BOOLEAN DEFAULT false,
            score NUMERIC(3,2),
            motivo TEXT,
            PRIMARY KEY (pqrs_id, secretaria_codigo)
        );
        """,
        """
        CREATE TABLE pqrs_historial (
            id BIGSERIAL PRIMARY KEY,
            pqrs_id UUID REFERENCES pqrs(id),
            estado_anterior VARCHAR(30),
            estado_nuevo VARCHAR(30),
            actor VARCHAR(50),
            nota TEXT,
            "timestamp" TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE banco_qa (
            id SERIAL PRIMARY KEY,
            pregunta TEXT NOT NULL,
            respuesta TEXT NOT NULL,
            secretaria_codigo VARCHAR(10) REFERENCES dim_secretaria(codigo),
            tags TEXT[],
            veces_consultada INTEGER DEFAULT 0
        );
        """,
        "CREATE INDEX idx_pqrs_estado_gestion ON pqrs(estado_gestion);",
        "CREATE INDEX idx_pqrs_nivel_riesgo ON pqrs(nivel_riesgo);",
        "CREATE INDEX idx_pqrs_fecha_limite ON pqrs(fecha_limite);",
        "CREATE INDEX idx_pqrs_territorio ON pqrs(territorio_id);",
        "CREATE INDEX idx_pqrs_geo ON pqrs USING GIST(punto_geo);",
    ]

    for stmt in statements:
        cleaned = stmt.strip().rstrip(";")
        op.execute(text(cleaned))


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS banco_qa CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS pqrs_historial CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS pqrs_secretaria CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS pqrs CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS dim_territorio CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS dim_secretaria CASCADE;"))
