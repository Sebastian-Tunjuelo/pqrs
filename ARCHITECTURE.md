# PROYECTO: PQRS-Medellín — Sistema Multi-Agente DDD

> **Instrucciones para VibeKanban**: Este es el `ARCHITECTURE.md` maestro. Cada card debe leerlo ANTES de ejecutar. Crea las cards en el orden de la sección "PLAN DE CARDS" al final de este documento. Respeta los bounded contexts — NO permitas que un agente modifique código fuera de su contexto.

---

## 1. OBJETIVO DE NEGOCIO

Sistema de gestión de PQRS (Peticiones, Quejas, Reclamos, Sugerencias) para la Secretaría de Desarrollo Económico de la Alcaldía de Medellín, con clasificación automática, enrutamiento multi-secretaría (26 dependencias) y cumplimiento de Ley 1755 de 2015.

**Entregables**:
1. ETL que consume MEData (API CKAN/DKAN + scraping fallback)
2. Pipeline multi-agente con Ollama `llama3.2:3b` + LangChain + LangGraph
3. Data warehouse limpio (DuckDB analítica + PostgreSQL OLTP)
4. Backend Rust (Axum) — API REST
5. Frontend Next.js con 4 vistas: historial, gestión, dashboard geoespacial, banco Q&A
6. Sistema de recomendación: PQRS → secretaría(s) competente(s)

**Restricciones**: TODO gratuito. Sin servicios pagos. Sin API keys de pago.

---

## 2. STACK TÉCNICO (INMUTABLE)

| Capa | Tecnología | Versión |
|---|---|---|
| LLM local | Ollama + `llama3.2:3b` | latest |
| Orquestación agentes | LangChain + LangGraph | ≥0.2 |
| ETL/Scraping | Python 3.11, httpx, BeautifulSoup4, pandas, pydantic | — |
| Backend | Rust, Axum 0.7, SQLx, Tokio | — |
| OLTP | PostgreSQL 16 + PostGIS | — |
| OLAP/Warehouse | DuckDB | ≥1.0 |
| Cola | Redis Streams | 7 |
| Frontend | Next.js 14 (App Router), TypeScript, TailwindCSS | — |
| Mapas | Leaflet + react-leaflet + GeoJSON Medellín | — |
| Gráficos | Plotly.js | — |
| Orquestación infra | Docker Compose | — |

**Prohibido**: OpenAI API, Anthropic API, servicios AWS pagos, MongoDB Atlas, Vercel Pro. Solo tiers gratuitos o self-hosted.

---

## 3. ARQUITECTURA DDD — BOUNDED CONTEXTS

Cada contexto tiene su propia carpeta, modelo de dominio, y NO comparte código con otros excepto por el `shared-kernel`.

```
pqrs-medellin/
├── shared-kernel/              # Tipos comunes, event bus schemas
│   ├── events/                 # JSON schemas de eventos de dominio
│   └── value_objects/          # PqrsId, CiudadanoId, SecretariaId
│
├── contexts/
│   ├── ingestion/              # [Python] ETL + scraping MEData
│   │   ├── domain/             # entities: RawPqrs, DataSource
│   │   ├── application/        # use cases: FetchFromMedata, ScrapeFallback
│   │   ├── infrastructure/     # CKAN client, BS4 scraper, Redis publisher
│   │   └── tests/
│   │
│   ├── classification/         # [Python] Filtro ofensivo/entendible
│   │   ├── domain/             # entities: ClassifiedPqrs, ClassificationVerdict
│   │   ├── application/        # ClassifyPqrsUseCase
│   │   ├── infrastructure/     # OllamaClient, GlossaryLoader
│   │   └── tests/
│   │
│   ├── prioritization/         # [Python] Ley 1755 + riesgo
│   │   ├── domain/             # entities: PrioritizedPqrs, Deadline, RiskLevel
│   │   ├── application/        # CalculateDeadline, AssessRisk
│   │   ├── infrastructure/     # Calendar (días hábiles Colombia)
│   │   └── tests/
│   │
│   ├── routing/                # [Python] PQRS → Secretaría(s)
│   │   ├── domain/             # entities: RoutingDecision, SecretariaMatch
│   │   ├── application/        # RecommendSecretaria (puede devolver N)
│   │   ├── infrastructure/     # secretarias_routing.yaml loader
│   │   └── tests/
│   │
│   ├── warehouse/              # [Python] ETL hacia warehouse
│   │   ├── domain/             # entities: FactPqrs, DimSecretaria, DimTiempo
│   │   ├── application/        # LoadToWarehouse, RefreshViews
│   │   └── infrastructure/     # DuckDB + Postgres writers
│   │
│   ├── api/                    # [Rust] Backend HTTP
│   │   ├── src/domain/         # modelos read (queries)
│   │   ├── src/application/    # handlers
│   │   ├── src/infrastructure/ # sqlx repos, duckdb readers
│   │   └── src/main.rs         # Axum router
│   │
│   └── presentation/           # [Next.js] Frontend
│       ├── app/
│       │   ├── historial/      # Vista 1
│       │   ├── gestion/        # Vista 2
│       │   ├── dashboard/      # Vista 3: mapas comunas/corregimientos
│       │   └── banco-qa/       # Vista 4
│       ├── components/
│       └── lib/
```

---

## 4. MODELO DE DOMINIO COMPARTIDO

### 4.1 Agregado raíz: `PQRS`

```python
from enum import Enum

class TipoPqrs(str, Enum):
    PETICION = "P"
    QUEJA = "Q"
    RECLAMO = "R"
    SUGERENCIA = "S"
    DENUNCIA = "D"

class EstadoClasificacion(str, Enum):
    PENDIENTE = "PENDIENTE"
    ACEPTADA = "ACEPTADA"
    RECHAZADA_OFENSIVO = "RECHAZADA_OFENSIVO"
    RECHAZADA_NO_ENTENDIBLE = "RECHAZADA_NO_ENTENDIBLE"

class NivelRiesgo(str, Enum):
    CRITICO = "CRITICO"
    ALTO = "ALTO"
    MEDIO = "MEDIO"
    BAJO = "BAJO"

class EstadoGestion(str, Enum):
    PENDIENTE = "PENDIENTE"
    EN_TRAMITE = "EN_TRAMITE"
    RESPONDIDA = "RESPONDIDA"
    VENCIDA = "VENCIDA"
```

### 4.2 Ley 1755 de 2015 — SLAs

- **Petición de interés general/particular**: 15 días hábiles
- **Petición de documentos e información**: 10 días hábiles
- **Consultas**: 30 días hábiles
- **Si es de riesgo crítico (vida, menores)**: priorizar a 10 días hábiles

---

## 5. FLUJO LANGGRAPH (ORQUESTACIÓN)

```
[FetchMedata] -> [NormalizeRaw] -> [ClassifyContent]
                                 -> [REJECT_*] o [ACCEPT]
                                 -> [AssessRisk + Ley1755]
                                 -> [RouteToSecretaria(s)]
                                 -> [LoadToWarehouse]
                                 -> [PublishEvent]
```

Cada nodo es un agente LangChain con su prompt específico en `orchestration/prompts/`.

---

## 6. AGENTES — ROLES Y RESPONSABILIDADES

### Agent 1: `ClassifierAgent`
- **Modelo**: `ollama/llama3.2:3b`
- **Input**: texto crudo de PQRS
- **Output JSON**:
```json
{"tipo":"P|Q|R|S|D","es_ofensivo":true,"es_entendible":true,"confianza":0.9,"razon":"...","palabras_detectadas":["..."]}
```

### Agent 2: `PrioritizerAgent`
- **Input**: PQRS clasificada como aceptada
- **Output JSON**:
```json
{"nivel_riesgo":"CRITICO|ALTO|MEDIO|BAJO","sla_dias_habiles":10,"fecha_limite":"YYYY-MM-DD","factores_riesgo":["..."],"justificacion":"..."}
```

### Agent 3: `RouterAgent`
- **Input**: PQRS priorizada
- **Output JSON**:
```json
{"secretarias_recomendadas":[{"codigo":"SDE","nombre":"Desarrollo Económico","score":0.92,"motivo":"..."}],"es_multidependencia":true,"secretaria_lider":"SDE"}
```

---

## 7. LAS 26 SECRETARÍAS Y DEPENDENCIAS

Crear `glosarios/secretarias_routing.yaml` con la estructura y códigos definidos en este documento (SDE, SED, SSA, SIF, SGC, SMA, SMO, SIS, SMU, SJU, SCU, SGO, SHA, SCO, SID, SGH, SEV, SGE, SNR, STU, DAP, DAGRD, DAS, SAG, SPF, SEJ) incluyendo reglas de `multidependencias`.

> **NOTA**: Verifica códigos exactos contra `medellin.gov.co` antes de deploy.

---

## 8. GLOSARIOS — CONTENIDO INICIAL

Se deben crear:
- `glosarios/ofensivo.yaml`
- `glosarios/riesgo_poblacional.yaml`
- `glosarios/riesgo_personal.yaml`
- `glosarios/secretarias_routing.yaml`

Con el contenido definido por este contrato arquitectónico.

---

## 9. ESQUEMA DE BASE DE DATOS

### 9.1 PostgreSQL (OLTP)

Debe incluir, como mínimo:
- `dim_secretaria`
- `dim_territorio` (PostGIS)
- `pqrs`
- `pqrs_secretaria` (N:M)
- `pqrs_historial`
- `banco_qa` (opcional `pgvector`)

Índices por estado, riesgo, fecha límite, territorio y geoespacial.

### 9.2 DuckDB (OLAP)

Vistas materializadas mínimas:
- `vw_pqrs_por_territorio`
- `vw_pqrs_pendientes_priorizadas`

---

## 10. API REST (Rust/Axum)

Endpoints mínimos:
- `GET /api/v1/pqrs`
- `GET /api/v1/pqrs/{id}`
- `GET /api/v1/pqrs/historial/aceptadas`
- `GET /api/v1/pqrs/historial/rechazadas`
- `GET /api/v1/pqrs/gestion/respondidas`
- `GET /api/v1/pqrs/gestion/pendientes`
- `GET /api/v1/pqrs/pendientes/prioridad`
- `GET /api/v1/dashboard/territorios`
- `GET /api/v1/dashboard/metricas`
- `GET /api/v1/secretarias`
- `GET /api/v1/secretarias/{codigo}/pqrs`
- `GET /api/v1/banco-qa`
- `POST /api/v1/banco-qa/buscar`
- `GET /api/v1/health`

---

## 11. FRONTEND — 4 VISTAS (+BONUS)

- `/historial`
- `/gestion`
- `/dashboard` (Leaflet + GeoJSON comunas/corregimientos)
- `/banco-qa`
- `/recomendador` (bonus)

---

## 12. PLAN DE CARDS VIBEKANBAN

Crear cards en este orden, una branch por card:

1. `bootstrap-mono-repo` → `feat/bootstrap`
2. `shared-kernel-and-events` → `feat/shared-kernel`
3. `ingestion-context` → `feat/ingestion`
4. `glossaries-and-seed` → `feat/glossaries`
5. `classification-context` → `feat/classification`
6. `prioritization-context` → `feat/prioritization`
7. `routing-context` → `feat/routing`
8. `warehouse-context` → `feat/warehouse`
9. `orchestration-langgraph` → `feat/orchestration`
10. `backend-rust-axum` → `feat/backend-rust`
11. `frontend-nextjs` → `feat/frontend`
12. `banco-qa-builder` → `feat/banco-qa`
13. `e2e-tests-and-demo-seed` → `feat/e2e`
14. `docs-readme-deploy` → `feat/docs`

Respetar dependencias entre cards según la definición original.

---

## 13. CONVENCIONES DE CÓDIGO

- Python: `black`, `ruff`, `mypy --strict` (domain/application)
- Rust: `rustfmt`, `clippy pedantic`
- TypeScript: `prettier`, `eslint-config-next`, `strictNullChecks`
- Commits: Conventional Commits
- Branches: `feat/`, `fix/`, `docs/`, `refactor/`

---

## 14. CRITERIOS DE ACEPTACIÓN GLOBALES

- `make up` < 60s en máquina limpia
- `make demo` con 200 PQRS sintéticas
- Clasificación ≥ 85% accuracy
- Ruteo top-1 ≥ 70%, top-3 ≥ 90%
- Dashboard con 16 comunas + 5 corregimientos
- p95 backend < 200ms con 200 PQRS
- Sin API keys de pago
- Cobertura ≥ 70% en dominios Python

---

## 15. REGLAS PARA LOS AGENTES DE VIBEKANBAN

1. No saltarse la capa de dominio.
2. No leaks entre contextos.
3. No abrir PR con tests rojos.
4. Secretos en `.env` y `.env.example`.
5. Glosarios como datos editables.
6. Decisiones no obvias en ADRs.
7. Descargar datos reales de fuentes oficiales.
8. Validar Ley 1755 con festivos de Colombia.
