# Bitácora — 5 hitos (OmegaHack / PQRS Medellín)

## Hito 1 — Arquitectura: DDD frente a monolito

**Contexto:** Se requería separar ingestión, clasificación, priorización, ruteo, persistencia y presentación con equipos distintos y despliegue incremental.

**Alternativas:** Monolito único (rápido al inicio, acoplamiento alto) vs microservicios puros (operación compleja) vs DDD por contextos acotados.

**Decisión:** Monorepo DDD con bounded contexts en Python, API Rust dedicada y Next.js como fachada; eventos y contratos compartidos en `shared-kernel`.

**Consecuencias:** Mayor claridad de límites y pruebas por contexto; coste inicial de wiring (Redis, migraciones) compensado por evolución paralela.

## Hito 2 — IA local: Ollama vs API externa

**Contexto:** Clasificación y síntesis deben ser reproducibles en demo sin coste por token ni fugas de datos personales.

**Alternativas:** APIs comerciales de LLM (calidad variable, coste, privacidad) vs modelo local (menor latencia de contrato, dependencia de hardware).

**Decisión:** Ollama local con prompts versionados en `orchestration/prompts` y clientes JSON acotados.

**Consecuencias:** Control de datos y coste cero en hackathon; el rendimiento depende de la máquina del jurado y del modelo elegido.

## Hito 3 — Dominio: validación humana (Ley 1755)

**Contexto:** La ley exige trazabilidad y intervención humana; la IA solo propone.

**Alternativas:** Auto-aprobación tras clasificador vs cola explícita de validación vs revisión solo en reclamos.

**Decisión:** Estado `validation_status` en `pqrs`, endpoints de validación y registro en `pqrs_historial`; pipeline de orquestación marca `PENDING_VALIDATION` al cerrarse el flujo aceptado.

**Consecuencias:** Más pasos en UX y API; cumplimiento explícito del relato legal para el jurado.

## Hito 4 — Datos: banco Q&A y semántica *(retirado del producto; migración 006 elimina `banco_qa`)*

**Contexto:** Recuperar precedentes similares no se resolvía con `ILIKE` alone.

**Alternativas:** Solo FTS en Postgres vs embeddings + pgvector vs motor externo (Elastic, etc.).

**Decisión:** Extensión `vector` en Postgres, embeddings locales `all-MiniLM-L6-v2`, microservicio HTTP mínimo para embed y endpoint `POST /banco-qa/buscar-semantico` en Rust.

**Consecuencias:** Imagen Docker de Postgres más pesada (compilación pgvector); dependencia opcional de `sentence-transformers` en Python.

## Hito 5 — UX: asesor jurídico en el centro

**Contexto:** El jurado valora un flujo creíble de funcionario validando IA.

**Alternativas:** Tabla plana sin contexto vs asistente solo chat vs panel con resumen en capas y texto íntegro.

**Decisión:** Vista `/gestion` con cola `pending-validation`, tarjetas densas estilo institucional + limpieza tipo banca, panel lateral con pestañas (resumen IA, pre-clasificación, original) y acciones de validar / solicitar corrección.

**Consecuencias:** Más componentes cliente y llamadas a API; mejor narrativa de demo a cambio de complejidad de estado en React.
