use axum::{extract::State, Json};
use serde::Deserialize;

use crate::domain::models::{BancoQaBuscarBody, BancoQaRow, BancoQaSemanticRow};
use crate::error::ApiError;
use crate::state::AppState;

#[derive(Debug, Deserialize)]
struct EmbedServiceResponse {
    embedding: Vec<f32>,
}

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

pub async fn buscar_semantico(
    State(state): State<AppState>,
    Json(body): Json<BancoQaBuscarBody>,
) -> Result<Json<Vec<BancoQaSemanticRow>>, ApiError> {
    let q = body.query.trim();
    if q.is_empty() {
        return Err(ApiError::bad_request("query no puede estar vacío"));
    }

    let base = state
        .embedding_url
        .as_deref()
        .ok_or_else(|| {
            ApiError::bad_request(
                "EMBEDDING_URL no configurada. Arranque `python -m banco_qa.embedding_server` y exporte EMBEDDING_URL=http://127.0.0.1:8765",
            )
        })?
        .trim_end_matches('/');

    let url = format!("{base}/embed");
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(60))
        .build()
        .map_err(|e| ApiError::internal(format!("reqwest: {e}")))?;

    let resp = client
        .post(&url)
        .json(&serde_json::json!({ "text": q }))
        .send()
        .await
        .map_err(|e| ApiError::bad_gateway(format!("embedding service: {e}")))?;

    if !resp.status().is_success() {
        let txt = resp.text().await.unwrap_or_default();
        return Err(ApiError::bad_gateway(format!(
            "embedding service HTTP error: {txt}"
        )));
    }

    let parsed: EmbedServiceResponse = resp
        .json()
        .await
        .map_err(|e| ApiError::bad_gateway(format!("embedding JSON: {e}")))?;

    if parsed.embedding.len() != 384 {
        return Err(ApiError::bad_gateway(format!(
            "embedding dim {} != 384",
            parsed.embedding.len()
        )));
    }

    let lit = format!(
        "[{}]",
        parsed
            .embedding
            .iter()
            .map(|x| x.to_string())
            .collect::<Vec<_>>()
            .join(",")
    );

    let rows = sqlx::query_as::<_, BancoQaSemanticRow>(
        r#"
        SELECT
            id,
            pregunta,
            respuesta,
            secretaria_codigo,
            tags,
            veces_consultada,
            (1 - (embedding <=> $1::vector))::float8 AS similarity
        FROM banco_qa
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> $1::vector
        LIMIT 5
        "#,
    )
    .bind(&lit)
    .fetch_all(&state.pool)
    .await?;

    Ok(Json(rows))
}
