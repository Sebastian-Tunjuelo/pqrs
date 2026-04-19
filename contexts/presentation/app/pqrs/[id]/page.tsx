import Link from "next/link";
import { notFound } from "next/navigation";

import { apiGetServer } from "@/lib/api";
import type { PqrsDetail } from "@/lib/types";

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" });
  } catch {
    return iso;
  }
}

export default async function PqrsDetallePage({ params }: { params: { id: string } }) {
  const id = params.id?.trim();
  if (!id) notFound();

  let pqrs: PqrsDetail;
  try {
    pqrs = await apiGetServer<PqrsDetail>(`/api/v1/pqrs/${encodeURIComponent(id)}`, 0);
  } catch {
    notFound();
  }

  const metaStr =
    pqrs.metadata != null && typeof pqrs.metadata === "object"
      ? JSON.stringify(pqrs.metadata, null, 2)
      : pqrs.metadata != null
        ? String(pqrs.metadata)
        : null;

  return (
    <main className="space-y-6">
      <nav className="flex flex-wrap gap-3 text-sm">
        <Link href="/historial" className="text-brand-700 underline hover:text-brand-900">
          ← Historial
        </Link>
        <Link href="/gestion" className="text-brand-700 underline hover:text-brand-900">
          Gestión
        </Link>
        <Link href="/asistente" className="text-brand-700 underline hover:text-brand-900">
          Asistente
        </Link>
      </nav>

      <header className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">PQRS</p>
        <h1 className="mt-1 text-xl font-semibold text-slate-900">
          {pqrs.id_externo ?? pqrs.id}
        </h1>
        <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-slate-500">Tipo</dt>
            <dd className="font-mono text-slate-800">{pqrs.tipo ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Radicado</dt>
            <dd className="text-slate-800">{fmtDate(pqrs.fecha_radicado)}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Clasificación</dt>
            <dd className="text-slate-800">{pqrs.estado_clasificacion}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Gestión</dt>
            <dd className="text-slate-800">{pqrs.estado_gestion ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Riesgo</dt>
            <dd className="text-slate-800">{pqrs.nivel_riesgo ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Límite</dt>
            <dd className="text-slate-800">{pqrs.fecha_limite ?? "—"}</dd>
          </div>
          {pqrs.confianza_clasificacion != null && (
            <div>
              <dt className="text-slate-500">Confianza clasificación</dt>
              <dd className="text-slate-800">{pqrs.confianza_clasificacion}</dd>
            </div>
          )}
        </dl>
      </header>

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-base font-semibold text-slate-800">Texto de la PQRS</h2>
        <article className="mt-3 max-w-none rounded-lg bg-slate-50 p-4 text-sm leading-relaxed text-slate-900">
          <pre className="whitespace-pre-wrap font-sans break-words">{pqrs.contenido}</pre>
        </article>
      </section>

      {pqrs.razon_rechazo && (
        <section className="rounded-xl border border-amber-200 bg-amber-50/80 p-5 shadow-sm">
          <h2 className="text-base font-semibold text-amber-950">Razón de rechazo</h2>
          <p className="mt-2 whitespace-pre-wrap text-sm text-amber-950">{pqrs.razon_rechazo}</p>
        </section>
      )}

      {metaStr && (
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-base font-semibold text-slate-800">Metadata</h2>
          <pre className="mt-2 max-h-80 overflow-auto rounded-md bg-slate-900 p-3 text-xs text-slate-100">
            {metaStr}
          </pre>
        </section>
      )}
    </main>
  );
}
