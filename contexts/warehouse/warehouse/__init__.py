"""Warehouse bounded context (OLTP migrations + DuckDB OLAP)."""

from warehouse.domain.content_hash import compute_contenido_hash
from warehouse.infrastructure.duckdb_refresher import refresh_warehouse

__all__ = ["compute_contenido_hash", "refresh_warehouse"]
