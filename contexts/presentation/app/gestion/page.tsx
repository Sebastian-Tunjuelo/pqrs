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
      <main className="space-y-4">
        <section className="rounded-2xl border border-[#1A4B8C]/20 bg-gradient-to-r from-[#1A4B8C] to-[#0077C8] px-6 py-6 text-white shadow-lg">
          <h1 className="text-2xl font-bold">Gestión</h1>
        </section>
        <div className="rounded-xl border border-danger/30 bg-danger/10 p-4 text-sm text-danger">
          <p className="font-medium">No se pudo cargar la API</p>
          <p className="mt-1">{msg}</p>
        </div>
      </main>
    );
  }

  return (
    <main className="space-y-10">
      <section className="rounded-2xl border border-[#1A4B8C]/20 bg-gradient-to-r from-[#1A4B8C] to-[#0077C8] px-6 py-6 text-white shadow-lg">
        <p className="text-xs font-semibold uppercase tracking-wide text-white/80">Módulo operativo</p>
        <h1 className="mt-1 text-2xl font-bold">Gestión y Validación</h1>
        <p className="mt-1 text-sm text-white/90">
          Validación humana de clasificación IA, respondidas y cola priorizada (Ley 1755).
        </p>
        <p className="mt-2 text-sm">
          <Link
            href="/asistente?tab=gestion"
            className="inline-flex min-h-11 items-center rounded-lg bg-white/15 px-3 font-medium text-white underline decoration-[#FF8C00] underline-offset-2 hover:bg-white/25"
          >
            Asistente: borrador de mensaje para el equipo de gestión
          </Link>
        </p>
      </section>

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
