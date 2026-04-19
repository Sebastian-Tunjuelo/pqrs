import Link from "next/link";

import { apiGetServer } from "@/lib/api";
import type { AlertaItem } from "@/lib/types";

export default async function AppHeader() {
  const officer =
    process.env.NEXT_PUBLIC_DEMO_OFFICER_NAME?.trim() || "Funcionario (demo)";
  let urgent = 0;
  try {
    const alertas = await apiGetServer<AlertaItem[]>("/api/v1/alertas", 0);
    urgent = alertas.filter(
      (a) => a.dias_habiles_restantes <= 3 && a.dias_habiles_restantes >= 0
    ).length;
  } catch {
    /* API apagada en build estático */
  }

  return (
    <header className="hidden border-b border-neutral-100 bg-white px-4 py-3 md:block">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-4">
        <div className="min-w-0">
          <p className="truncate text-sm text-neutral-900/70">Sesión</p>
          <p className="truncate font-semibold text-neutral-900">{officer}</p>
        </div>
        <Link
          href="/gestion#validacion"
          className="relative inline-flex items-center gap-2 rounded-lg border border-neutral-200 bg-neutral-50 px-3 py-2 text-sm font-medium text-neutral-800 hover:border-primary/40 hover:bg-white"
        >
          <span aria-hidden>🔔</span>
          Alertas
          {urgent > 0 ? (
            <span className="absolute -right-1 -top-1 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-danger px-1 text-[10px] font-bold text-white">
              {urgent > 99 ? "99+" : urgent}
            </span>
          ) : null}
        </Link>
      </div>
    </header>
  );
}
