# PQRS Medellín

Sistema de referencia para **gestión de PQRS** (peticiones, quejas, reclamos y sugerencias), alineado a flujos tipo **Alcaldía de Medellín** y **Ley 1755 de 2015**: ingestión de datos, clasificación asistida por IA, priorización, ruteo a secretarías, almacenamiento en **PostgreSQL**, **API REST en Rust (Axum + SQLx)**, interfaz **Next.js 14**, orquestación con **LangGraph** y **Redis**, y **banco de preguntas y respuestas** para apoyo al funcionario.

Este repositorio es un **monorepo por contextos acotados (DDD)**. El contrato técnico y el plan de trabajo detallado están en [`ARCHITECTURE.md`](ARCHITECTURE.md). Para asistentes de código (arranque rápido, puertos y rutas) use [`AGENTS.md`](AGENTS.md).

---

## Contenido funcional (resumen)

| Área | Descripción |
|------|-------------|
| **Historial** | Consulta de PQRS con filtros y detalle. |
| **Gestión** | Cola de validación humana de clasificación IA, alertas por plazo, tablas de respondidas y prioridad. |
| **Dashboard** | Indicadores y visualización geoespacial (GeoJSON de comunas/corregimientos). |
| **Banco Q&A** | Búsqueda y consulta de respuestas tipo guía (semillas en `data/seed/` y glosarios). |
| **Asistente** | Borradores y apoyo vía **Ollama** (modelo local, sin API de pago obligatoria). |

**Restricción de diseño:** el proyecto está pensado para **operación gratuita o self-hosted** (Ollama local, Postgres y Redis en Docker, sin dependencias de nube de pago en el núcleo).

---

## Stack técnico

| Capa | Tecnología |
|------|------------|
| Base de datos OLTP | PostgreSQL 16 + PostGIS (Docker) |
| Cola / jobs | Redis 7 |
| Inferencia local | Ollama |
| Backend HTTP | Rust, Axum, SQLx, Tokio |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Mapas | Leaflet, react-leaflet |
| Gráficos | Plotly.js |
| Dominio y ETL | Python 3.11+ (Pydantic, contextos por carpeta) |
| Migraciones | Alembic en `contexts/warehouse` |
| Orquestación de agentes | LangGraph (Python), workers contra Redis |

---

## Requisitos previos

| Herramienta | Uso |
|-------------|-----|
| **Docker Desktop** (o motor compatible) | Postgres, Redis, Ollama |
| **Python 3.11+** | Paquetes `shared-kernel`, `contexts/*`, scripts de demo y seeds |
| **Rust** (`rustup`, `cargo`) | Compilar y ejecutar `contexts/api` |
| **Node.js 20+** y **npm** | `contexts/presentation` |
| **GNU Make** y **Bash** (Linux, macOS, WSL) | Objetivos del `Makefile` |

En **Windows nativo**, los pasos equivalentes están en **PowerShell** (scripts en `scripts/`). En máquinas con otro PostgreSQL en el puerto **5432**, este proyecto publica Postgres del Compose en el host en el puerto **5433** por defecto; use siempre la misma URL en variables de entorno (véase [`.env.example`](.env.example)).

---

## Inicio rápido

### Opción A — Windows (recomendado en el repo)

Desde la **raíz** del repositorio:

1. **Infraestructura y datos de demostración** (espera Postgres, Alembic, dimensiones, banco Q&A y ~200 PQRS demo):

   ```powershell
   .\scripts\verify_local.ps1
   ```

2. **Worker de síntesis** (resúmenes IA en detalle; requiere Redis y Ollama con el modelo indicado en `.env.example`, p. ej. `llama3.2:3b`):

   ```powershell
   .\scripts\_run_summary_worker.ps1
   ```

3. **API Rust** (otra terminal), con `DATABASE_URL` y, si aplica, `REDIS_URL`:

   ```powershell
   cd contexts\api
   $env:DATABASE_URL = "postgresql://pqrs:pqrs@localhost:5433/pqrs?sslmode=disable"
   $env:REDIS_URL = "redis://127.0.0.1:6379/0"
   cargo run
   ```

4. **Frontend** (otra terminal):

   ```powershell
   cd contexts\presentation
   ```

   Cree `contexts/presentation/.env.local` con al menos:

   ```env
   NEXT_PUBLIC_API_URL=http://127.0.0.1:8080
   ```

   Luego:

   ```powershell
   npm install
   npm run dev
   ```

   Abra **http://localhost:3000**.

**Atajo:** `.\scripts\start_stack.ps1` intenta levantar Docker (si hace falta), el worker de síntesis, la API y Next en ventanas separadas.

### Opción B — Linux / macOS (Make + Bash)

1. **Docker**

   ```bash
   make up
   # o: docker compose up -d
   ```

2. **Migraciones y seeds**  
   Instale `contexts/warehouse`, defina `DATABASE_URL` con **psycopg** (véase `.env.example`) y ejecute `alembic upgrade head`. Aplique los SQL de `data/seed/` según `Makefile` / documentación de seeds.

3. **Datos demo** (~200 PQRS):

   ```bash
   export DATABASE_URL=postgresql://pqrs:pqrs@localhost:5433/pqrs?sslmode=disable
   make demo
   ```

4. **Modelo Ollama** (opcional pero necesario para IA local):

   ```bash
   make pull-model
   ```

5. **API y Next** como en la sección Windows, adaptando rutas y `export` en lugar de `$env:`.

---

## Variables de entorno

Copie [`.env.example`](.env.example) a `.env` (o configure su entorno de despliegue) y revise como mínimo:

| Variable | Rol |
|----------|-----|
| `DATABASE_URL` | Conexión Postgres para la API (SQLx), scripts Python y Alembic |
| `NEXT_PUBLIC_API_URL` | URL base de la API expuesta al navegador (Next.js) |
| `REDIS_URL` | Cola de síntesis y orquestación cuando esté habilitada |
| `OLLAMA_URL` / `OLLAMA_MODEL` | Inferencia local para asistente y workers |

Detalles adicionales (`API_URL`, `E2E_API_URL`, `NEXT_PUBLIC_DEMO_OFFICER_NAME`, etc.) están comentados en `.env.example`.

---

## Estructura del repositorio

| Ruta | Contenido |
|------|-----------|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Visión DDD, bounded contexts, endpoints y plan de trabajo |
| [`AGENTS.md`](AGENTS.md) | Guía breve para asistentes: puertos, comandos y diagnóstico |
| `shared-kernel/` | Eventos y tipos compartidos (Python) |
| `contexts/ingestion/` | ETL y publicación hacia Redis |
| `contexts/classification/` | Clasificación y reglas de calidad |
| `contexts/prioritization/` | Riesgo y plazos (Ley 1755) |
| `contexts/routing/` | Recomendación de secretaría |
| `contexts/warehouse/` | Alembic, esquema y herramientas de almacén |
| `contexts/api/` | Servicio HTTP Axum + SQLx |
| `contexts/presentation/` | Aplicación Next.js (App Router) |
| `contexts/banco_qa/` | Utilidades para sembrar el banco Q&A |
| `orchestration/` | LangGraph y workers |
| `glosarios/` | YAML de ofensividad, riesgo, routing y Q&A |
| `data/seed/` | SQL de dimensiones y datos de referencia |
| `data/geojson/` | Límites territoriales para el dashboard |
| `scripts/` | Verificación local, demo, arranque de API/Next/worker |
| `e2e/` | Pruebas HTTP (pytest) contra la API |
| [`docs/DEPLOY.md`](docs/DEPLOY.md) | Notas de despliegue self-hosted |

---

## Desarrollo y calidad

### Makefile (entornos con Bash)

| Objetivo | Descripción |
|----------|-------------|
| `make up` / `make down` | Inicia o detiene los servicios de Docker Compose |
| `make demo` | Inserta PQRS de demostración (`scripts/demo_seed_pqrs.py --purge`) |
| `make demo-full` | `make demo` y descarga de modelo Ollama |
| `make test` | Suite e2e contra la API (requiere API en ejecución) |
| `make lint` | Ruff, Black, formateo frontend y Rust según `scripts/lint.sh` |
| `make seed` | Recordatorio de comandos para dimensiones y banco Q&A |

### Pre-commit

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Hooks habituales: **Black**, **Ruff**, **Prettier** (presentación), **rustfmt** (API).

### API en Windows (compilación)

Si `cargo` falla por enlazador, instale **Visual Studio Build Tools** con la carga de trabajo de desarrollo de escritorio en C++. El repositorio incluye `scripts\build_api_windows.cmd` como ayuda.

---

## Despliegue

Guía orientativa para entornos propios: [`docs/DEPLOY.md`](docs/DEPLOY.md).

---

## Documentación complementaria

- **Arquitectura y dominio:** [`ARCHITECTURE.md`](ARCHITECTURE.md)  
- **Onboarding para IA / troubleshooting:** [`AGENTS.md`](AGENTS.md)  
- **Variables:** [`.env.example`](.env.example)

---

## Problemas frecuentes

1. **Página en blanco en `localhost:3000`** — Confirme `npm run dev` y que el puerto 3000 no esté ocupado por otro proceso.  
2. **Error de contraseña Postgres** — Suele indicar conexión al puerto equivocado; use **5433** hacia el contenedor si así está definido en Compose.  
3. **502 o timeout en “Resumen IA”** — Compruebe `REDIS_URL` en la API, el worker `_run_summary_worker.ps1` y que Ollama tenga el modelo cargado.  
4. **E2E o pytest con rutas mezcladas** — Ejecute las pruebas **desde el directorio** de cada paquete, como indica `AGENTS.md`.

---

## Historial de entregas (tarjetas de trabajo)

El proyecto se ha ido construyendo por fases (bootstrap, kernel compartido, ingestion, glosarios, clasificación, priorización, ruteo, warehouse, orquestación, API, frontend, banco Q&A, demo y e2e). El orden y los criterios globales están descritos al final de [`ARCHITECTURE.md`](ARCHITECTURE.md).
