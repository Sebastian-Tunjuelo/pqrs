use std::net::SocketAddr;

use axum::http::header::{HeaderValue, AUTHORIZATION, CONTENT_TYPE};
use axum::http::{HeaderName, Method};
use axum::Router;
use redis::aio::ConnectionManager;
use sqlx::postgres::PgPoolOptions;
use tower_http::cors::{AllowOrigin, CorsLayer};
use tower_http::trace::TraceLayer;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};

mod co_calendar;
mod domain;
mod error;
mod handlers;
mod infrastructure;
mod routes;
mod state;

use routes::api_v1_router;
use state::AppState;

#[tokio::main]
async fn main() {
    tracing_subscriber::registry()
        .with(EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info")))
        .with(tracing_subscriber::fmt::layer())
        .init();

    let database_url = std::env::var("DATABASE_URL").unwrap_or_else(|_| {
        "postgresql://pqrs:pqrs@localhost:5432/pqrs?sslmode=disable".to_string()
    });

    let pool = PgPoolOptions::new()
        .max_connections(10)
        .connect(&database_url)
        .await
        .expect("conectar a PostgreSQL (DATABASE_URL)");

    let redis = match std::env::var("REDIS_URL") {
        Ok(url) => match redis::Client::open(url.as_str()) {
            Ok(client) => match ConnectionManager::new(client).await {
                Ok(cm) => Some(cm),
                Err(e) => {
                    tracing::warn!(?e, "no se pudo conectar a Redis");
                    None
                }
            },
            Err(e) => {
                tracing::warn!(?e, "REDIS_URL inválida");
                None
            }
        },
        Err(_) => {
            tracing::info!("REDIS_URL no definida: síntesis bajo demanda deshabilitada");
            None
        }
    };

    let embedding_url = std::env::var("EMBEDDING_URL")
        .ok()
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty());

    let state = AppState {
        pool,
        redis,
        embedding_url,
    };

    let origins = [
        HeaderValue::from_static("http://localhost:3000"),
        HeaderValue::from_static("http://127.0.0.1:3000"),
    ];
    let cors = CorsLayer::new()
        .allow_origin(AllowOrigin::list(origins))
        .allow_methods([
            Method::GET,
            Method::POST,
            Method::PATCH,
            Method::PUT,
            Method::DELETE,
            Method::OPTIONS,
        ])
        .allow_headers([
            HeaderName::from_static("content-type"),
            AUTHORIZATION,
            CONTENT_TYPE,
        ]);

    let app = Router::new()
        .nest("/api/v1", api_v1_router(state))
        .layer(TraceLayer::new_for_http())
        .layer(cors);

    let port: u16 = std::env::var("PORT")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(8080);
    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .expect("bind listener");

    tracing::info!("API escuchando en http://{addr}");
    axum::serve(listener, app).await.expect("serve");
}
