import Link from "next/link";

import { PlazoDiasBadge } from "@/components/PlazoDiasBadge";
import { tipoConSignificado } from "@/lib/tipoPqrs";
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
      <section className="rounded-xl border border-[#1A4B8C]/20 bg-white p-6 shadow-sm">
        <h2 className="mb-2 text-base font-semibold text-neutral-900">{title}</h2>
        <p className="text-sm text-neutral-500">{emptyMessage ?? "Sin registros."}</p>
      </section>
    );
  }

  return (
    <section className="overflow-hidden rounded-xl border border-[#1A4B8C]/20 bg-white shadow-sm">
      <div className="border-b border-[#1A4B8C]/10 bg-gradient-to-r from-[#1A4B8C]/5 to-[#00A8E8]/5 px-4 py-3">
        <h2 className="text-base font-semibold text-neutral-900">{title}</h2>
        <p className="text-xs text-neutral-500">
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
          <thead className="bg-[#eff6ff] text-xs uppercase tracking-wide text-[#1A4B8C]">
            <tr>
              <th className="px-4 py-2">Tipo</th>
              <th className="px-4 py-2">Contenido</th>
              <th className="px-4 py-2">Radicado</th>
              <th className="px-4 py-2">Clasificación</th>
              <th className="px-4 py-2">Gestión</th>
              <th className="px-4 py-2">Riesgo</th>
              <th className="px-4 py-2">Plazo (cal.)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1A4B8C]/10">
            {items.map((row) => (
              <tr key={row.id} className="transition-colors hover:bg-[#eff6ff]/60">
                <td className="max-w-[10rem] whitespace-normal px-4 py-2 text-xs leading-snug">
                  {tipoConSignificado(row.tipo)}
                </td>
                <td className="max-w-md px-4 py-2 text-neutral-700">
                  <Link
                    href={`/pqrs/${row.id}`}
                    className="group block min-h-11 rounded-md px-1 py-1 outline-none ring-[#1A4B8C] hover:bg-[#eff6ff] focus-visible:ring-2"
                    title="Ver texto completo"
                  >
                    <span className="line-clamp-2 group-hover:text-[#1A4B8C]">{row.contenido}</span>
                    <span className="mt-1 block text-xs font-semibold text-[#1A4B8C] underline-offset-2 group-hover:underline">
                      Ver texto completo
                    </span>
                  </Link>
                </td>
                <td className="whitespace-nowrap px-4 py-2 text-neutral-600">
                  {fmtDate(row.fecha_radicado)}
                </td>
                <td className="whitespace-nowrap px-4 py-2 text-xs">{row.estado_clasificacion}</td>
                <td className="whitespace-nowrap px-4 py-2 text-xs">{row.estado_gestion ?? "—"}</td>
                <td className="whitespace-nowrap px-4 py-2 text-xs">{row.nivel_riesgo ?? "—"}</td>
                <td className="whitespace-nowrap px-4 py-2">
                  <PlazoDiasBadge fechaLimite={row.fecha_limite} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
