# PQRS Medellín

Monorepo del sistema multi-agente DDD para gestión de PQRS (Medellín), descrito en detalle en [**`ARCHITECTURE.md`**](ARCHITECTURE.md): ingestion, clasificación, priorización (Ley 1755), ruteo, warehouse, API Rust (Axum), frontend Next.js, orquestación LangGraph y banco Q&A.

**Stack local:** Docker (Postgres/PostGIS, Redis, Ollama), Python 3.11+, Node 20+ (frontend), Rust (API). Sin servicios de pago obligatorios.

---

## Requisitos

| Componente | Uso |
|--------------|-----|
| Docker / Docker Compose | Postgres, Redis, Ollama |
| Python 3.11+ | Contextos Python, seeds, e2e, demo |
| Node.js + npm | `contexts/presentation` |
| Rust (cargo) | `contexts/api` |
| GNU Make + bash | Targets del `Makefile` (o ejecuta los comandos a mano) |

### Windows: Postgres en el puerto 5433

Si en el PC ya corre **otro PostgreSQL en el puerto 5432**, las conexiones a `localhost:5432` **no** son el contenedor Docker y verás errores de contraseña para el usuario `pqrs`. Por eso el `docker-compose.yml` publica por defecto el host **`5433`**. Usa siempre la misma URL en `DATABASE_URL` (ver `.env.example`).

**Script todo-en-uno (PowerShell, desde la raíz del repo):**

```powershell
.\scripts\verify_local.ps1
```

Hace: Compose → espera Postgres → Alembic → seeds `dim_*` → **banco Q&A** → 200 PQRS demo. No arranca la API ni Next (indica comandos al final).

**Solo sembrar banco Q&A** (use esto si en **CMD** le falló `Get-Content`: ese comando es de **PowerShell**):

```bat
scripts\seed_banco_qa.cmd
```

**Asistente Ollama (Next.js):** la UI usa la ruta interna **`/api/assist/ollama`** (lee la PQRS en la API Rust y habla con Ollama). No hace falta recompilar la API solo por el asistente; sí hace falta **Ollama arriba** y el modelo (`docker compose exec ollama ollama pull llama3.2:3b`). En `contexts/presentation/.env.local` puede definir `API_URL`, `OLLAMA_URL` y `OLLAMA_MODEL` (ver `.env.example`).

---

## Variables de entorno

Copia **`cp .env.example .env`** y ajusta al menos:

- **`DATABASE_URL`**: Postgres para la API (sqlx), scripts y Alembic (acepta también `postgresql+psycopg://…` en herramientas Python).
- **`NEXT_PUBLIC_API_URL`**: URL pública de la API para el frontend (p. ej. `http://localhost:8080`).
- **`REDIS_URL`**: orquestación / ingestion si publicas eventos.

---

## Estructura del repositorio

| Ruta | Contenido |
|------|-----------|
| `ARCHITECTURE.md` | Contrato maestro (DDD, endpoints, plan de cards). |
| `shared-kernel/` | Eventos Pydantic, enums, IDs. |
| `contexts/ingestion` | ETL MEData → Redis. |
| `contexts/classification` | Clasificación (prefiltro + Ollama). |
| `contexts/prioritization` | Riesgo + SLA Colombia. |
| `contexts/routing` | Recomendación de secretaría. |
| `contexts/warehouse` | Alembic + DuckDB refresh. |
| `contexts/api` | API REST Axum + SQLx. |
| `contexts/presentation` | Next.js 14 (App Router). |
| `contexts/banco_qa` | CLI para cargar `glosarios/banco_qa.yaml` → tabla `banco_qa`. |
| `orchestration/` | Grafo LangGraph + worker Redis. |
| `glosarios/` | YAML ofensivo, riesgo, routing, banco Q&A. |
| `data/geojson/` | Límites comunas/corregimientos (dashboard). |
| `data/seed/` | SQL de dimensiones. |
| `scripts/` | Demo PQRS, lint, pull modelo Ollama. |
| `e2e/` | Pytest + httpx contra la API. |

---

## Puesta en marcha (local)

### 1. Kernel compartido (Python)

```bash
pip install -e ./shared-kernel
```

Instala cada contexto según necesites, por ejemplo:

```bash
pip install -e ./contexts/ingestion
pip install -e ./contexts/warehouse
# … classification, prioritization, routing, orchestration, banco_qa
```

### 2. Servicios Docker

```bash
make up
# o: docker compose up -d
```

### 3. Migraciones y seeds de base de datos

Con Postgres del Compose accesible (host **5433** por defecto; ver `docker-compose.yml` y `.env.example`, usuario/clave `pqrs`):

```bash
cd contexts/warehouse
pip install -e .
export DATABASE_URL=postgresql+psycopg://pqrs:pqrs@localhost:5433/pqrs
alembic upgrade head
```

Luego aplica los SQL de `data/seed/` (secretaría, territorio) con `psql` o tu cliente preferido.

### 4. Demo de 200 PQRS (opcional)

Requiere dimensiones cargadas. Desde la **raíz** del repo:

```bash
export DATABASE_URL=postgresql://pqrs:pqrs@localhost:5433/pqrs?sslmode=disable
make demo
```

Ver también `scripts/demo_seed_pqrs.py --help`.

### 5. API Rust

**Windows:** hace falta el **linker MSVC** (p. ej. *Visual Studio Build Tools* con carga *Desktop development with C++* / herramientas VC). Tras instalar Rust (`rustup`), puedes compilar con:

```bat
scripts\build_api_windows.cmd build
scripts\build_api_windows.cmd run
```

O manualmente: abrir *x64 Native Tools Command Prompt* / ejecutar `vcvars64.bat` y luego `cargo build` en `contexts\api`.

Para ejecutar el binario (PowerShell), con Postgres en el puerto **5433**:

```powershell
cd contexts\api
$env:DATABASE_URL = "postgresql://pqrs:pqrs@127.0.0.1:5433/pqrs?sslmode=disable"
.\target\debug\pqrs-api.exe
```

**Linux/macOS:**

```bash
cd contexts/api
export DATABASE_URL=postgresql://pqrs:pqrs@localhost:5433/pqrs?sslmode=disable
cargo run
```

### 6. Frontend Next.js

```bash
cd contexts/presentation
npm install
export NEXT_PUBLIC_API_URL=http://localhost:8080
npm run dev
```

GeoJSON del mapa: la app sirve `/api/geojson/comunas` leyendo `data/geojson/` (ruta relativa al monorepo).

### 7. Orquestación (opcional)

Con Redis y los contextos Python instalados:

```bash
export REDIS_URL=redis://localhost:6379/0
python -m orchestration worker
```

### 8. Modelo Ollama

```bash
make pull-model
# o: bash scripts/pull-ollama-model.sh
```

---

## Makefile (resumen)

| Target | Descripción |
|--------|-------------|
| `make up` / `make down` | Levanta o detiene Docker Compose. |
| `make seed` | Indica comandos para dimensiones y banco Q&A. |
| `make demo` | Inserta 200 PQRS demo (`--purge` de filas demo previas). |
| `make demo-full` | `demo` + descarga de modelo Ollama. |
| `make test` | E2E HTTP contra la API (requiere API en marcha). |
| `make lint` | Ruff, black, opcionalmente `cargo` y Prettier (ver `scripts/lint.sh`). |
| `make pull-model` | Script bash para Ollama. |

---

## Calidad y pre-commit

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Hooks: **black**, **ruff**, **prettier** (solo `contexts/presentation`, mirror de pre-commit), **rustfmt** (API, requiere `cargo` en PATH).

---

## Despliegue

Guía de referencia (self-hosted, sin proveedor concreto): **[`docs/DEPLOY.md`](docs/DEPLOY.md)**.

---

## Documentación histórica (cards)

- **Card 1**: bootstrap monorepo, Compose, Makefile, pre-commit.
- **Card 2**: `shared-kernel` (enums, eventos, JSON Schema).
- **Cards 3–8**: ingestion, glosarios, classification, prioritization, routing, warehouse.
- **Card 9**: orquestación LangGraph + worker Redis.
- **Card 10**: API Rust (`/api/v1/...`).
- **Card 11**: Next.js + Tailwind + Leaflet + Plotly.
- **Card 12**: builder YAML → `banco_qa`.
- **Card 13**: `scripts/demo_seed_pqrs.py`, e2e pytest, `make demo` / `make test`.

Para criterios globales y plan de cards completos, ver **`ARCHITECTURE.md`** (secciones finales).
