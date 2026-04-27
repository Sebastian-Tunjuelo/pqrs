# TODO list (Cursor) — Días restantes con semáforo + subdivisión por secretarías

**Contexto del repo `pqrs`:** monorepo con **Next.js 14** (`contexts/presentation`), **API Rust Axum** (`contexts/api`, rutas `/api/v1/...`), **PostgreSQL** (`pqrs`, `pqrs_secretaria`, `dim_secretaria`). Los colores de marca están en `contexts/presentation/tailwind.config.ts`: `success` (#388E3C), `warning` (#F57C00), `danger` (#D32F2F), `primary`, `accent`.

**Nota técnica:** hoy el **Historial** calcula **días calendario** hasta `fecha_limite` en `HistorialView.tsx` (`diasCalendarioRestantes`). Las **alertas** (`AlertaBanner`, `AppHeader`) usan **`dias_habiles_restantes`** desde `/api/v1/alertas`. Ley 1755 en producción suele priorizar **días hábiles**; conviene **unificar criterio** (ver tarea 1).

---

## A. Días faltantes — semáforo verde / amarillo / rojo

- [ ] **A1. Definir reglas de umbral** (documentar en código o `README`): por ejemplo  
  - **Verde:** más de N días (p. ej. `> 14` calendario o equivalente hábil).  
  - **Amarillo:** zona intermedia (p. ej. `4…N`).  
  - **Rojo:** crítico (p. ej. `≤ 3` alineado a alertas actuales o `≤ 0` si venció).  
  Ajustar N con negocio; si se usan **hábiles**, reutilizar lógica del backend/Python (`fecha_limite_dias_habiles` / worker) o exponer campo en API para no duplicar calendario festivo en el front.

- [ ] **A2. Extraer helper único** en `contexts/presentation/lib/` (p. ej. `plazoPqrs.ts`):  
  - Entrada: `fecha_limite: string | null`, opcional `fecha_radicado`, y criterio `calendario | habiles`.  
  - Salida: `{ texto: string; dias: number | null; variante: 'ok' | 'aviso' | 'critico' | 'sin' }` donde `variante` mapea a clases Tailwind (`text-success`, `bg-warning/15` + `text-warning`, `text-danger` + `font-semibold`, etc.).

- [ ] **A3. Historial** — `HistorialView.tsx`:  
  - Sustituir celda plana de “Días rest.” por badge/pill con color según `variante`.  
  - Mantener número legible + accesible (`aria-label` con “X días restantes, estado …”).  
  - CSV: opcional columna numérica + texto estado, o dejar solo número (no romper export).

- [ ] **A4. PqrsCard** — `PqrsCard.tsx`:  
  - La barra de plazo (`diasBar`) hoy usa solo `urgent` booleano; extender a **tres tonos** en la barra y/o en el texto del plazo para coherencia con Historial.

- [ ] **A5. Detalle PQRS** — `app/pqrs/[id]/page.tsx`:  
  - Mostrar plazo restante con el mismo semáforo junto a `fecha_limite`.

- [ ] **A6. Tablas de gestión** — `PqrsTable.tsx` / `GestionValidacion`:  
  - Si se muestra plazo o fecha límite, reutilizar el mismo helper para no divergencias.

- [ ] **A7. Pruebas manuales:** PQRS con `fecha_limite` lejana, intermedia, vencida y `null`; modo claro; contraste mínimo legible.

---

## B. Subdivisión / navegación por secretarías (para Cursor)

**Estado actual:** la API expone `GET /api/v1/secretarias` (lista) y `GET /api/v1/secretarias/:codigo/pqrs` (paginado de PQRS de una secretaría). El **front no consume** estas rutas: solo filtro por **código** manual en Historial (`?secretaria=SDE`). No hay página ni menú “por secretaría”.

- [ ] **B1. Cargar catálogo en cliente** — función `apiFetch<SecretariaRow[]>('/api/v1/secretarias')` (tipos ya en `lib/types.ts` como `SecretariaRow`).

- [ ] **B2. Historial — filtro usable** — `HistorialView.tsx`:  
  - Reemplazar input libre por **`<select>`** (u otro control) con opción “Todas” + lista de `dim_secretaria` (código + nombre visible; valor query sigue siendo **código** para no romper `parse_secretaria_codigo` en la API).  
  - Opcional: búsqueda incremental si la lista crece.

- [ ] **B3. Vista “Por secretaría”** (elegir una):  
  - **Opción 1 (mínima):** ruta nueva `app/secretarias/page.tsx` que liste las 26 dependencias con enlace a ` /secretarias/[codigo]` o query `historial?secretaria=`.  
  - **Opción 2:** subruta `app/secretarias/[codigo]/page.tsx` que llame `GET /api/v1/secretarias/:codigo/pqrs` y reutilice tabla tipo `PqrsTable` / mismos estilos que Historial.  
  - Añadir entrada en **`AppNav.tsx`** y en **tarjetas del inicio** si aplica (`app/page.tsx`), sin inventar secciones fuera del alcance del prompt de portal.

- [ ] **B4. Coherencia API ↔ UI** — Verificar que `pqrs_por_secretaria` y listado general muestren la misma forma de **tipo** y **secretaría** (nombre completo); revisar `secretarias.rs` si hace falta orden o metadatos.

- [ ] **B5. Multidependencia (alcance acotado):** si en el futuro se listan varias filas en `pqrs_secretaria`, definir en UI solo **líder** vs “+N” (hoy el listado ya toma líder por `LATERAL`); documentar en comentario en API o en README.

- [ ] **B6. E2E / humo:** con API levantada, comprobar filtro por secretaría y nueva ruta (si se implementa) con al menos dos códigos distintos del seed.

---

## Orden sugerido de implementación

1. Helper de plazo + colores (**A2**), luego **A3**–**A5**.  
2. Catálogo secretarías + select en Historial (**B1**, **B2**).  
3. Vista por secretaría (**B3**) si el producto la requiere.

---

*Pegar este archivo en Cursor como contexto de tarea o dividir cada `[ ]` en issues de Kanba.*
