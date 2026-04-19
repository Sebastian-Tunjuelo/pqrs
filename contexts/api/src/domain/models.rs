use chrono::{DateTime, NaiveDate, Utc};
use serde::Serialize;
use sqlx::FromRow;
use uuid::Uuid;

#[derive(Debug, Serialize, FromRow)]
pub struct PqrsListItem {
    pub id: Uuid,
    pub id_externo: Option<String>,
    pub tipo: Option<String>,
    pub contenido: String,
    pub fecha_radicado: DateTime<Utc>,
    pub fecha_limite: Option<NaiveDate>,
    pub estado_clasificacion: String,
    pub estado_gestion: Option<String>,
    pub nivel_riesgo: Option<String>,
    pub territorio_id: Option<i32>,
    pub confianza_clasificacion: Option<f64>,
}

#[derive(Debug, Serialize, FromRow)]
pub struct PqrsDetail {
    pub id: Uuid,
    pub id_externo: Option<String>,
    pub tipo: Option<String>,
    pub contenido: String,
    pub contenido_hash: Option<String>,
    pub fecha_radicado: DateTime<Utc>,
    pub fecha_limite: Option<NaiveDate>,
    pub estado_clasificacion: String,
    pub estado_gestion: Option<String>,
    pub nivel_riesgo: Option<String>,
    pub territorio_id: Option<i32>,
    pub confianza_clasificacion: Option<f64>,
    pub razon_rechazo: Option<String>,
    pub metadata: Option<serde_json::Value>,
    pub created_at: Option<DateTime<Utc>>,
    pub updated_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Serialize, FromRow)]
pub struct SecretariaRow {
    pub codigo: String,
    pub nombre: String,
    pub activa: Option<bool>,
}

#[derive(Debug, Serialize, FromRow)]
pub struct TerritorioDashboardRow {
    pub id: i32,
    pub tipo: String,
    pub codigo: String,
    pub nombre: String,
    pub pqrs_count: i64,
    pub pendientes: i64,
    pub en_tramite: i64,
    pub respondidas: i64,
    pub vencidas: i64,
    /// GeoJSON string desde `ST_AsGeoJSON`, si hay geometría.
    pub geojson: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct MetricasDashboard {
    pub total_pqrs: i64,
    pub pendientes_gestion: i64,
    pub en_tramite: i64,
    pub respondidas: i64,
    pub vencidas: i64,
    pub por_nivel_riesgo: serde_json::Value,
}

#[derive(Debug, Serialize, FromRow)]
pub struct BancoQaRow {
    pub id: i32,
    pub pregunta: String,
    pub respuesta: String,
    pub secretaria_codigo: Option<String>,
    pub tags: Option<Vec<String>>,
    pub veces_consultada: Option<i32>,
}

#[derive(Debug, serde::Deserialize)]
pub struct BancoQaBuscarBody {
    pub query: String,
}

#[derive(Debug, Serialize)]
#[serde(bound(serialize = "T: Serialize"))]
pub struct Paginated<T> {
    pub items: Vec<T>,
    pub total: i64,
    pub page: u32,
    pub per_page: u32,
}
