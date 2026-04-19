use axum::{extract::State, Json};
use serde_json::{json, Map, Value};

use crate::domain::models::{MetricasDashboard, TerritorioDashboardRow};
use crate::error::ApiError;
use crate::state::AppState;

pub async fn territorios(
    State(state): State<AppState>,
) -> Result<Json<Vec<TerritorioDashboardRow>>, ApiError> {
    let rows = sqlx::query_as::<_, TerritorioDashboardRow>(
        r#"
        SELECT
            t.id,
            t.tipo::text AS tipo,
            t.codigo,
            t.nombre,
            COUNT(p.id)::bigint AS pqrs_count,
            COUNT(p.id) FILTER (WHERE p.estado_gestion = 'PENDIENTE')::bigint AS pendientes,
            COUNT(p.id) FILTER (WHERE p.estado_gestion = 'EN_TRAMITE')::bigint AS en_tramite,
            COUNT(p.id) FILTER (WHERE p.estado_gestion = 'RESPONDIDA')::bigint AS respondidas,
            COUNT(p.id) FILTER (WHERE p.estado_gestion = 'VENCIDA')::bigint AS vencidas,
            ST_AsGeoJSON(t.geometria)::text AS geojson
        FROM dim_territorio t
        LEFT JOIN pqrs p ON p.territorio_id = t.id
        GROUP BY t.id, t.tipo, t.codigo, t.nombre, t.geometria
        ORDER BY t.tipo, t.codigo
        "#,
    )
    .fetch_all(&state.pool)
    .await?;
    Ok(Json(rows))
}

pub async fn metricas(State(state): State<AppState>) -> Result<Json<MetricasDashboard>, ApiError> {
    let row: (i64, i64, i64, i64, i64) = sqlx::query_as(
        r#"
        SELECT
            (SELECT COUNT(*)::bigint FROM pqrs) AS total_pqrs,
            (SELECT COUNT(*)::bigint FROM pqrs WHERE estado_gestion = 'PENDIENTE') AS pendientes_gestion,
            (SELECT COUNT(*)::bigint FROM pqrs WHERE estado_gestion = 'EN_TRAMITE') AS en_tramite,
            (SELECT COUNT(*)::bigint FROM pqrs WHERE estado_gestion = 'RESPONDIDA') AS respondidas,
            (SELECT COUNT(*)::bigint FROM pqrs WHERE estado_gestion = 'VENCIDA') AS vencidas
        "#,
    )
    .fetch_one(&state.pool)
    .await?;

    let niveles: Vec<(Option<String>, i64)> = sqlx::query_as(
        r#"
        SELECT nivel_riesgo::text, COUNT(*)::bigint
        FROM pqrs
        GROUP BY nivel_riesgo
        "#,
    )
    .fetch_all(&state.pool)
    .await?;

    let mut por_nivel: Map<String, Value> = Map::new();
    for (k, v) in niveles {
        let key = k.unwrap_or_else(|| "SIN_CLASIFICAR".to_string());
        por_nivel.insert(key, json!(v));
    }

    Ok(Json(MetricasDashboard {
        total_pqrs: row.0,
        pendientes_gestion: row.1,
        en_tramite: row.2,
        respondidas: row.3,
        vencidas: row.4,
        por_nivel_riesgo: Value::Object(por_nivel),
    }))
}
