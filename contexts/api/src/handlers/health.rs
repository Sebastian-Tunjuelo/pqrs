use axum::extract::State;
use axum::Json;
use serde_json::json;

use crate::state::AppState;

fn ollama_base() -> String {
    std::env::var("OLLAMA_URL").unwrap_or_else(|_| "http://127.0.0.1:11434".to_string())
}

pub async fn get_health(State(state): State<AppState>) -> Json<serde_json::Value> {
    let pg_ok = sqlx::query_scalar::<_, i32>("SELECT 1")
        .fetch_one(&state.pool)
        .await
        .is_ok();

    let redis_ok = if let Some(mut cm) = state.redis.clone() {
        redis::cmd("PING")
            .query_async::<String>(&mut cm)
            .await
            .is_ok()
    } else {
        false
    };

    let ollama_url = format!("{}/api/tags", ollama_base().trim_end_matches('/'));
    let ollama_ok = match reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(3))
        .build()
    {
        Ok(client) => client
            .get(&ollama_url)
            .send()
            .await
            .map(|r| r.status().is_success())
            .unwrap_or(false),
        Err(_) => false,
    };

    let overall = if pg_ok && redis_ok && ollama_ok {
        "ok"
    } else {
        "degraded"
    };

    Json(json!({
        "status": overall,
        "postgres": { "ok": pg_ok },
        "redis": { "ok": redis_ok },
        "ollama": { "ok": ollama_ok, "url": ollama_url },
    }))
}
