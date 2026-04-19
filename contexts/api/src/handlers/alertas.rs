use axum::{extract::State, Json};
use chrono::{DateTime, Local, NaiveDate, Utc};
use serde::Serialize;
use sqlx::FromRow;
use uuid::Uuid;

use crate::co_calendar::dias_habiles_restantes_hasta;
use crate::error::ApiError;
use crate::state::AppState;

#[derive(Debug, FromRow)]
struct AlertaDbRow {
    id: i64,
    pqrs_id: Uuid,
    tipo: String,
    mensaje: Option<String>,
    activa: bool,
    creado_en: DateTime<Utc>,
    fecha_limite: Option<NaiveDate>,
    id_externo: Option<String>,
    nivel_riesgo: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct AlertaItem {
    pub id: i64,
    pub pqrs_id: Uuid,
    pub tipo: String,
    pub mensaje: Option<String>,
    pub activa: bool,
    pub creado_en: DateTime<Utc>,
    pub fecha_limite: Option<NaiveDate>,
    pub id_externo: Option<String>,
    pub nivel_riesgo: Option<String>,
    pub dias_habiles_restantes: i32,
}

pub async fn list_alertas(
    State(state): State<AppState>,
) -> Result<Json<Vec<AlertaItem>>, ApiError> {
    let hoy = Local::now().date_naive();
    let rows = sqlx::query_as::<_, AlertaDbRow>(
        r#"
        SELECT
            a.id,
            a.pqrs_id,
            a.tipo,
            a.mensaje,
            a.activa,
            a.creado_en,
            p.fecha_limite,
            p.id_externo,
            p.nivel_riesgo
        FROM pqrs_alertas a
        INNER JOIN pqrs p ON p.id = a.pqrs_id
        WHERE a.activa = true
        ORDER BY
            p.fecha_limite ASC NULLS LAST,
            CASE p.nivel_riesgo
                WHEN 'CRITICO' THEN 1
                WHEN 'ALTO' THEN 2
                WHEN 'MEDIO' THEN 3
                WHEN 'BAJO' THEN 4
                ELSE 5
            END,
            a.creado_en DESC
        "#,
    )
    .fetch_all(&state.pool)
    .await?;

    let out: Vec<AlertaItem> = rows
        .into_iter()
        .map(|r| {
            let dhr = match r.fecha_limite {
                Some(lim) => dias_habiles_restantes_hasta(hoy, lim),
                None => 0,
            };
            AlertaItem {
                id: r.id,
                pqrs_id: r.pqrs_id,
                tipo: r.tipo,
                mensaje: r.mensaje,
                activa: r.activa,
                creado_en: r.creado_en,
                fecha_limite: r.fecha_limite,
                id_externo: r.id_externo,
                nivel_riesgo: r.nivel_riesgo,
                dias_habiles_restantes: dhr,
            }
        })
        .collect();

    Ok(Json(out))
}
