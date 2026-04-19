import Link from "next/link";

import { PqrsTable } from "@/components/PqrsTable";
import { apiGetServer } from "@/lib/api";
import type { Paginated, PqrsListItem } from "@/lib/types";

export default async function GestionPage() {
  let respondidas: Paginated<PqrsListItem>;
  let pendientes: Paginated<PqrsListItem>;
  let prioridad: Paginated<PqrsListItem>;
  try {
    [respondidas, pendientes, prioridad] = await Promise.all([
      apiGetServer<Paginated<PqrsListItem>>("/api/v1/pqrs/gestion/respondidas?page=1&per_page=15"),
      apiGetServer<Paginated<PqrsListItem>>("/api/v1/pqrs/gestion/pendientes?page=1&per_page=15"),
      apiGetServer<Paginated<PqrsListItem>>("/api/v1/pqrs/pendientes/prioridad?page=1&per_page=15")
    ]);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Error desconocido";
    return (
      <main>
        <h1 className="mb-2 text-2xl font-bold text-slate-900">Gestión</h1>
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
          <p className="font-medium">No se pudo cargar la API</p>
          <p className="mt-1">{msg}</p>
        </div>
      </main>
    );
  }

  return (
    <main className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Gestión</h1>
        <p className="mt-1 text-sm text-slate-600">
          Respondidas, pendientes y cola priorizada por riesgo y fecha límite (Ley 1755).
        </p>
        <p className="mt-2 text-sm">
          <Link
            href="/asistente?tab=gestion"
            className="font-medium text-brand-700 underline decoration-brand-300 underline-offset-2 hover:text-brand-800"
          >
            Asistente Ollama: borrador de mensaje para el equipo de gestión
          </Link>
        </p>
      </div>
      <PqrsTable
        title={`Respondidas (${respondidas.total} total)`}
        items={respondidas.items}
        emptyMessage="Sin respondidas en esta página."
      />
      <PqrsTable
        title={`Pendientes (${pendientes.total} total)`}
        items={pendientes.items}
        emptyMessage="Sin pendientes en esta página."
      />
      <PqrsTable
        title={`Pendientes por prioridad (${prioridad.total} total)`}
        items={prioridad.items}
        emptyMessage="Sin ítems en cola de prioridad."
      />
    </main>
  );
}
