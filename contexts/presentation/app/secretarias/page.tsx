import Link from "next/link";
import { notFound } from "next/navigation";

import { apiGetServer } from "@/lib/api";
import type { SecretariaRow } from "@/lib/types";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function SecretariasIndexPage() {
  let rows: SecretariaRow[];
  try {
    rows = await apiGetServer<SecretariaRow[]>("/api/v1/secretarias", 0);
  } catch {
    notFound();
  }

  return (
    <main className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-neutral-900">Secretarías</h1>
        <p className="mt-2 max-w-2xl text-sm text-neutral-600">
          Catálogo desde <code className="rounded bg-neutral-100 px-1">dim_secretaria</code>. Elija una
          dependencia para ver sus PQRS o use el filtro en{" "}
          <Link href="/historial" className="text-primary hover:underline">
            Historial
          </Link>
          .
        </p>
      </div>
      <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {rows.map((s) => (
          <li key={s.codigo}>
            <Link
              href={`/secretarias/${encodeURIComponent(s.codigo)}`}
              className="block rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-brand-300 hover:shadow-md"
            >
              <p className="font-mono text-xs font-semibold text-brand-700">{s.codigo}</p>
              <p className="mt-1 text-sm font-medium text-slate-900">{s.nombre}</p>
              <span className="mt-2 inline-block text-xs font-medium text-brand-600">Ver PQRS →</span>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
