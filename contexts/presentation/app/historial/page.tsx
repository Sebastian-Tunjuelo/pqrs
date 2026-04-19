import { PqrsTable } from "@/components/PqrsTable";
import { apiGetServer } from "@/lib/api";
import type { Paginated, PqrsListItem } from "@/lib/types";

export default async function HistorialPage() {
  let aceptadas: Paginated<PqrsListItem>;
  let rechazadas: Paginated<PqrsListItem>;
  try {
    [aceptadas, rechazadas] = await Promise.all([
      apiGetServer<Paginated<PqrsListItem>>("/api/v1/pqrs/historial/aceptadas?page=1&per_page=20"),
      apiGetServer<Paginated<PqrsListItem>>("/api/v1/pqrs/historial/rechazadas?page=1&per_page=20")
    ]);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Error desconocido";
    return (
      <main>
        <h1 className="mb-2 text-2xl font-bold text-slate-900">Historial</h1>
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
          <p className="font-medium">No se pudo cargar la API</p>
          <p className="mt-1">{msg}</p>
          <p className="mt-2 text-rose-800/80">
            Asegúrate de que la API Rust esté en marcha y de tener{" "}
            <code className="rounded bg-white/60 px-1">DATABASE_URL</code> correcto.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Historial</h1>
        <p className="mt-1 text-sm text-slate-600">
          Clasificación aceptada vs. rechazos (ofensivo / no entendible). Total aceptadas:{" "}
          <strong>{aceptadas.total}</strong>, rechazadas: <strong>{rechazadas.total}</strong>.
        </p>
      </div>
      <PqrsTable
        title="Aceptadas"
        items={aceptadas.items}
        emptyMessage="No hay PQRS aceptadas en la primera página."
      />
      <PqrsTable
        title="Rechazadas"
        items={rechazadas.items}
        emptyMessage="No hay PQRS rechazadas en la primera página."
      />
    </main>
  );
}
