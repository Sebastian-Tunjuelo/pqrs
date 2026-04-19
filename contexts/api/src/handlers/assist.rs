use std::time::Duration;

use axum::{extract::State, Json};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::domain::models::PqrsDetail;
use crate::error::ApiError;
use crate::state::AppState;

#[derive(Debug, Deserialize)]
pub struct AssistPqrsBody {
    pub pqrs_id: Uuid,
}

#[derive(Debug, Serialize)]
pub struct AssistReply {
    pub respuesta: String,
    pub modelo: String,
}

#[derive(Debug, Serialize)]
struct OllamaChatRequest<'a> {
    model: &'a str,
    messages: Vec<OllamaMessage<'a>>,
    stream: bool,
}

#[derive(Debug, Serialize)]
struct OllamaMessage<'a> {
    role: &'a str,
    content: String,
}

#[derive(Debug, Deserialize)]
struct OllamaChatResponse {
    message: OllamaAssistantMessage,
}

#[derive(Debug, Deserialize)]
struct OllamaAssistantMessage {
    content: String,
}

fn ollama_url() -> String {
    std::env::var("OLLAMA_URL").unwrap_or_else(|_| "http://127.0.0.1:11434".to_string())
}

fn ollama_model() -> String {
    std::env::var("OLLAMA_MODEL").unwrap_or_else(|_| "llama3.2:3b".to_string())
}

async fn load_pqrs(pool: &sqlx::PgPool, id: Uuid) -> Result<PqrsDetail, ApiError> {
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
    .fetch_optional(pool)
    .await?;

    match row {
        Some(r) => Ok(r),
        None => Err(ApiError::not_found("PQRS no encontrada")),
    }
}

async fn ollama_chat(system: &str, user: &str) -> Result<String, ApiError> {
    let base = ollama_url();
    let model = ollama_model();
    let url = format!("{}/api/chat", base.trim_end_matches('/'));

    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(120))
        .build()
        .map_err(|e| ApiError::internal(format!("cliente HTTP: {e}")))?;

    let body = OllamaChatRequest {
        model: &model,
        messages: vec![
            OllamaMessage {
                role: "system",
                content: system.to_string(),
            },
            OllamaMessage {
                role: "user",
                content: user.to_string(),
            },
        ],
        stream: false,
    };

    let res = client
        .post(&url)
        .json(&body)
        .send()
        .await
        .map_err(|e| ApiError::bad_gateway(format!("no se pudo contactar Ollama ({url}): {e}")))?;

    if !res.status().is_success() {
        let status = res.status();
        let txt = res.text().await.unwrap_or_default();
        let head: String = txt.chars().take(400).collect();
        return Err(ApiError::bad_gateway(format!(
            "Ollama respondió {status}: {head}"
        )));
    }

    let parsed: OllamaChatResponse = res.json().await.map_err(|e| {
        ApiError::bad_gateway(format!("respuesta Ollama no es JSON válido: {e}"))
    })?;

    Ok(parsed.message.content)
}

pub async fn explicar_rechazo(
    State(state): State<AppState>,
    Json(body): Json<AssistPqrsBody>,
) -> Result<Json<AssistReply>, ApiError> {
    let p = load_pqrs(&state.pool, body.pqrs_id).await?;
    let modelo = ollama_model();

    let system = r#"Eres un asistente institucional de la Alcaldía de Medellín (Colombia).
Explicas con tono respetuoso y claro por qué una PQRS pudo ser clasificada como rechazada o qué implica su estado de clasificación.
No inventes hechos externos al texto suministrado; si falta información, dilo.
Responde en español, en párrafos breves."#;

    let razon = p
        .razon_rechazo
        .as_deref()
        .unwrap_or("(no hay texto de rechazo registrado en el sistema)");
    let user = format!(
        "Datos de la PQRS:\n\
        - id_externo: {:?}\n\
        - tipo: {:?}\n\
        - estado_clasificacion: {}\n\
        - estado_gestion: {:?}\n\
        - nivel_riesgo: {:?}\n\
        - confianza_clasificacion: {:?}\n\
        - razon_rechazo (sistema): {}\n\
        - texto ciudadano (contenido):\n{}\n\n\
        Pregunta del usuario: ¿Por qué pudo haber sido rechazada o qué significa esta clasificación? Resume causas probables y próximos pasos recomendables.",
        p.id_externo,
        p.tipo,
        p.estado_clasificacion,
        p.estado_gestion,
        p.nivel_riesgo,
        p.confianza_clasificacion,
        razon,
        p.contenido
    );

    let respuesta = ollama_chat(system, &user).await?;
    Ok(Json(AssistReply { respuesta, modelo }))
}

pub async fn mensaje_gestion(
    State(state): State<AppState>,
    Json(body): Json<AssistPqrsBody>,
) -> Result<Json<AssistReply>, ApiError> {
    let p = load_pqrs(&state.pool, body.pqrs_id).await?;
    let modelo = ollama_model();

    let system = r#"Eres un asistente que redacta borradores de mensaje interno para el equipo de gestión de PQRS en la Alcaldía de Medellín.
El tono es profesional, directo y colaborativo. No inventes datos que no estén en el contexto.
Salida: un único borrador listo para copiar y pegar (asunto breve en una línea, luego cuerpo)."#;

    let user = format!(
        "Redacta un borrador para el equipo de gestión sobre el siguiente caso:\n\
        - id_externo: {:?}\n\
        - tipo: {:?}\n\
        - estado_clasificacion: {}\n\
        - estado_gestion: {:?}\n\
        - nivel_riesgo: {:?}\n\
        - fecha_limite: {:?}\n\
        - razon_rechazo (si aplica): {:?}\n\
        - texto ciudadano:\n{}\n\n\
        Objetivo: priorizar acciones, riesgos y coordinación entre secretarías si aplica.",
        p.id_externo,
        p.tipo,
        p.estado_clasificacion,
        p.estado_gestion,
        p.nivel_riesgo,
        p.fecha_limite,
        p.razon_rechazo,
        p.contenido
    );

    let respuesta = ollama_chat(system, &user).await?;
    Ok(Json(AssistReply { respuesta, modelo }))
}
