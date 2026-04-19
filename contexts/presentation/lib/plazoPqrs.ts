/**
 * Plazo restante en **días calendario** respecto a `fecha_limite` (fin de día local).
 * Las alertas del header usan días **hábiles** desde la API; unificar a hábiles implicaría
 * exponer ese valor en el listado o duplicar calendario festivo en el front (ver README).
 *
 * Umbrales (ajustar con negocio):
 * - **ok (verde):** más de 14 días calendario restantes
 * - **aviso (amarillo):** entre 4 y 14 días (inclusive)
 * - **critico (rojo):** 0–3 días restantes o ya vencida (< 0)
 * - **sin:** sin fecha límite
 */
export type PlazoVariante = "sin" | "ok" | "aviso" | "critico";

export const UMBRAL_DIAS_OK_MIN = 15; // >14 → ok
export const UMBRAL_DIAS_AVISO_MAX = 14;
export const UMBRAL_DIAS_AVISO_MIN = 4; // 4..14 → aviso
export const UMBRAL_DIAS_CRITICO_MAX = 3; // 0..3 → critico

export type PlazoInfo = {
  /** Días calendario hasta la fecha límite (negativo = vencida). */
  dias: number | null;
  variante: PlazoVariante;
  /** Texto corto para celda o badge. */
  etiqueta: string;
  ariaLabel: string;
};

function toEpochMs(fechaLimite: string): number | null {
  const raw = fechaLimite.trim();
  if (!raw) return null;
  const normalized = /[tT]/.test(raw) ? raw : `${raw}T12:00:00`;
  const ms = new Date(normalized).getTime();
  return Number.isFinite(ms) ? ms : null;
}

export function plazoCalendarioRestante(fechaLimite: string | null): PlazoInfo {
  if (!fechaLimite?.trim()) {
    return {
      dias: null,
      variante: "sin",
      etiqueta: "Sin plazo",
      ariaLabel: "Sin fecha límite registrada"
    };
  }
  const lim = toEpochMs(fechaLimite);
  if (lim == null) {
    return {
      dias: null,
      variante: "sin",
      etiqueta: "Sin plazo",
      ariaLabel: "Fecha límite inválida"
    };
  }
  const d = Math.ceil((lim - Date.now()) / (86400 * 1000));

  if (d < 0) {
    const abs = Math.abs(d);
    return {
      dias: d,
      variante: "critico",
      etiqueta: `Vencida ${abs}d`,
      ariaLabel: `Plazo vencido hace ${abs} día${abs === 1 ? "" : "s"} calendario`
    };
  }
  if (d <= UMBRAL_DIAS_CRITICO_MAX) {
    const etiqueta = d === 0 ? "Hoy" : `${d} d.`;
    return {
      dias: d,
      variante: "critico",
      etiqueta,
      ariaLabel:
        d === 0
          ? "Fecha límite es hoy"
          : `Quedan ${d} día${d === 1 ? "" : "s"} calendario; plazo crítico`
    };
  }
  if (d <= UMBRAL_DIAS_AVISO_MAX) {
    return {
      dias: d,
      variante: "aviso",
      etiqueta: `${d} d.`,
      ariaLabel: `Quedan ${d} días calendario; atención al plazo`
    };
  }
  return {
    dias: d,
    variante: "ok",
    etiqueta: `${d} d.`,
    ariaLabel: `Quedan ${d} días calendario; plazo holgado`
  };
}

export function plazoBadgeClasses(v: PlazoVariante): string {
  switch (v) {
    case "ok":
      return "inline-flex min-w-[2.5rem] justify-center rounded-full border border-success/40 bg-success/15 px-2 py-0.5 text-xs font-semibold text-success";
    case "aviso":
      return "inline-flex min-w-[2.5rem] justify-center rounded-full border border-warning/50 bg-warning/15 px-2 py-0.5 text-xs font-semibold text-warning";
    case "critico":
      return "inline-flex min-w-[2.5rem] justify-center rounded-full border border-danger/40 bg-danger/15 px-2 py-0.5 text-xs font-semibold text-danger";
    default:
      return "inline-flex min-w-[2.5rem] justify-center rounded-full bg-neutral-100 px-2 py-0.5 text-xs text-neutral-500";
  }
}

/** Color de la barra de progreso (PqrsCard). */
export function plazoBarTone(v: PlazoVariante): "ok" | "aviso" | "critico" | "sin" {
  if (v === "sin") return "sin";
  return v;
}

export function plazoBarFillClass(tone: "ok" | "aviso" | "critico" | "sin"): string {
  switch (tone) {
    case "ok":
      return "bg-success";
    case "aviso":
      return "bg-warning";
    case "critico":
      return "bg-danger";
    default:
      return "bg-neutral-300";
  }
}

/** Porcentaje visual de la barra (más ancho cuando queda menos tiempo). */
export function plazoBarPct(dias: number | null): number {
  if (dias == null) return 0;
  if (dias < 0) return 100;
  return Math.min(100, Math.max(8, 100 - Math.min(dias * 6, 92)));
}
