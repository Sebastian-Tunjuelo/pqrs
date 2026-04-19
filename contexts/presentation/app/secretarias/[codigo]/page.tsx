import Link from "next/link";
import { notFound } from "next/navigation";

import { PlazoDiasBadge } from "@/components/PlazoDiasBadge";
import { apiGetServer } from "@/lib/api";
import { tipoConSignificado } from "@/lib/tipoPqrs";
import type { Paginated, PqrsListItem, SecretariaRow } from "@/lib/types";

export const dynamic = "force-dynamic";
export const revalidate = 0;

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" });
  } catch {
    return iso;
  }
}

export default async function SecretariaPqrsPage({
  params,
  searchParams
}: {
  params: { codigo: string };
  searchParams?: { page?: string };
}) {
  const codigo = params.codigo?.trim().toUpperCase();
  if (!codigo) notFound();

  const pageRaw = searchParams?.page;
  const page = Math.max(1, Number.parseInt(pageRaw ?? "1", 10) || 1);
  const perPage = 25;

  let list: Paginated<PqrsListItem>;
  let catalog: SecretariaRow[];
  try {
    [list, catalog] = await Promise.all([
      apiGetServer<Paginated<PqrsListItem>>(
        `/api/v1/secretarias/${encodeURIComponent(codigo)}/pqrs?page=${page}&per_page=${perPage}`,
        0
      ),
      apiGetServer<SecretariaRow[]>("/api/v1/secretarias", 0)
    ]);
  } catch {
    notFound();
  }

  const meta = catalog.find((s) => s.codigo === codigo);
  const totalPages = Math.max(1, Math.ceil(list.total / list.per_page));

  return (
    <main className="space-y-6">
      <nav aria-label="Migas de pan" className="text-sm text-neutral-600">
        <ol className="flex flex-wrap items-center gap-1">
          <li>
            <Link href="/" className="text-primary hover:underline">
              Inicio
            </Link>
          </li>
          <li aria-hidden className="text-neutral-400">
            /
          </li>
          <li>
            <Link href="/secretarias" className="text-primary hover:underline">
              Secretarías
            </Link>
          </li>
          <li aria-hidden className="text-neutral-400">
            /
          </li>
          <li className="font-medium text-neutral-900" aria-current="page">
            {codigo}
          </li>
        </ol>
      </nav>

      <header>
        <h1 className="text-2xl font-bold text-neutral-900">
          PQRS — <span className="font-mono text-primary">{codigo}</span>
        </h1>
        {meta ? <p className="mt-1 text-sm text-neutral-600">{meta.nombre}</p> : null}
        <p className="mt-2 text-xs text-neutral-500">
          {list.total} registro{list.total === 1 ? "" : "s"} · página {list.page} de {totalPages}
        </p>
      </header>

      {list.items.length === 0 ? (
        <p className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
          No hay PQRS asociadas a esta secretaría en la base actual.
        </p>
      ) : (
        <>
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-4 py-2">Tipo</th>
                    <th className="px-4 py-2">Contenido</th>
                    <th className="px-4 py-2">Radicado</th>
                    <th className="px-4 py-2">Plazo (cal.)</th>
                    <th className="px-4 py-2">Clasificación</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {list.items.map((row) => (
                    <tr key={row.id} className="hover:bg-slate-50/80">
                      <td className="max-w-[10rem] whitespace-normal px-4 py-2 text-xs leading-snug">
                        {tipoConSignificado(row.tipo)}
                      </td>
                      <td className="max-w-md px-4 py-2 text-slate-700">
                        <Link
                          href={`/pqrs/${row.id}`}
                          className="group block rounded-md px-1 py-0.5 outline-none ring-brand-400 hover:bg-brand-50 focus-visible:ring-2"
                        >
                          <span className="line-clamp-2 group-hover:text-brand-950">{row.contenido}</span>
                        </Link>
                      </td>
                      <td className="whitespace-nowrap px-4 py-2 text-slate-600">
                        {fmtDate(row.fecha_radicado)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-2">
                        <PlazoDiasBadge fechaLimite={row.fecha_limite} />
                      </td>
                      <td className="whitespace-nowrap px-4 py-2 text-xs">{row.estado_clasificacion}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {totalPages > 1 ? (
            <nav className="flex flex-wrap items-center gap-2 text-sm" aria-label="Paginación">
              {page > 1 ? (
                <Link
                  href={`/secretarias/${encodeURIComponent(codigo)}?page=${page - 1}`}
                  className="rounded-lg border border-slate-200 px-3 py-1.5 text-primary hover:bg-slate-50"
                >
                  Anterior
                </Link>
              ) : (
                <span className="rounded-lg border border-slate-100 px-3 py-1.5 text-slate-400">Anterior</span>
              )}
              {page < totalPages ? (
                <Link
                  href={`/secretarias/${encodeURIComponent(codigo)}?page=${page + 1}`}
                  className="rounded-lg border border-slate-200 px-3 py-1.5 text-primary hover:bg-slate-50"
                >
                  Siguiente
                </Link>
              ) : (
                <span className="rounded-lg border border-slate-100 px-3 py-1.5 text-slate-400">Siguiente</span>
              )}
            </nav>
          ) : null}
        </>
      )}
    </main>
  );
}
