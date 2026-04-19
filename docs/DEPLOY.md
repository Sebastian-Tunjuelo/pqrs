# Despliegue y operación (referencia)

Este documento describe **cómo preparar un entorno** (local o servidor propio). No automatiza despliegue a ningún proveedor cloud: el proyecto está pensado para **self-hosted** (Docker Compose, VM propia, etc.), alineado con `ARCHITECTURE.md` (stack gratuito / sin API keys de pago).

## 1. Orden recomendado (primera vez)

1. **Variables**: copiar `.env.example` → `.env` y revisar `DATABASE_URL`, puertos y `NEXT_PUBLIC_API_URL`.
2. **Infra**: `docker compose up -d` (Postgres/PostGIS, Redis, Ollama).
3. **Esquema OLTP**: en `contexts/warehouse`, con `DATABASE_URL` en formato SQLAlchemy, por ejemplo:
   - `postgresql+psycopg://pqrs:pqrs@localhost:5433/pqrs` (puerto host por defecto en `docker-compose.yml`)
   - `alembic upgrade head`
4. **Dimensiones**: ejecutar contra la misma base los SQL de `data/seed/` (`seed_dim_secretaria.sql`, `seed_dim_territorio.sql` u otros que uses).
5. **Demo de datos**: `make demo` (200 PQRS sintéticas; requiere pasos 3–4).
6. **API Rust**: `cd contexts/api && cargo run` (puerto `PORT` o 8080).
7. **Frontend**: `cd contexts/presentation && npm install && npm run dev`.
8. **Orquestación** (opcional): worker Redis + grafo LangGraph (`python -m orchestration worker` desde entorno con dependencias instaladas).
9. **Modelo LLM**: `make pull-model` o `bash scripts/pull-ollama-model.sh` cuando Ollama esté arriba.

## 2. Comprobaciones rápidas

- API: `GET /api/v1/health` → `{"status":"ok"}`.
- E2E: con la API levantada, `make test` (pytest + httpx en `e2e/tests`).

## 3. Producción (orientación)

- **Postgres**: backups, `max_connections`, disco para PostGIS.
- **API**: compilar release (`cargo build --release`), variable `DATABASE_URL`, TLS terminado en reverse proxy (nginx, Caddy, Traefik).
- **Next.js**: `npm run build && npm start` detrás del mismo proxy o subdominio.
- **Redis / Ollama**: red privada; no exponer Ollama a Internet sin autenticación.
- **Secretos**: solo `.env` o secret manager del host; no commitear credenciales.

## 4. Windows

`Makefile` asume **bash** (Git Bash, WSL o Linux). En PowerShell puro, ejecuta los mismos pasos manualmente usando los comandos del `README.md`.

**Puerto Postgres:** si `psql` o Python fallan con “password authentication failed” para `pqrs` usando `localhost:5432`, suele haber **otro Postgres local** ocupando 5432. El Compose del repo usa por defecto el host **5433**; alinea `DATABASE_URL` y `POSTGRES_PORT` (ver `.env.example`). Prueba rápida: `.\scripts\verify_local.ps1`.
