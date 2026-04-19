use axum::{
    routing::{get, patch, post},
    Router,
};

use crate::handlers::{alertas, assist, banco_qa, dashboard, health, pqrs, secretarias};
use crate::state::AppState;

/// Rutas bajo prefijo `/api/v1`.
pub fn api_v1_router(state: AppState) -> Router {
    Router::new()
        .route("/health", get(health::get_health))
        .route("/alertas", get(alertas::list_alertas))
        .route("/pqrs", get(pqrs::list_pqrs))
        .route("/pqrs/historial/aceptadas", get(pqrs::historial_aceptadas))
        .route("/pqrs/historial/rechazadas", get(pqrs::historial_rechazadas))
        .route("/pqrs/gestion/respondidas", get(pqrs::gestion_respondidas))
        .route("/pqrs/gestion/pendientes", get(pqrs::gestion_pendientes))
        .route("/pqrs/pendientes/prioridad", get(pqrs::pendientes_prioridad))
        .route(
            "/pqrs/pending-validation",
            get(pqrs::pending_validation),
        )
        .route(
            "/assist/ollama/explicar-rechazo",
            post(assist::explicar_rechazo),
        )
        .route("/assist/ollama/mensaje-gestion", post(assist::mensaje_gestion))
        .route("/pqrs/:id/summary", get(pqrs::get_pqrs_summary))
        .route("/pqrs/:id/validate", patch(pqrs::validate_pqrs))
        .route("/pqrs/:id", get(pqrs::get_pqrs))
        .route("/dashboard/territorios", get(dashboard::territorios))
        .route("/dashboard/metricas", get(dashboard::metricas))
        .route("/secretarias", get(secretarias::list_secretarias))
        .route(
            "/secretarias/:codigo/pqrs",
            get(secretarias::pqrs_por_secretaria),
        )
        .route("/banco-qa", get(banco_qa::list_banco_qa))
        .route("/banco-qa/buscar", post(banco_qa::buscar_banco_qa))
        .route(
            "/banco-qa/buscar-semantico",
            post(banco_qa::buscar_semantico),
        )
        .with_state(state)
}
