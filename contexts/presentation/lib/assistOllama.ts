/** Prompts del asistente (servidor Next → Ollama). Mantener alineado con negocio PQRS. */

export type AssistMode = "rechazo" | "gestion" | "riesgo" | "clasificacion";

export type PqrsDetailPayload = {
  id: string;
  id_externo: string | null;
  tipo: string | null;
  contenido: string;
  fecha_radicado: string;
  fecha_limite: string | null;
  estado_clasificacion: string;
  estado_gestion: string | null;
  nivel_riesgo: string | null;
  confianza_clasificacion: number | null;
  razon_rechazo: string | null;
  metadata: unknown;
};

export function systemPrompt(mode: AssistMode): string {
  const base =
    "Eres un asistente técnico-institucional de la Alcaldía de Medellín (Colombia). " +
    "Responde en español, con párrafos claros. No inventes hechos externos al contexto; " +
    "si faltan datos, dilo explícitamente.";

  switch (mode) {
    case "rechazo":
      return (
        base +
        " Explicas por qué una PQRS pudo ser clasificada como rechazada o qué implica su estado de clasificación."
      );
    case "gestion":
      return (
        base +
        " Redactas un borrador de mensaje interno para el equipo de gestión de PQRS: tono profesional, acciones y riesgos."
      );
    case "riesgo":
      return (
        base +
        " Explicas el nivel de riesgo asignado (BAJO, MEDIO, ALTO, CRITICO o sin clasificar): qué suele significar en Ley 1755, " +
        "qué factores del texto o metadatos podrían haber influido, y qué implica para plazos y priorización."
      );
    case "clasificacion":
      return (
        base +
        " Explicas el estado de clasificación (ACEPTADA, rechazos, PENDIENTE, etc.) y la confianza numérica si existe: " +
        "qué indica, limitaciones y próximos pasos para el ciudadano o la entidad."
      );
    default:
      return base;
  }
}

function metaStr(m: unknown): string {
  if (m == null) return "(sin metadata)";
  try {
    return JSON.stringify(m).slice(0, 1200);
  } catch {
    return String(m);
  }
}

export function userPrompt(mode: AssistMode, p: PqrsDetailPayload): string {
  const bloque = `Datos de la PQRS:
- id: ${p.id}
- id_externo: ${p.id_externo ?? "—"}
- tipo: ${p.tipo ?? "—"}
- estado_clasificacion: ${p.estado_clasificacion}
- estado_gestion: ${p.estado_gestion ?? "—"}
- nivel_riesgo: ${p.nivel_riesgo ?? "—"}
- confianza_clasificacion: ${p.confianza_clasificacion ?? "—"}
- fecha_limite: ${p.fecha_limite ?? "—"}
- fecha_radicado: ${p.fecha_radicado}
- razon_rechazo (sistema): ${p.razon_rechazo ?? "—"}
- metadata (recorte): ${metaStr(p.metadata)}
- texto ciudadano:
${p.contenido}
`;

  switch (mode) {
    case "rechazo":
      return `${bloque}\nPregunta: ¿Por qué pudo haber sido rechazada o qué significa esta clasificación? Próximos pasos recomendables.`;
    case "gestion":
      return `${bloque}\nTarea: borrador (asunto en una línea, luego cuerpo) para coordinación interna y seguimiento.`;
    case "riesgo":
      return `${bloque}\nPregunta: ¿Por qué este caso podría tener este nivel de riesgo y qué debería priorizar la entidad?`;
    case "clasificacion":
      return `${bloque}\nPregunta: ¿Qué significa esta clasificación y la confianza reportada para el caso?`;
    default:
      return bloque;
  }
}
