import Link from "next/link";

import { AlertaBanner } from "@/components/AlertaBanner";
import { GestionValidacion } from "@/components/GestionValidacion";
import { PqrsTable } from "@/components/PqrsTable";
import { apiGetServer } from "@/lib/api";
import type { AlertaItem, Paginated, PqrsListItem } from "@/lib/types";

export default async function GestionPage() {
  let respondidas: Paginated<PqrsListItem>;
  let pendientes: Paginated<PqrsListItem>;
  let prioridad: Paginated<PqrsListItem>;
  let pendingVal: Paginated<PqrsListItem>;
  let alertas: AlertaItem[];
  try {
    [respondidas, pendientes, prioridad, pendingVal, alertas] = await Promise.all([
      apiGetServer<Paginated<PqrsListItem>>("/api/v1/pqrs/gestion/respondidas?page=1&per_page=15"),
      apiGetServer<Paginated<PqrsListItem>>("/api/v1/pqrs/gestion/pendientes?page=1&per_page=15"),
      apiGetServer<Paginated<PqrsListItem>>("/api/v1/pqrs/pendientes/prioridad?page=1&per_page=15"),
      apiGetServer<Paginated<PqrsListItem>>("/api/v1/pqrs/pending-validation?page=1&per_page=30", 0),
      apiGetServer<AlertaItem[]>("/api/v1/alertas", 0)
    ]);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Error desconocido";
    return (
      <main>
        <h1 className="mb-2 text-2xl font-bold text-neutral-900">Gestión</h1>
        <div className="rounded-xl border border-danger/30 bg-danger/10 p-4 text-sm text-danger">
          <p className="font-medium">No se pudo cargar la API</p>
          <p className="mt-1">{msg}</p>
        </div>
      </main>
    );
  }

  return (
    <main className="space-y-10">
      <div>
        <h1 className="text-2xl font-bold text-neutral-900">Gestión</h1>
        <p className="mt-1 text-sm text-neutral-900/60">
          Validación humana de clasificación IA, respondidas y cola priorizada (Ley 1755).
        </p>
        <p className="mt-2 text-sm">
          <Link
            href="/asistente?tab=gestion"
            className="font-medium text-primary underline decoration-accent underline-offset-2 hover:opacity-90"
          >
            Asistente: borrador de mensaje para el equipo de gestión
          </Link>
        </p>
      </div>

      <AlertaBanner alertas={alertas} />

      <GestionValidacion initial={pendingVal} />

      <PqrsTable
        title={`Respondidas (${respondidas.total} total)`}
        items={respondidas.items}
        emptyMessage="Sin respondidas en esta página."
      />
      <PqrsTable
        title={`Pendientes gestión (${pendientes.total} total)`}
        items={pendientes.items}
        emptyMessage="Sin pendientes en esta página."
      />
      <PqrsTable
        title={`Prioridad operativa (${prioridad.total} total)`}
        items={prioridad.items}
        emptyMessage="Sin ítems en cola de prioridad."
      />
    </main>
  );
}
