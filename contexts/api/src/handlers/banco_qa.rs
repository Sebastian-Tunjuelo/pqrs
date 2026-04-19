use axum::{extract::State, Json};

use crate::domain::models::{BancoQaBuscarBody, BancoQaRow};
use crate::error::ApiError;
use crate::state::AppState;

pub async fn list_banco_qa(
    State(state): State<AppState>,
) -> Result<Json<Vec<BancoQaRow>>, ApiError> {
    let rows = sqlx::query_as::<_, BancoQaRow>(
        r#"
        SELECT id, pregunta, respuesta, secretaria_codigo, tags, veces_consultada
        FROM banco_qa
        ORDER BY id
        LIMIT 500
        "#,
    )
    .fetch_all(&state.pool)
    .await?;
    Ok(Json(rows))
}

pub async fn buscar_banco_qa(
    State(state): State<AppState>,
    Json(body): Json<BancoQaBuscarBody>,
) -> Result<Json<Vec<BancoQaRow>>, ApiError> {
    let q = body.query.trim();
    if q.is_empty() {
        return Err(ApiError::bad_request("query no puede estar vacío"));
    }
    let pattern = format!("%{q}%");
    let rows = sqlx::query_as::<_, BancoQaRow>(
        r#"
        SELECT id, pregunta, respuesta, secretaria_codigo, tags, veces_consultada
        FROM banco_qa
        WHERE
            pregunta ILIKE $1
            OR respuesta ILIKE $1
            OR secretaria_codigo ILIKE $1
            OR COALESCE(array_to_string(tags, ' '), '') ILIKE $1
        ORDER BY id
        LIMIT 50
        "#,
    )
    .bind(&pattern)
    .fetch_all(&state.pool)
    .await?;
    Ok(Json(rows))
}
