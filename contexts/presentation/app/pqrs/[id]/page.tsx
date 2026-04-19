import Link from "next/link";
import { notFound } from "next/navigation";

import { PlazoDiasBadge } from "@/components/PlazoDiasBadge";
import { apiGetServer } from "@/lib/api";
import {
  deQueTrataPqrs,
  esClasificacionRechazo,
  etiquetaTipo,
  resumenPqrs,
  tituloPqrs
} from "@/lib/pqrsDetalleFormat";
import type { PqrsDetail } from "@/lib/types";

/** Siempre datos frescos desde la API (evita cachés raras y 500 en detalle). */
export const dynamic = "force-dynamic";
export const revalidate = 0;

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" });
  } catch {
    return iso;
  }
}

function metaJsonString(p: PqrsDetail): string | null {
  if (p.metadata == null) return null;
  try {
    if (typeof p.metadata === "object") {
      const s = JSON.stringify(p.metadata, null, 2);
      return s === "{}" ? null : s;
    }
    const raw = String(p.metadata);
    return raw.length ? raw : null;
  } catch {
    return null;
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

  const titulo = tituloPqrs(pqrs);
  const resumen = resumenPqrs(pqrs.contenido ?? "");
  const deQueTrata = deQueTrataPqrs(pqrs, resumen);
  const metaStr = metaJsonString(pqrs);
  const muestraRechazo = esClasificacionRechazo(pqrs.estado_clasificacion) || Boolean(pqrs.razon_rechazo?.trim());

  const radicado = pqrs.id_externo ?? pqrs.id.slice(0, 8);

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
            <Link href="/historial" className="text-primary hover:underline">
              Historial
            </Link>
          </li>
          <li aria-hidden className="text-neutral-400">
            /
          </li>
          <li className="font-medium text-neutral-900" aria-current="page">
            {radicado}
          </li>
        </ol>
      </nav>
      <nav className="flex flex-wrap gap-3 text-xs text-neutral-500" aria-label="Accesos rápidos">
        <Link href="/gestion" className="text-primary hover:underline">
          Gestión
        </Link>
        <span aria-hidden>·</span>
        <Link href="/asistente" className="text-primary hover:underline">
          Asistente
        </Link>
      </nav>

      <header className="rounded-xl border border-slate-200 bg-gradient-to-br from-brand-50 to-white p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-brand-800">Título de la PQRS</p>
        <h1 className="mt-2 text-2xl font-bold leading-snug text-slate-900">{titulo}</h1>
        <p className="mt-3 text-sm text-slate-600">
          <span className="font-mono font-medium text-slate-800">{pqrs.id_externo ?? pqrs.id}</span>
          {" · "}
          {etiquetaTipo(pqrs.tipo)}
          {" · Radicado "}
          {fmtDate(pqrs.fecha_radicado)}
        </p>
      </header>

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Resumen de la PQRS</h2>
        <p className="mt-2 text-base leading-relaxed text-slate-800">{resumen}</p>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">De qué trata</h2>
        <p className="mt-2 text-base leading-relaxed text-slate-800">{deQueTrata}</p>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">La PQRS (texto íntegro)</h2>
        <article className="mt-3 max-w-none rounded-lg border border-slate-100 bg-slate-50 p-4 text-sm leading-relaxed text-slate-900">
          <pre className="whitespace-pre-wrap font-sans break-words">{pqrs.contenido ?? ""}</pre>
        </article>
      </section>

      {muestraRechazo && (
        <section className="rounded-xl border border-amber-200 bg-amber-50/90 p-5 shadow-sm">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-amber-900">Razón de rechazo</h2>
          {pqrs.razon_rechazo?.trim() ? (
            <p className="mt-2 whitespace-pre-wrap text-base leading-relaxed text-amber-950">{pqrs.razon_rechazo}</p>
          ) : (
            <p className="mt-2 text-sm text-amber-900">
              No consta un texto detallado de rechazo en el sistema. La clasificación registrada es «
              {pqrs.estado_clasificacion}».
            </p>
          )}
        </section>
      )}

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Datos de radicación y trámite</h2>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-slate-500">Identificador interno</dt>
            <dd className="break-all font-mono text-xs text-slate-800">{pqrs.id}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Radicado externo</dt>
            <dd className="font-mono text-slate-800">{pqrs.id_externo ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Tipo</dt>
            <dd className="text-slate-800">
              {pqrs.tipo ?? "—"} ({etiquetaTipo(pqrs.tipo)})
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Fecha de radicación</dt>
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
            <dt className="text-slate-500">Fecha límite</dt>
            <dd className="flex flex-wrap items-center gap-2 text-slate-800">
              <span>{pqrs.fecha_limite ?? "—"}</span>
              {pqrs.fecha_limite ? <PlazoDiasBadge fechaLimite={pqrs.fecha_limite} /> : null}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Territorio (id)</dt>
            <dd className="text-slate-800">{pqrs.territorio_id ?? "—"}</dd>
          </div>
          {pqrs.confianza_clasificacion != null && (
            <div>
              <dt className="text-slate-500">Confianza clasificación</dt>
              <dd className="text-slate-800">{pqrs.confianza_clasificacion}</dd>
            </div>
          )}
          {pqrs.created_at && (
            <div>
              <dt className="text-slate-500">Creado en sistema</dt>
              <dd className="text-slate-800">{fmtDate(pqrs.created_at)}</dd>
            </div>
          )}
          {pqrs.updated_at && (
            <div>
              <dt className="text-slate-500">Última actualización</dt>
              <dd className="text-slate-800">{fmtDate(pqrs.updated_at)}</dd>
            </div>
          )}
        </dl>
      </section>

      {metaStr && (
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Metadata</h2>
          <p className="mt-1 text-xs text-slate-500">
            Objeto JSON asociado al registro (p. ej. banderas demo, índice sintético, arquetipo).
          </p>
          <pre className="mt-3 max-h-96 overflow-auto rounded-md bg-slate-900 p-4 text-xs text-slate-100">
            {metaStr}
          </pre>
        </section>
      )}
    </main>
  );
}
