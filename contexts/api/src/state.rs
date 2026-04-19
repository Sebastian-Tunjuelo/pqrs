use redis::aio::ConnectionManager;
use sqlx::PgPool;

#[derive(Clone)]
pub struct AppState {
    pub pool: PgPool,
    pub redis: Option<ConnectionManager>,
    /// Base URL del microservicio Python `python -m banco_qa.embedding_server` (POST /embed).
    pub embedding_url: Option<String>,
}
