"""Refresco de vistas analíticas en DuckDB leyendo PostgreSQL vía ATTACH."""

from __future__ import annotations

import os
from pathlib import Path

import duckdb


def _postgres_attach_string() -> str:
    return (
        "dbname={db} host={host} port={port} user={user} password={password}".format(
            db=os.environ.get("POSTGRES_DB", "pqrs"),
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=os.environ.get("POSTGRES_PORT", "5432"),
            user=os.environ.get("POSTGRES_USER", "pqrs"),
            password=os.environ.get("POSTGRES_PASSWORD", "pqrs"),
        )
    )


def build_views_sql(alias: str = "src") -> list[str]:
    """SQL de vistas (DuckDB) sobre tablas adjuntas ``alias``."""
    p = alias
    return [
        "DROP VIEW IF EXISTS vw_pqrs_por_territorio;",
        f"""
CREATE VIEW vw_pqrs_por_territorio AS
SELECT
    t.tipo,
    t.nombre,
    t.codigo,
    COUNT(*) FILTER (WHERE p.estado_clasificacion = 'ACEPTADA') AS aceptadas,
    COUNT(*) FILTER (WHERE p.estado_clasificacion LIKE 'RECHAZADA%') AS rechazadas,
    COUNT(*) FILTER (WHERE p.estado_gestion = 'RESPONDIDA') AS gestionadas,
    COUNT(*) FILTER (WHERE p.estado_gestion = 'PENDIENTE') AS pendientes,
    COUNT(*) FILTER (WHERE p.estado_gestion = 'VENCIDA') AS vencidas
FROM {p}.pqrs AS p
JOIN {p}.dim_territorio AS t ON p.territorio_id = t.id
GROUP BY t.tipo, t.nombre, t.codigo;
""",
        "DROP VIEW IF EXISTS vw_pqrs_pendientes_priorizadas;",
        f"""
CREATE VIEW vw_pqrs_pendientes_priorizadas AS
SELECT
    p.id,
    p.tipo,
    p.nivel_riesgo,
    p.fecha_limite,
    p.fecha_limite - CURRENT_DATE AS dias_restantes,
    CASE
        WHEN p.fecha_limite < CURRENT_DATE THEN 'VENCIDA'
        WHEN p.fecha_limite - CURRENT_DATE <= 2 THEN 'URGENTE'
        WHEN p.fecha_limite - CURRENT_DATE <= 5 THEN 'PROXIMA'
        ELSE 'NORMAL'
    END AS urgencia
FROM {p}.pqrs AS p
WHERE p.estado_gestion = 'PENDIENTE'
  AND p.estado_clasificacion = 'ACEPTADA';
""",
    ]


def refresh_warehouse(duckdb_path: str | None = None) -> Path:
    """
    Instala extensión postgres, adjunta la BD OLTP y recrea vistas analíticas.

    Retorna la ruta del fichero DuckDB usado.
    """
    path_str = duckdb_path or os.environ.get(
        "WAREHOUSE_DUCKDB_PATH", str(Path("data") / "pqrs_warehouse.duckdb")
    )
    out = Path(path_str)
    out.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(out))
    try:
        con.execute("INSTALL postgres;")
        con.execute("LOAD postgres;")
    except Exception as exc:
        msg = "No se pudo cargar la extensión postgres de DuckDB"
        raise RuntimeError(msg) from exc

    attach = _postgres_attach_string()
    try:
        con.execute("DETACH src")
    except Exception:
        pass

    con.execute(f"ATTACH '{attach}' AS src (TYPE POSTGRES, READ_ONLY);")

    for sql in build_views_sql("src"):
        con.execute(sql)

    con.close()
    return out
