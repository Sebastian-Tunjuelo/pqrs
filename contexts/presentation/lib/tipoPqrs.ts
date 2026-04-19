const TIPO_PQRS_LABEL: Record<string, string> = {
  P: "Petición",
  Q: "Queja",
  R: "Reclamo",
  S: "Sugerencia",
  D: "Denuncia"
};

/** Nombre legible del tipo PQRS (Ley 1755 / uso municipal), sin la letra inicial. */
export function tipoConSignificado(tipo: string | null | undefined): string {
  if (!tipo) return "—";
  const k = tipo.trim().toUpperCase();
  const lab = TIPO_PQRS_LABEL[k];
  return lab ?? tipo.trim();
}
