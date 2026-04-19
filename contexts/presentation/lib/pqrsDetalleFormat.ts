import type { PqrsDetail } from "@/lib/types";

const TIPO_LABEL: Record<string, string> = {
  P: "Petición",
  Q: "Queja",
  R: "Reclamo",
  S: "Sugerencia",
  D: "Denuncia"
};

export function etiquetaTipo(tipo: string | null | undefined): string {
  if (tipo == null || tipo === "") return "PQRS";
  const c = tipo.toUpperCase().charAt(0);
  return TIPO_LABEL[c] ?? `PQRS (tipo ${tipo})`;
}

function metaRecord(p: PqrsDetail): Record<string, unknown> | null {
  if (p.metadata != null && typeof p.metadata === "object" && !Array.isArray(p.metadata)) {
    return p.metadata as Record<string, unknown>;
  }
  return null;
}

/** Título legible: metadata explícita, arquetipo demo, o primera línea sustancial del texto. */
export function tituloPqrs(p: PqrsDetail): string {
  const contenido = p.contenido ?? "";
  const m = metaRecord(p);
  if (m?.titulo && typeof m.titulo === "string" && m.titulo.trim()) return m.titulo.trim();

  const arch = m?.arquetipo_demo;
  if (arch === "aceptada_informacion_vial") {
    return "Solicitud de información sobre proyectos de infraestructura vial";
  }
  if (arch === "ilegible_chat") {
    return "Petición o comunicación de difícil lectura (redacción informal)";
  }
  if (arch === "ofensivo_reclamo") {
    return "Reclamo u opinión con lenguaje irrespetuoso o vulgar";
  }

  const lines = contenido
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);

  const skipGreeting = (s: string) =>
    /^(estimad|cordiales|atentamente|buenos|buenas|hola|por medio)/i.test(s) && s.length < 80;

  for (const line of lines) {
    if (line.length < 12) continue;
    if (skipGreeting(line)) continue;
    if (/^(cc|cedula|cédula|tel|correo|referencia interna)/i.test(line) && line.length < 40) continue;
    const t = line.length > 120 ? `${line.slice(0, 117)}…` : line;
    return t;
  }

  const base = etiquetaTipo(p.tipo);
  return `${base} — ${p.id_externo ?? p.id.slice(0, 8)}`;
}

/** Resumen en 1–3 frases o primeros caracteres con corte prudente. */
export function resumenPqrs(contenido: string | null | undefined, maxChars = 360): string {
  const texto = (contenido ?? "").trim();
  if (!texto) return "—";

  const parts = texto.split(/(?<=[.!?¿¡])\s+/).filter(Boolean);
  let acc = "";
  for (const part of parts) {
    const next = acc ? `${acc} ${part}` : part;
    if (next.length > maxChars) {
      if (!acc) return texto.slice(0, maxChars).trim() + "…";
      break;
    }
    acc = next;
    if (acc.length >= maxChars * 0.5 && parts.length <= 2) break;
    if (acc.length >= maxChars * 0.65) break;
  }

  if (!acc) return texto.slice(0, maxChars).trim() + (texto.length > maxChars ? "…" : "");
  const tail = texto.length > acc.length ? "…" : "";
  return acc + tail;
}

/** Contexto administrativo en prosa (sin markdown). */
export function deQueTrataPqrs(p: PqrsDetail, resumen: string): string {
  const tipo = etiquetaTipo(p.tipo);
  const clasif = p.estado_clasificacion ?? "Sin clasificar";
  const partes: string[] = [
    `Es una ${tipo} presentada ante la entidad.`,
    `La clasificación actual es «${clasif}».`
  ];
  if (p.estado_gestion) {
    partes.push(`El estado de gestión registrado es «${p.estado_gestion}».`);
  }
  if (p.nivel_riesgo) {
    partes.push(`Nivel de riesgo asignado: ${p.nivel_riesgo}.`);
  }
  const limpio = resumen.replace(/…\s*$/, "").trim();
  partes.push(`Respecto al fondo del escrito: ${limpio}${resumen.endsWith("…") ? "…" : ""}`);
  return partes.join(" ");
}

export function esClasificacionRechazo(estado: string | null | undefined): boolean {
  if (estado == null || typeof estado !== "string") return false;
  const u = estado.toUpperCase();
  return u.includes("RECHAZ") || u.includes("ILEGIBLE") || u.includes("NO_ENTENDIBLE");
}
