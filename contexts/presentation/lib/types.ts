export type PqrsListItem = {
  id: string;
  id_externo: string | null;
  tipo: string | null;
  contenido: string;
  fecha_radicado: string;
  fecha_limite: string | null;
  estado_clasificacion: string;
  estado_gestion: string | null;
  nivel_riesgo: string | null;
  territorio_id: number | null;
  confianza_clasificacion: number | null;
  /** Cola de validación humana (API ≥ migración 002). */
  validation_status?: string;
  /** Secretaría líder o mayor score (`pqrs_secretaria`). */
  secretaria_codigo?: string | null;
  secretaria_nombre?: string | null;
};

/** Respuesta de `GET /api/v1/pqrs/:id` (API Rust). */
export type PqrsDetail = {
  id: string;
  id_externo: string | null;
  tipo: string | null;
  contenido: string;
  contenido_hash: string | null;
  fecha_radicado: string;
  fecha_limite: string | null;
  estado_clasificacion: string;
  estado_gestion: string | null;
  nivel_riesgo: string | null;
  territorio_id: number | null;
  confianza_clasificacion: number | null;
  razon_rechazo: string | null;
  metadata: unknown | null;
  created_at: string | null;
  updated_at: string | null;
  validation_status?: string;
  summary_lead?: string | null;
  summary_topics?: unknown;
  summary_executive?: string | null;
};

/** GET /api/v1/pqrs/:id/summary */
export type PqrsSummaryResponse = {
  lead: string;
  temas: string[];
  resumen_ejecutivo: string;
  pqrs_completa: string;
};

export type Paginated<T> = {
  items: T[];
  total: number;
  page: number;
  per_page: number;
};

export type TerritorioDashboard = {
  id: number;
  tipo: string;
  codigo: string;
  nombre: string;
  pqrs_count: number;
  pendientes: number;
  en_tramite: number;
  respondidas: number;
  vencidas: number;
  geojson: string | null;
};

export type AssistOllamaReply = {
  respuesta: string;
  modelo: string;
};

export type MetricasDashboard = {
  total_pqrs: number;
  pendientes: number;
  pendientes_gestion: number;
  en_tramite: number;
  respondidas: number;
  vencidas: number;
  promedio_dias_respuesta?: number | null;
  por_tipo: Record<string, number>;
  por_riesgo: Record<string, number>;
  por_nivel_riesgo: Record<string, number>;
  tasa_clasificacion_correcta?: number | null;
  tendencia_semanal?: { semana: string; total: number }[];
};

export type SecretariaRow = {
  codigo: string;
  nombre: string;
  activa: boolean | null;
};

export type AlertaItem = {
  id: number;
  pqrs_id: string;
  tipo: string;
  mensaje: string | null;
  activa: boolean;
  creado_en: string;
  fecha_limite: string | null;
  id_externo: string | null;
  nivel_riesgo: string | null;
  dias_habiles_restantes: number;
};
