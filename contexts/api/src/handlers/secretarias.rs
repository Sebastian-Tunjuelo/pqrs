use axum::{
    extract::{Path, Query, State},
    Json,
};

use crate::domain::models::{Paginated, PqrsListItem, SecretariaRow};
use crate::error::ApiError;
use crate::handlers::pqrs::PageQuery;
use crate::state::AppState;

pub async fn list_secretarias(
    State(state): State<AppState>,
) -> Result<Json<Vec<SecretariaRow>>, ApiError> {
    let rows = sqlx::query_as::<_, SecretariaRow>(
        r#"
        SELECT codigo, nombre, activa
        FROM dim_secretaria
        WHERE COALESCE(activa, true)
        ORDER BY codigo
        "#,
    )
    .fetch_all(&state.pool)
    .await?;
    Ok(Json(rows))
}

pub async fn pqrs_por_secretaria(
    State(state): State<AppState>,
    Path(codigo): Path<String>,
    Query(q): Query<PageQuery>,
) -> Result<Json<Paginated<PqrsListItem>>, ApiError> {
    let codigo = codigo.trim().to_uppercase();
    if codigo.is_empty() || codigo.len() > 10 {
        return Err(ApiError::bad_request("código de secretaría inválido"));
    }

    let exists: bool = sqlx::query_scalar(
        "SELECT EXISTS(SELECT 1 FROM dim_secretaria WHERE codigo = $1)",
    )
    .bind(&codigo)
    .fetch_one(&state.pool)
    .await?;

    if !exists {
        return Err(ApiError::not_found("secretaría no encontrada"));
    }

    let per = q.per_page.clamp(1, 100) as i64;
    let page = q.page.max(1);
    let offset = (page - 1) as i64 * per;

    let total: i64 = sqlx::query_scalar(
        r#"
        SELECT COUNT(*)::bigint
        FROM pqrs p
        INNER JOIN pqrs_secretaria ps ON ps.pqrs_id = p.id AND ps.secretaria_codigo = $1
        "#,
    )
    .bind(&codigo)
    .fetch_one(&state.pool)
    .await?;

    let data_sql = r#"
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
            p.confianza_clasificacion::float8 AS confianza_clasificacion,
            p.validation_status::text AS validation_status,
            $1::varchar AS secretaria_codigo,
            ds.nombre AS secretaria_nombre
        FROM pqrs p
        INNER JOIN pqrs_secretaria ps ON ps.pqrs_id = p.id AND ps.secretaria_codigo = $1
        INNER JOIN dim_secretaria ds ON ds.codigo = $1
        ORDER BY p.fecha_radicado DESC
        LIMIT $2 OFFSET $3
        "#;

    let items = sqlx::query_as::<_, PqrsListItem>(&data_sql)
    .bind(&codigo)
    .bind(per)
    .bind(offset)
    .fetch_all(&state.pool)
    .await?;

    Ok(Json(Paginated {
        items,
        total,
        page,
        per_page: per as u32,
    }))
}
