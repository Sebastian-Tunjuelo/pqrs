# PROMPT — Portal PQRS (repo `pqrs`) para Vibe Kanba

**Alcance:** solo lo que **existe hoy** en este monorepo. No pedir secciones, bots ni apps que **no** estén en el código (p. ej. sin Centro de Ayuda / FAQ dedicado, sin bot de Telegram, sin Vite ni React Router si no se añaden al proyecto).

---

## Objetivo

Refinar la **experiencia visual y de navegación** del frontend actual hacia un **portal gubernamental colombiano** sobrio y legible (referencia de **patrones** tipo portales institucionales / GOV.CO: jerarquía tipográfica, contraste, breadcrumbs donde aplique, cabeceras claras).  

**Únicamente** estructura visual y UX; **no** copiar nombres, marcas ni identidades de terceros.

---

## Stack técnico (real del proyecto)

| Capa | Tecnología |
|------|------------|
| Frontend | **Next.js 14** (App Router), **React 18**, **TypeScript** |
| Estilos | **Tailwind CSS 3.4** (tokens: `primary` #00693E, `accent` #F5A800, `brand`, `neutral`, etc. en `tailwind.config.ts`) |
| Mapas | **Leaflet**, **react-leaflet** |
| Gráficos | **Plotly.js**, **react-plotly.js** |
| API | **Rust** (Axum, SQLx, Tokio) — base URL típica `http://127.0.0.1:8080`, rutas bajo `/api/v1/...` |
| Datos / jobs | **PostgreSQL 16** + PostGIS, **Redis 7** |
| IA local | **Ollama** (asistente y workers Python; el asistente en UI llama vía **ruta Next** `/api/assist/ollama`) |
| Dominio / orquestación | **Python 3.11+** (Pydantic, LangGraph, workers), **Alembic** en `contexts/warehouse` |

**No usar en el prompt de trabajo:** Vite, React Router v6, Zustand, React Query, Framer Motion, React Hook Form, Zod, Lucide, python-telegram-bot, etc., **salvo** que el equipo decida incorporarlos explícitamente después.

---

## Navegación y secciones (solo las que ya existen)

Sidebar principal (`AppNav`) y rutas App Router:

| Ruta | Nombre en UI | Rol |
|------|----------------|-----|
| `/` | Inicio / PQRS Medellín | Hero + accesos a módulos principales |
| `/historial` | Historial | Filtros, tabla de PQRS, exportación CSV |
| `/gestion` | Gestión | Validación humana, alertas, tablas respondidas / pendientes / prioridad |
| `/dashboard` | Dashboard | Métricas (cards), gráficos Plotly, mapa territorios |
| `/asistente` | Asistente | Pestañas: clasificación, riesgo, rechazo, mensaje gestión; lista PQRS + consulta modelo |
| `/pqrs/[id]` | Detalle PQRS | Texto completo, estados, resúmenes cuando apliquen |

**No añadir** en el alcance de este prompt: “Centro de Ayuda”, “PQRSD” como producto distinto, “Contacto” como página nueva, “Inicia sesión / Regístrate” (no hay auth en este frontend), **bot Telegram**, ni flujos de radicación ciudadana fuera de lo ya cubierto por API + pantallas anteriores.

---

## Lineamientos de diseño (aplicables a lo existente)

1. **Cabecera / layout**  
   - Mantener layout con **sidebar** + área principal; mejorar jerarquía visual (portal) sin romper rutas.  
   - Opcional: top bar fina institucional (accesibilidad / enlace útil) **solo** si encaja con el layout actual (`app/layout.tsx`).

2. **Inicio (`/`)**  
   - Hero alineado a identidad **verde institucional** (`primary`) y texto claro sobre Ley 1755 / PQRS (P, Q, R, S, D).  
   - Tarjetas hacia Historial, Gestión, Dashboard (y enlace coherente al **Asistente** si se desea paridad con el menú lateral).

3. **Historial**  
   - Tabla legible, filtros agrupados, tipos como **Petición / Queja / Reclamo / Sugerencia / Denuncia** (no solo letras si el diseño lo mejora).  
   - Columna secretaría con **nombre completo** (datos vienen de API + `dim_secretaria`).

4. **Gestión**  
   - Cola de validación y tablas con mismo lenguaje visual que el resto del portal.  
   - Alertas por plazo visibles y calmadas (semántica `danger` / `warning` ya presente en Tailwind extendido).

5. **Dashboard**  
   - Leyendas y ejes con **nombres de tipo completos** (coherente con historial).  
   - Mapa Leaflet y tarjetas de métricas con aire “tablero de control” municipal.

6. **Asistente**  
   - Tabs claras; estados de carga y errores legibles; sin copy técnico innecesario en UI (configuración queda en documentación / `.env.example`).

7. **Detalle PQRS**  
   - Breadcrumb mínimo (ej. Historial → detalle) si mejora orientación.  
   - Tipografía y bloques de contenido tipo expediente.

8. **Accesibilidad**  
   - Contraste AA donde sea razonable, foco visible, `aria-` en navegación y tablas.  
   - Cualquier widget flotante de accesibilidad es **opcional** y no debe inventar nuevas rutas.

---

## Restricciones

- No usar branding ni nombres de productos de terceros (ej. “Tabot”, “A la mano”, etc.).  
- No prometer funcionalidades que **no** estén en el repo (Telegram, FAQ, login ciudadano, etc.).  
- Respetar consumo de **API Rust** y modelos TypeScript existentes (`contexts/presentation/lib/types.ts`).

---

## Entregables esperados (para Kanba / diseño)

- Lista de **tareas por ruta** anterior (sin nuevas secciones).  
- Referencias de **componentes** a tocar: `AppNav`, `layout`, páginas en `app/*`, `HistorialView`, `GestionValidacion`, `Dashboard*`, `AsistentePanel`, detalle `pqrs/[id]`.  
- Guía de **tokens** desde `tailwind.config.ts` (no imponer paleta ajena sin alinearla a `primary` / `accent`).

---

*Documento generado a partir del monorepo **pqrs** (PQRS Medellín — referencia). Copiar/pegar en Vibe Kanba como descripción del epic o del proyecto UI.*
