import { PqrsTable } from "@/components/PqrsTable";
import { apiGetServerAllPqrs } from "@/lib/api";
import type { PqrsListItem } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function HistorialPage() {
  let aceptadas: { items: PqrsListItem[]; total: number };
  let rechazadas: { items: PqrsListItem[]; total: number };
  try {
    [aceptadas, rechazadas] = await Promise.all([
      apiGetServerAllPqrs("/api/v1/pqrs/historial/aceptadas"),
      apiGetServerAllPqrs("/api/v1/pqrs/historial/rechazadas")
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

  const suma = aceptadas.total + rechazadas.total;

  return (
    <main className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Historial</h1>
        <p className="mt-1 text-sm text-slate-600">
          Listado completo cargado desde la API (paginación automática). Aceptadas:{" "}
          <strong>{aceptadas.total}</strong> ({aceptadas.items.length} filas), rechazadas:{" "}
          <strong>{rechazadas.total}</strong> ({rechazadas.items.length} filas). Suma clasificada:{" "}
          <strong>{suma}</strong>.
        </p>
      </div>
      <PqrsTable
        title="Aceptadas (listado completo)"
        items={aceptadas.items}
        scrollable
        emptyMessage="No hay PQRS aceptadas."
      />
      <PqrsTable
        title="Rechazadas (listado completo)"
        items={rechazadas.items}
        scrollable
        emptyMessage="No hay PQRS rechazadas."
      />
    </main>
  );
}
