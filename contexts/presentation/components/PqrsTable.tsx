import type { PqrsListItem } from "@/lib/types";

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("es-CO", {
      dateStyle: "short",
      timeStyle: "short"
    });
  } catch {
    return iso;
  }
}

export function PqrsTable({
  title,
  items,
  emptyMessage,
  scrollable
}: {
  title: string;
  items: PqrsListItem[];
  emptyMessage?: string;
  /** Lista larga: scroll vertical dentro de la tarjeta. */
  scrollable?: boolean;
}) {
  if (!items.length) {
    return (
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-2 text-base font-semibold text-slate-800">{title}</h2>
        <p className="text-sm text-slate-500">{emptyMessage ?? "Sin registros."}</p>
      </section>
    );
  }

  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-4 py-3">
        <h2 className="text-base font-semibold text-slate-800">{title}</h2>
        <p className="text-xs text-slate-500">
          {items.length} registro{items.length === 1 ? "" : "s"}
        </p>
      </div>
      <div
        className={
          scrollable
            ? "max-h-[min(32rem,70vh)] overflow-y-auto overflow-x-auto"
            : "overflow-x-auto"
        }
      >
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-2">Tipo</th>
              <th className="px-4 py-2">Contenido</th>
              <th className="px-4 py-2">Radicado</th>
              <th className="px-4 py-2">Clasificación</th>
              <th className="px-4 py-2">Gestión</th>
              <th className="px-4 py-2">Riesgo</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((row) => (
              <tr key={row.id} className="hover:bg-slate-50/80">
                <td className="whitespace-nowrap px-4 py-2 font-mono text-xs">{row.tipo ?? "—"}</td>
                <td className="max-w-md px-4 py-2 text-slate-700">
                  <span className="line-clamp-2">{row.contenido}</span>
                </td>
                <td className="whitespace-nowrap px-4 py-2 text-slate-600">
                  {fmtDate(row.fecha_radicado)}
                </td>
                <td className="whitespace-nowrap px-4 py-2 text-xs">{row.estado_clasificacion}</td>
                <td className="whitespace-nowrap px-4 py-2 text-xs">{row.estado_gestion ?? "—"}</td>
                <td className="whitespace-nowrap px-4 py-2 text-xs">{row.nivel_riesgo ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
