use std::time::Duration;

use axum::http::{HeaderMap, HeaderName, HeaderValue};
use axum::response::{IntoResponse, Response};
use axum::{
    extract::{Path, Query, State},
    Json,
};
use chrono::{NaiveDate, Utc, Datelike};
use redis::AsyncCommands;
use uuid::Uuid;

use crate::domain::models::{Paginated, PqrsDetail, PqrsListItem, PqrsSummaryResponse};
use crate::error::ApiError;
use crate::state::AppState;

#[derive(Debug, serde::Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ValidateAction {
    Validate,
    Reject,
    RequestCorrection,
}

#[derive(Debug, serde::Deserialize)]
pub struct ValidatePqrsBody {
    pub action: ValidateAction,
    pub officer_id: String,
    pub correction_note: Option<String>,
    pub override_secretaria: Option<String>,
}

#[derive(Debug, serde::Serialize)]
pub struct ValidatePqrsResponse {
    pub id: Uuid,
    pub validation_status: String,
}

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

#[derive(Debug, serde::Deserialize)]
pub struct PqrsListFilters {
    #[serde(default = "default_page")]
    pub page: u32,
    #[serde(default = "default_per_page")]
    pub per_page: u32,
    /// `validation_status` (enum en Postgres).
    pub estado: Option<String>,
    pub secretaria: Option<String>,
    pub riesgo: Option<String>,
    pub fecha_desde: Option<NaiveDate>,
    pub fecha_hasta: Option<NaiveDate>,
    /// P, Q, R, S o D.
    pub tipo: Option<String>,
    /// `estado_clasificacion` (ACEPTADA, RECHAZADA_*).
    pub estado_clasificacion: Option<String>,
    /// `estado_gestion` (PENDIENTE, EN_TRAMITE, …).
    pub estado_gestion: Option<String>,
}

fn parse_validation_status(raw: &str) -> Result<&'static str, ApiError> {
    match raw.trim() {
        "PENDING_VALIDATION" => Ok("PENDING_VALIDATION"),
        "VALIDATED" => Ok("VALIDATED"),
        "REJECTED_BY_OFFICER" => Ok("REJECTED_BY_OFFICER"),
        "CORRECTION_REQUESTED" => Ok("CORRECTION_REQUESTED"),
        _ => Err(ApiError::bad_request(
            "estado inválido: use PENDING_VALIDATION | VALIDATED | REJECTED_BY_OFFICER | CORRECTION_REQUESTED",
        )),
    }
}

fn parse_riesgo(raw: &str) -> Result<&'static str, ApiError> {
    match raw.trim().to_ascii_uppercase().as_str() {
        "CRITICO" => Ok("CRITICO"),
        "ALTO" => Ok("ALTO"),
        "MEDIO" => Ok("MEDIO"),
        "BAJO" => Ok("BAJO"),
        _ => Err(ApiError::bad_request("riesgo inválido")),
    }
}

fn parse_secretaria_codigo(raw: &str) -> Result<String, ApiError> {
    let c = raw.trim().to_uppercase();
    if !(2..=10).contains(&c.len()) || !c.chars().all(|x| x.is_ascii_alphanumeric()) {
        return Err(ApiError::bad_request("secretaria: código inválido"));
    }
    Ok(c)
}

fn parse_tipo_pqrs(raw: &str) -> Result<&'static str, ApiError> {
    match raw.trim().to_ascii_uppercase().as_str() {
        "P" => Ok("P"),
        "Q" => Ok("Q"),
        "R" => Ok("R"),
        "S" => Ok("S"),
        "D" => Ok("D"),
        _ => Err(ApiError::bad_request("tipo debe ser P, Q, R, S o D")),
    }
}

fn parse_estado_clasificacion(raw: &str) -> Result<&'static str, ApiError> {
    match raw.trim() {
        "ACEPTADA" => Ok("ACEPTADA"),
        "RECHAZADA_OFENSIVO" => Ok("RECHAZADA_OFENSIVO"),
        "RECHAZADA_NO_ENTENDIBLE" => Ok("RECHAZADA_NO_ENTENDIBLE"),
        _ => Err(ApiError::bad_request(
            "estado_clasificacion inválido (ACEPTADA | RECHAZADA_OFENSIVO | RECHAZADA_NO_ENTENDIBLE)",
        )),
    }
}

fn parse_estado_gestion(raw: &str) -> Result<&'static str, ApiError> {
    match raw.trim().to_ascii_uppercase().as_str() {
        "PENDIENTE" => Ok("PENDIENTE"),
        "EN_TRAMITE" => Ok("EN_TRAMITE"),
        "RESPONDIDA" => Ok("RESPONDIDA"),
        "VENCIDA" => Ok("VENCIDA"),
        _ => Err(ApiError::bad_request(
            "estado_gestion inválido (PENDIENTE | EN_TRAMITE | RESPONDIDA | VENCIDA)",
        )),
    }
}

fn build_pqrs_list_where(f: &PqrsListFilters) -> Result<String, ApiError> {
    let mut parts = vec!["TRUE".to_string()];
    if let Some(ref e) = f.estado {
        let v = parse_validation_status(e)?;
        parts.push(format!("p.validation_status = '{v}'::validation_status"));
    }
    if let Some(ref s) = f.secretaria {
        let c = parse_secretaria_codigo(s)?;
        parts.push(format!(
            "EXISTS (SELECT 1 FROM pqrs_secretaria ps WHERE ps.pqrs_id = p.id AND ps.secretaria_codigo = '{c}')"
        ));
    }
    if let Some(ref r) = f.riesgo {
        let rv = parse_riesgo(r)?;
        parts.push(format!("p.nivel_riesgo = '{rv}'"));
    }
    if let Some(d) = f.fecha_desde {
        parts.push(format!("p.fecha_radicado::date >= '{}'", d));
    }
    if let Some(d) = f.fecha_hasta {
        parts.push(format!("p.fecha_radicado::date <= '{}'", d));
    }
    if let Some(ref t) = f.tipo {
        let tv = parse_tipo_pqrs(t)?;
        parts.push(format!("p.tipo = '{tv}'"));
    }
    if let Some(ref ec) = f.estado_clasificacion {
        let v = parse_estado_clasificacion(ec)?;
        parts.push(format!("p.estado_clasificacion = '{v}'"));
    }
    if let Some(ref eg) = f.estado_gestion {
        let v = parse_estado_gestion(eg)?;
        parts.push(format!("p.estado_gestion = '{v}'"));
    }
    Ok(parts.join(" AND "))
}

const PQRS_DETAIL_SQL: &str = r#"
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
            p.updated_at,
            p.validation_status::text AS validation_status,
            p.summary_lead,
            p.summary_topics,
            p.summary_executive
        FROM pqrs p
        WHERE p.id = $1
"#;

async fn fetch_pqrs_detail(pool: &sqlx::PgPool, id: Uuid) -> Result<Option<PqrsDetail>, ApiError> {
    sqlx::query_as::<_, PqrsDetail>(PQRS_DETAIL_SQL)
        .bind(id)
        .fetch_optional(pool)
        .await
        .map_err(Into::into)
}

fn summary_topics_nonempty(topics: &Option<serde_json::Value>) -> bool {
    topics
        .as_ref()
        .and_then(|x| x.as_array())
        .map(|a| !a.is_empty())
        .unwrap_or(false)
}

fn has_complete_summary(d: &PqrsDetail) -> bool {
    d.summary_lead
        .as_ref()
        .map(|s| !s.trim().is_empty())
        .unwrap_or(false)
        && d
            .summary_executive
            .as_ref()
            .map(|s| !s.trim().is_empty())
            .unwrap_or(false)
        && summary_topics_nonempty(&d.summary_topics)
}

fn to_summary_response(d: &PqrsDetail) -> PqrsSummaryResponse {
    let temas: Vec<String> = d
        .summary_topics
        .as_ref()
        .and_then(|x| x.as_array())
        .map(|arr| {
            arr.iter()
                .filter_map(|v| v.as_str().map(str::to_string))
                .collect()
        })
        .unwrap_or_default();
    PqrsSummaryResponse {
        lead: d.summary_lead.clone().unwrap_or_default(),
        temas,
        resumen_ejecutivo: d.summary_executive.clone().unwrap_or_default(),
        pqrs_completa: d.contenido.clone(),
    }
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
    p.confianza_clasificacion::float8 AS confianza_clasificacion,
    p.validation_status::text AS validation_status,
    lead_sec.secretaria_codigo,
    lead_sec.secretaria_nombre
FROM pqrs p
LEFT JOIN LATERAL (
    SELECT ps.secretaria_codigo, d.nombre AS secretaria_nombre
    FROM pqrs_secretaria ps
    INNER JOIN dim_secretaria d ON d.codigo = ps.secretaria_codigo
    WHERE ps.pqrs_id = p.id
    ORDER BY ps.es_lider DESC NULLS LAST, ps.score DESC NULLS LAST
    LIMIT 1
) lead_sec ON true
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

use crate::co_calendar::cuenta_dias_habiles_entre;

#[derive(Debug, serde::Deserialize)]
pub struct CreatePqrsBody {
    pub tipo: String,
    pub contenido: String,
    pub nombre_solicitante: Option<String>,
    pub canal: Option<String>,
    pub secretaria_codigo: Option<String>,
}

#[derive(Debug, serde::Serialize)]
pub struct CreatePqrsResponse {
    pub id: Uuid,
    pub id_externo: String,
    pub fecha_radicado: chrono::DateTime<Utc>,
    pub fecha_limite: Option<NaiveDate>,
}

pub async fn create_pqrs(
    State(state): State<AppState>,
    Json(body): Json<CreatePqrsBody>,
) -> Result<Json<CreatePqrsResponse>, ApiError> {
    let tipo = parse_tipo_pqrs(&body.tipo)?;
    let contenido = body.contenido.trim().to_string();
    if contenido.is_empty() {
        return Err(ApiError::bad_request("contenido no puede estar vacío"));
    }

    // Calcular fecha_limite: 15 días hábiles desde hoy (Ley 1755)
    let hoy = chrono::Utc::now().date_naive();
    let mut fecha_limite = hoy;
    let mut habiles = 0;
    loop {
        fecha_limite += chrono::Duration::days(1);
        let dia = fecha_limite.weekday();
        if !matches!(dia, chrono::Weekday::Sat | chrono::Weekday::Sun) {
            habiles += 1;
        }
        if habiles >= 15 {
            break;
        }
    }

    let id = Uuid::new_v4();
    let canal = body.canal.as_deref().unwrap_or("telegram");
    let nombre = body.nombre_solicitante.as_deref().unwrap_or("Ciudadano");

    // Generar id_externo secuencial simple
    let seq: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM pqrs")
        .fetch_one(&state.pool)
        .await
        .unwrap_or(0);
    let id_externo = format!("TG-{:05}", seq + 1);

    let contenido_hash = {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        let mut h = DefaultHasher::new();
        contenido.hash(&mut h);
        format!("{:016x}", h.finish())
    };

    let metadata = serde_json::json!({
        "canal": canal,
        "nombre_solicitante": nombre,
    });

    sqlx::query(
        r#"
        INSERT INTO pqrs (
            id, id_externo, tipo, contenido, contenido_hash,
            fecha_radicado, fecha_limite,
            estado_clasificacion, estado_gestion, validation_status,
            metadata
        ) VALUES (
            $1, $2, $3, $4, $5,
            NOW(), $6,
            'ACEPTADA', 'PENDIENTE', 'PENDING_VALIDATION',
            $7
        )
        "#,
    )
    .bind(id)
    .bind(&id_externo)
    .bind(tipo)
    .bind(&contenido)
    .bind(&contenido_hash)
    .bind(fecha_limite)
    .bind(&metadata)
    .execute(&state.pool)
    .await?;

    // Si se indicó secretaría, validarla e insertarla en pqrs_secretaria
    if let Some(ref codigo) = body.secretaria_codigo {
        let c = codigo.trim().to_uppercase();
        if !c.is_empty() {
            let existe: bool = sqlx::query_scalar(
                "SELECT EXISTS(SELECT 1 FROM dim_secretaria WHERE codigo = $1 AND (activa IS NULL OR activa = true))"
            )
            .bind(&c)
            .fetch_one(&state.pool)
            .await
            .unwrap_or(false);

            if !existe {
                return Err(ApiError::bad_request(format!(
                    "Secretaría '{c}' no existe o está inactiva"
                )));
            }

            sqlx::query(
                r#"
                INSERT INTO pqrs_secretaria (pqrs_id, secretaria_codigo, es_lider, score, motivo)
                VALUES ($1, $2, true, 1.00, 'Seleccionada por ciudadano vía Telegram')
                "#,
            )
            .bind(id)
            .bind(&c)
            .execute(&state.pool)
            .await?;
        }
    }

    Ok(Json(CreatePqrsResponse {
        id,
        id_externo,
        fecha_radicado: chrono::Utc::now(),
        fecha_limite: Some(fecha_limite),
    }))
}

pub async fn list_pqrs(
    State(state): State<AppState>,
    Query(q): Query<PqrsListFilters>,
) -> Result<Response, ApiError> {
    let where_sql = format!("WHERE {}", build_pqrs_list_where(&q)?);
    let data = pqrs_paginated(
        &state.pool,
        &where_sql,
        "ORDER BY p.fecha_radicado DESC",
        q.page,
        q.per_page,
    )
    .await?;
    let mut headers = HeaderMap::new();
    if let Ok(hv) = HeaderValue::from_str(&data.total.to_string()) {
        headers.insert(HeaderName::from_static("x-total-count"), hv);
    }
    Ok((headers, Json(data)).into_response())
}

pub async fn get_pqrs(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<PqrsDetail>, ApiError> {
    let row = fetch_pqrs_detail(&state.pool, id).await?;

    match row {
        Some(r) => Ok(Json(r)),
        None => Err(ApiError::not_found("PQRS no encontrada")),
    }
}

pub async fn get_pqrs_summary(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<PqrsSummaryResponse>, ApiError> {
    let row = fetch_pqrs_detail(&state.pool, id).await?;
    let Some(ref d) = row else {
        return Err(ApiError::not_found("PQRS no encontrada"));
    };

    if has_complete_summary(d) {
        return Ok(Json(to_summary_response(d)));
    }

    let mut redis_cm = state.redis.clone().ok_or_else(|| {
        ApiError::bad_request(
            "Redis no configurado (REDIS_URL). Sin Redis no se puede disparar la síntesis.",
        )
    })?;

    let corr = Uuid::new_v4().to_string();
    let _: String = redis::cmd("XADD")
        .arg("pqrs.summary.jobs")
        .arg("*")
        .arg("correlation_id")
        .arg(&corr)
        .arg("pqrs_id")
        .arg(id.to_string())
        .query_async(&mut redis_cm)
        .await
        .map_err(|e| ApiError::internal(format!("Redis XADD: {e}")))?;

    let key = format!("pqrs:summary:result:{corr}");
    let mut saw_ok = false;
    // Ollama en CPU puede tardar >45 s; ~120 s da margen al worker de síntesis.
    for _ in 0..800u32 {
        let val: Option<String> = redis_cm
            .get(&key)
            .await
            .map_err(|e| ApiError::internal(format!("Redis GET: {e}")))?;
        if let Some(s) = val {
            let j: serde_json::Value =
                serde_json::from_str(&s).unwrap_or_else(|_| serde_json::json!({}));
            if let Some(err) = j.get("error") {
                let msg = err
                    .as_str()
                    .map(str::to_string)
                    .unwrap_or_else(|| err.to_string());
                return Err(ApiError::internal(format!("síntesis: {msg}")));
            }
            if j.get("ok").and_then(|v| v.as_bool()) == Some(true) {
                saw_ok = true;
                break;
            }
        }
        tokio::time::sleep(Duration::from_millis(150)).await;
    }

    if !saw_ok {
        return Err(ApiError::bad_gateway(
            "Timeout esperando síntesis. ¿Está corriendo `python -m classification.summary_redis_worker`?",
        ));
    }

    let d = fetch_pqrs_detail(&state.pool, id)
        .await?
        .ok_or_else(|| ApiError::not_found("PQRS no encontrada"))?;
    if !has_complete_summary(&d) {
        return Err(ApiError::internal(
            "La síntesis no se persistió correctamente en base de datos",
        ));
    }
    Ok(Json(to_summary_response(&d)))
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

pub async fn pending_validation(
    State(state): State<AppState>,
    Query(q): Query<PageQuery>,
) -> Result<Json<Paginated<PqrsListItem>>, ApiError> {
    let data = pqrs_paginated(
        &state.pool,
        "WHERE p.validation_status = 'PENDING_VALIDATION' AND p.estado_clasificacion = 'ACEPTADA'",
        "ORDER BY p.fecha_limite ASC NULLS LAST, p.fecha_radicado ASC",
        q.page,
        q.per_page,
    )
    .await?;
    Ok(Json(data))
}

pub async fn validate_pqrs(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
    Json(body): Json<ValidatePqrsBody>,
) -> Result<Json<ValidatePqrsResponse>, ApiError> {
    if body.officer_id.trim().is_empty() {
        return Err(ApiError::bad_request("officer_id es obligatorio"));
    }

    let new_status = match body.action {
        ValidateAction::Validate => "VALIDATED",
        ValidateAction::Reject => "REJECTED_BY_OFFICER",
        ValidateAction::RequestCorrection => "CORRECTION_REQUESTED",
    };

    let mut tx = state.pool.begin().await?;

    let current: Option<String> = sqlx::query_scalar(
        "SELECT validation_status::text FROM pqrs WHERE id = $1 FOR UPDATE",
    )
    .bind(id)
    .fetch_optional(&mut *tx)
    .await?;

    let Some(prev) = current else {
        return Err(ApiError::not_found("PQRS no encontrada"));
    };

    if prev != "PENDING_VALIDATION" && prev != "CORRECTION_REQUESTED" {
        return Err(ApiError::bad_request(
            "Solo se puede validar/rechazar/solicitar corrección cuando la PQRS está pendiente de validación o en corrección",
        ));
    }

    let action_label = match body.action {
        ValidateAction::Validate => "VALIDATE",
        ValidateAction::Reject => "REJECT",
        ValidateAction::RequestCorrection => "REQUEST_CORRECTION",
    };
    let nota = if let Some(n) = body.correction_note.as_ref().map(|s| s.trim()).filter(|s| !s.is_empty()) {
        format!("Acción: {action_label}. {n}")
    } else {
        format!("Acción: {action_label}")
    };

    let oid = body.officer_id.trim();
    let actor_short: String = oid.chars().take(50).collect();

    sqlx::query(
        r#"
        INSERT INTO pqrs_historial (pqrs_id, estado_anterior, estado_nuevo, actor, officer_id, nota)
        VALUES ($1, $2, $3, $4, $5, $6)
        "#,
    )
    .bind(id)
    .bind(&prev)
    .bind(new_status)
    .bind(&actor_short)
    .bind(oid)
    .bind(&nota)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        UPDATE pqrs
        SET validation_status = $1::validation_status,
            updated_at = NOW()
        WHERE id = $2
        "#,
    )
    .bind(new_status)
    .bind(id)
    .execute(&mut *tx)
    .await?;

    if let Some(ref codigo) = body.override_secretaria {
        let c = codigo.trim();
        if !c.is_empty() {
            let ok: bool = sqlx::query_scalar(
                r#"SELECT EXISTS(
                    SELECT 1 FROM dim_secretaria WHERE codigo = $1 AND (activa IS NULL OR activa = true)
                )"#,
            )
            .bind(c)
            .fetch_one(&mut *tx)
            .await?;

            if !ok {
                return Err(ApiError::bad_request(format!(
                    "Secretaría '{c}' no existe o está inactiva"
                )));
            }

            sqlx::query("UPDATE pqrs_secretaria SET es_lider = false WHERE pqrs_id = $1")
                .bind(id)
                .execute(&mut *tx)
                .await?;

            sqlx::query(
                r#"
                INSERT INTO pqrs_secretaria (pqrs_id, secretaria_codigo, es_lider, score, motivo)
                VALUES ($1, $2, true, 1.00, $3)
                ON CONFLICT (pqrs_id, secretaria_codigo) DO UPDATE
                SET es_lider = true, score = 1.00, motivo = EXCLUDED.motivo
                "#,
            )
            .bind(id)
            .bind(c)
            .bind(format!(
                "Ruteo corregido por funcionario {} (override manual)",
                body.officer_id.trim()
            ))
            .execute(&mut *tx)
            .await?;
        }
    }

    tx.commit().await?;

    Ok(Json(ValidatePqrsResponse {
        id,
        validation_status: new_status.to_string(),
    }))
}
