"""Job: refrescar DuckDB OLAP desde PostgreSQL (cada ~15 min vía cron).

Ejecución:
    python -m warehouse.jobs.refresh_warehouse
"""

from __future__ import annotations

from warehouse.infrastructure.duckdb_refresher import refresh_warehouse


def main() -> None:
    path = refresh_warehouse()
    print(f"Warehouse DuckDB actualizado: {path}")


if __name__ == "__main__":
    main()
