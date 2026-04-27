import Link from "next/link";

import type { AlertaItem } from "@/lib/types";

type Props = { alertas: AlertaItem[] };

export function AlertaBanner({ alertas }: Props) {
  const urgentes = alertas.filter((a) => a.dias_habiles_restantes <= 3 && a.dias_habiles_restantes >= 0);
  if (urgentes.length === 0) return null;

  return (
    <div className="mb-6 rounded-xl border border-danger/30 bg-gradient-to-r from-danger/10 to-warning/10 px-4 py-3 text-sm text-danger shadow-sm">
      <p className="font-semibold">Atención: hay PQRS con ≤ 3 días hábiles sin validar</p>
      <p className="mt-1 text-danger/90">
        {urgentes.length} alerta(s) activa(s). Revise la cola de validación.
      </p>
      <Link
        href="/gestion#validacion"
        className="mt-2 inline-flex min-h-11 items-center rounded-lg bg-danger/15 px-3 text-sm font-semibold underline underline-offset-2 hover:bg-danger/20"
      >
        Ir a validación →
      </Link>
    </div>
  );
}
