from warehouse.infrastructure.duckdb_refresher import build_views_sql


def test_build_views_sql_referencia_adjunto() -> None:
    stmts = build_views_sql("src")
    joined = "\n".join(stmts)
    assert "vw_pqrs_por_territorio" in joined
    assert "vw_pqrs_pendientes_priorizadas" in joined
    assert "src.pqrs" in joined
    assert "src.dim_territorio" in joined
