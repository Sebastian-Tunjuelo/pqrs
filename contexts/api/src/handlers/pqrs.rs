use axum::{
    extract::{Path, Query, State},
    Json,
};
use uuid::Uuid;

use crate::domain::models::{Paginated, PqrsDetail, PqrsListItem};
use crate::error::ApiError;
use crate::state::AppState;

#[derive(Debug, serde::Deserialize)]
pub struct PageQuery {
    #[serde(default = "default_page")]
    pub page: u32,
    #[serde(default = "default_per_page")]
    pub per_page: u32,
}

fn default_page() -> u32 {
    1
}

fn default_per_page() -> u32 {
    20
}

const PQRS_LIST_SELECT: &str = r#"
SELECT
    p.id,
    p.id_externo,
    p.tipo::text AS tipo,
    LEFT(p.contenido, 400) AS contenido,
    p.fecha_radicado,
    p.fecha_limite,
    p.estado_clasificacion,
    p.estado_gestion,
    p.nivel_riesgo,
    p.territorio_id,
    p.confianza_clasificacion::float8 AS confianza_clasificacion
FROM pqrs p
"#;

async fn pqrs_paginated(
    pool: &sqlx::PgPool,
    where_sql: &str,
    order_sql: &str,
    page: u32,
    per_page: u32,
) -> Result<Paginated<PqrsListItem>, ApiError> {
    let per = per_page.clamp(1, 500) as i64;
    let page = page.max(1);
    let offset = (page - 1) as i64 * per;

    let count_sql = format!("SELECT COUNT(*)::bigint FROM pqrs p {where_sql}");
    let total: i64 = sqlx::query_scalar(&count_sql).fetch_one(pool).await?;

    let data_sql = format!(
        "{PQRS_LIST_SELECT} {where_sql} {order_sql} LIMIT $1 OFFSET $2"
    );
    let items = sqlx::query_as::<_, PqrsListItem>(&data_sql)
        .bind(per)
        .bind(offset)
        .fetch_all(pool)
        .await?;

    Ok(Paginated {
        items,
        total,
        page,
        per_page: per as u32,
    })
}

pub async fn list_pqrs(
    State(state): State<AppState>,
    Query(q): Query<PageQuery>,
) -> Result<Json<Paginated<PqrsListItem>>, ApiError> {
    let data = pqrs_paginated(
        &state.pool,
        "",
        "ORDER BY p.fecha_radicado DESC",
        q.page,
        q.per_page,
    )
    .await?;
    Ok(Json(data))
}

pub async fn get_pqrs(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<PqrsDetail>, ApiError> {
    let row = sqlx::query_as::<_, PqrsDetail>(
        r#"
        SELECT
            p.id,
            p.id_externo,
            p.tipo::text AS tipo,
            p.contenido,
            p.contenido_hash,
            p.fecha_radicado,
            p.fecha_limite,
            p.estado_clasificacion,
            p.estado_gestion,
            p.nivel_riesgo,
            p.territorio_id,
            p.confianza_clasificacion::float8 AS confianza_clasificacion,
            p.razon_rechazo,
            p.metadata,
            p.created_at,
            p.updated_at
        FROM pqrs p
        WHERE p.id = $1
        "#,
    )
    .bind(id)
    .fetch_optional(&state.pool)
    .await?;

    match row {
        Some(r) => Ok(Json(r)),
        None => Err(ApiError::not_found("PQRS no encontrada")),
    }
}

pub async fn historial_aceptadas(
    State(state): State<AppState>,
    Query(q): Query<PageQuery>,
) -> Result<Json<Paginated<PqrsListItem>>, ApiError> {
    let data = pqrs_paginated(
        &state.pool,
        "WHERE p.estado_clasificacion = 'ACEPTADA'",
        "ORDER BY p.fecha_radicado DESC",
        q.page,
        q.per_page,
    )
    .await?;
    Ok(Json(data))
}

pub async fn historial_rechazadas(
    State(state): State<AppState>,
    Query(q): Query<PageQuery>,
) -> Result<Json<Paginated<PqrsListItem>>, ApiError> {
    let data = pqrs_paginated(
        &state.pool,
        "WHERE p.estado_clasificacion IN ('RECHAZADA_OFENSIVO', 'RECHAZADA_NO_ENTENDIBLE')",
        "ORDER BY p.fecha_radicado DESC",
        q.page,
        q.per_page,
    )
    .await?;
    Ok(Json(data))
}

pub async fn gestion_respondidas(
    State(state): State<AppState>,
    Query(q): Query<PageQuery>,
) -> Result<Json<Paginated<PqrsListItem>>, ApiError> {
    let data = pqrs_paginated(
        &state.pool,
        "WHERE p.estado_gestion = 'RESPONDIDA'",
        "ORDER BY p.updated_at DESC NULLS LAST, p.fecha_radicado DESC",
        q.page,
        q.per_page,
    )
    .await?;
    Ok(Json(data))
}

pub async fn gestion_pendientes(
    State(state): State<AppState>,
    Query(q): Query<PageQuery>,
) -> Result<Json<Paginated<PqrsListItem>>, ApiError> {
    let data = pqrs_paginated(
        &state.pool,
        "WHERE p.estado_gestion = 'PENDIENTE'",
        "ORDER BY p.fecha_limite ASC NULLS LAST, p.fecha_radicado ASC",
        q.page,
        q.per_page,
    )
    .await?;
    Ok(Json(data))
}

pub async fn pendientes_prioridad(
    State(state): State<AppState>,
    Query(q): Query<PageQuery>,
) -> Result<Json<Paginated<PqrsListItem>>, ApiError> {
    let data = pqrs_paginated(
        &state.pool,
        "WHERE p.estado_gestion IN ('PENDIENTE', 'EN_TRAMITE')",
        r#"ORDER BY
            CASE p.nivel_riesgo
                WHEN 'CRITICO' THEN 1
                WHEN 'ALTO' THEN 2
                WHEN 'MEDIO' THEN 3
                WHEN 'BAJO' THEN 4
                ELSE 5
            END,
            p.fecha_limite ASC NULLS LAST,
            p.fecha_radicado ASC"#,
        q.page,
        q.per_page,
    )
    .await?;
    Ok(Json(data))
}
