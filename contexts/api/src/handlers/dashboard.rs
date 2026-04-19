use axum::{extract::State, Json};
use chrono::NaiveDate;
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

    let promedio: Option<f64> = sqlx::query_scalar(
        r#"
        SELECT AVG(
            EXTRACT(EPOCH FROM (COALESCE(p.updated_at, p.created_at) - p.fecha_radicado)) / 86400.0
        )::float8
        FROM pqrs p
        WHERE p.estado_gestion = 'RESPONDIDA'
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

    let mut por_riesgo: Map<String, Value> = Map::new();
    for (k, v) in &niveles {
        let key = k.clone().unwrap_or_else(|| "SIN_CLASIFICAR".to_string());
        por_riesgo.insert(key, json!(v));
    }
    let por_nivel_val = Value::Object(por_riesgo.clone());

    let tipos: Vec<(Option<String>, i64)> = sqlx::query_as(
        r#"
        SELECT tipo::text, COUNT(*)::bigint
        FROM pqrs
        GROUP BY tipo
        "#,
    )
    .fetch_all(&state.pool)
    .await?;

    let mut por_tipo: Map<String, Value> = Map::new();
    for (k, v) in tipos {
        let key = k.unwrap_or_else(|| "?".to_string());
        por_tipo.insert(key, json!(v));
    }

    let tasa: Option<f64> = sqlx::query_scalar(
        r#"
        SELECT (
            COUNT(*) FILTER (
                WHERE p.validation_status = 'VALIDATED'
                AND NOT EXISTS (
                    SELECT 1 FROM pqrs_historial h
                    WHERE h.pqrs_id = p.id AND h.estado_nuevo = 'CORRECTION_REQUESTED'
                )
            )::float8
            / NULLIF(COUNT(*) FILTER (WHERE p.validation_status = 'VALIDATED'), 0)::float8
        )
        FROM pqrs p
        "#,
    )
    .fetch_one(&state.pool)
    .await?;

    let tendencia_rows: Vec<(NaiveDate, i64)> = sqlx::query_as(
        r#"
        SELECT
            (date_trunc('week', p.fecha_radicado AT TIME ZONE 'UTC'))::date AS semana,
            COUNT(*)::bigint AS total
        FROM pqrs p
        GROUP BY 1
        ORDER BY 1 DESC
        LIMIT 8
        "#,
    )
    .fetch_all(&state.pool)
    .await
    .unwrap_or_default();

    let tendencia_vals: Vec<Value> = tendencia_rows
        .into_iter()
        .rev()
        .map(|(semana, total)| json!({ "semana": semana.to_string(), "total": total }))
        .collect();
    let tendencia_semanal = Value::Array(tendencia_vals);

    Ok(Json(MetricasDashboard {
        total_pqrs: row.0,
        pendientes: row.1,
        pendientes_gestion: row.1,
        en_tramite: row.2,
        respondidas: row.3,
        vencidas: row.4,
        promedio_dias_respuesta: promedio,
        por_tipo: Value::Object(por_tipo),
        por_riesgo: por_nivel_val.clone(),
        por_nivel_riesgo: por_nivel_val,
        tasa_clasificacion_correcta: tasa,
        tendencia_semanal,
    }))
}
