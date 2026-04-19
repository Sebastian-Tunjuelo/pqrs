import { plazoBadgeClasses, plazoCalendarioRestante } from "@/lib/plazoPqrs";

export function PlazoDiasBadge({ fechaLimite }: { fechaLimite: string | null }) {
  const p = plazoCalendarioRestante(fechaLimite);
  return (
    <span className={plazoBadgeClasses(p.variante)} aria-label={p.ariaLabel}>
      {p.etiqueta}
    </span>
  );
}
