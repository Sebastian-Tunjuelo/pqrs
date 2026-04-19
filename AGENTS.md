# Contexto para asistentes (IA) — PQRS Medellín

Este archivo existe para que **cualquier asistente de código** entienda en minutos **qué es el repo**, **cómo levantarlo** y **dónde está cada pieza**. El detalle de dominio y contratos está en [`ARCHITECTURE.md`](ARCHITECTURE.md) y la guía humana en [`README.md`](README.md).

---

## Qué es el proyecto

Monorepo **DDD** para gestión de **PQRS** (peticiones, quejas, reclamos, sugerencias) alineado a flujos tipo Alcaldía de Medellín / Ley 1755: **ingestión**, **clasificación**, **priorización**, **ruteo**, **warehouse** (Postgres + Alembic, DuckDB opcional), **API REST en Rust (Axum + SQLx)**, **frontend Next.js 14 (App Router)**, **orquestación LangGraph** con Redis, y asistente vía **Ollama**.

---

## Puertos y URLs (local típico)

| Servicio | Host | Notas |
|----------|------|--------|
| Postgres (Docker) | `localhost:5433` | Mapeado desde 5432 del contenedor. **No uses 5432** en Windows si hay otro Postgres local. |
| Redis | `localhost:6379` | |
| Ollama | `localhost:11434` | Modelo sugerido: `llama3.2:3b` (`docker compose exec ollama ollama pull …`). |
| API Rust | `http://127.0.0.1:8080` | Prefijo REST: `/api/v1`. Health: `GET /api/v1/health`. |
| Next.js (dev) | `http://localhost:3000` | Requiere `npm run dev` en `contexts/presentation`. |

**`DATABASE_URL` habitual para API y scripts:**  
`postgresql://pqrs:pqrs@localhost:5433/pqrs?sslmode=disable`

**Alembic (Python/psycopg) en `contexts/warehouse`:**  
`postgresql+psycopg://pqrs:pqrs@localhost:5433/pqrs`

---

## Cómo levantar el stack (orden obligatorio)

### 0. Requisitos

- Docker Desktop (motor en marcha).
- Python **3.11+** (`py`, `py -3.12` o `python` en PATH; el repo resuelve con `scripts/_resolve_python.ps1`).
- **Rust** (`cargo`) para la API.
- **Node 20+** y **npm** para el frontend.

### 1. Infraestructura Docker

Desde la **raíz del repo** (`pqrs/`):

```powershell
docker compose up -d
```

Servicios: `postgres` (PostGIS), `redis`, `ollama`.

### 2. Esquema Postgres + dimensiones + demo

**PowerShell**, raíz del repo:

```powershell
.\scripts\verify_local.ps1
```

Hace: espera Postgres → `pip install -e contexts/warehouse` → **Alembic `upgrade head`** → SQL `data/seed/seed_dim_secretaria.sql`, `seed_dim_territorio.sql` → **~200 PQRS demo** (`scripts/demo_seed_pqrs.py --purge`).  
**No arranca** la API ni Next; solo deja la BD lista.

### 3. Worker de síntesis (Resumen IA en detalle PQRS)

La API encola trabajos en Redis (`pqrs.summary.jobs`); sin este proceso verá **502** al pedir síntesis.

```powershell
.\scripts\_run_summary_worker.ps1
```

(Requiere Docker con **Redis** y **Ollama** en marcha, y modelo `llama3.2:3b` u otro compatible.)

### 4. API Rust (obligatoria para el frontend útil)

```powershell
cd contexts\api
$env:DATABASE_URL = "postgresql://pqrs:pqrs@localhost:5433/pqrs?sslmode=disable"
$env:REDIS_URL = "redis://127.0.0.1:6379/0"
cargo run
```

`REDIS_URL` habilita síntesis bajo demanda y cola de resúmenes. Por defecto escucha en **8080**.

### 5. Next.js (interfaz web)

En **otra** terminal, raíz del repo o carpeta presentation:

```powershell
cd contexts\presentation
```

Asegura `contexts/presentation/.env.local` con al menos:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8080
```

Luego:

```powershell
npm install   # o npm ci si hay package-lock
npm run dev
```

Abre **`http://localhost:3000`**. Si la pestaña queda **en blanco**, casi siempre falta `npm run dev` o el puerto **3000** está ocupado por un Node viejo.

### Atajo (Windows): abrir API + Next en ventanas

```powershell
.\scripts\start_stack.ps1
```

o doble clic en `scripts\start_stack.cmd`.  
Levanta Docker (si hace falta), espera Postgres, y lanza **`_run_summary_worker.ps1`**, **`_run_api.ps1`** y **`_run_next.ps1`** en ventanas separadas. **`_run_next.ps1`** intenta liberar el puerto **3000** si hay un Node previo.

### Verificación / CI local (sin depender de `run_all.ps1`)

Si el usuario pide “correr todo” **por comandos explícitos**: Docker + pasos de `verify_local` + `pip install -e` por paquete + `pytest` **desde cada carpeta** (`shared-kernel/tests`, `contexts/ingestion/tests`, …) para evitar conflicto del paquete `tests` + `cargo test` en `contexts/api` + `npm run build` en `contexts/presentation`. Ver historial de la conversación o `scripts/run_all.ps1` como referencia ordenada.

---

## Mapa mínimo del repositorio

| Ruta | Rol |
|------|-----|
| `contexts/api/` | API Axum, rutas `/api/v1/...`, SQLx Postgres. |
| `contexts/presentation/` | Next.js: `/`, `/historial`, `/gestion`, `/dashboard`, `/asistente`, `/pqrs/[id]` (detalle texto completo). |
| `contexts/warehouse/` | Alembic + migraciones esquema `pqrs`, etc. |
| `data/seed/*.sql` | Dimensiones sembradas por `verify_local.ps1`. |
| `scripts/demo_seed_pqrs.py` | PQRS sintéticas demo (arquetipos aceptada / ilegible / ofensivo). |
| `scripts/verify_local.ps1` | Orquesta BD local (Compose + Alembic + seeds + demo). |
| `scripts/start_stack.ps1` | Arranque Docker + ventanas worker síntesis + API + Next. |
| `scripts/_run_summary_worker.ps1` | Worker Redis/Ollama para síntesis en detalle PQRS. |
| `scripts/_resolve_python.ps1` | Resuelve ejecutable Python 3.11+ para los scripts. |
| `shared-kernel/` | Eventos y tipos compartidos (Python). |
| `contexts/ingestion`, `classification`, `prioritization`, `routing` | Dominio Python por contexto. |
| `orchestration/` | LangGraph + worker Redis. |
| `e2e/` | Pytest contra API HTTP. |
| `glosarios/` | YAML (ofensivo, riesgo, routing). |

---

## Endpoints útiles (API)

- `GET /api/v1/health`
- `GET /api/v1/pqrs` (paginado)
- `GET /api/v1/pqrs/:id` (detalle, texto completo)
- Listados de historial / gestión / prioridad (ver `contexts/api/src/routes.rs`)

El frontend usa `NEXT_PUBLIC_API_URL` (fetch desde servidor o cliente según la página).

---

## Problemas frecuentes (para IA al depurar)

1. **`localhost:3000` en blanco** — No está corriendo Next (`npm run dev`) o hay proceso zombie en 3000. Liberar con `Get-NetTCPConnection -LocalPort 3000` y matar `node`, o usar `_run_next.ps1`.
2. **Error de contraseña Postgres** — Suele ser conexión al **5432** local equivocado; usar **5433** (host) hacia el contenedor.
3. **API sin tablas** — Ejecutar `verify_local.ps1` (Alembic + seeds).
4. **Pytest “ModuleNotFoundError: tests.xxx”** al mezclar rutas — Ejecutar `pytest` **desde dentro** de cada paquete (`cd shared-kernel; pytest tests`).
5. **502 en “Resumen IA” / timeout de síntesis** — Falta **`_run_summary_worker.ps1`** o la API sin **`REDIS_URL`**; Ollama saturado (muchas inferencias a la vez).

---

## Convenciones para cambios de código

- Cambios **acotados** al pedido; no refactors masivos.
- Mantener estilo e imports del archivo tocado.
- No añadir documentación markdown nueva salvo que el usuario la pida (este archivo es la excepción explícita para onboarding de IA).

---

## Documentación relacionada

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — arquitectura y contratos.
- [`.env.example`](.env.example) — variables de entorno de referencia.
