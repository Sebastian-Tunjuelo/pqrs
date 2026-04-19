"use client";

import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import type { Paginated, PqrsListItem } from "@/lib/types";

function diasCalendarioRestantes(fechaLimite: string | null): string {
  if (!fechaLimite) return "—";
  const t = new Date(fechaLimite + "T12:00:00").getTime();
  const d = Math.ceil((t - Date.now()) / (86400 * 1000));
  return String(d);
}

function toCsv(rows: PqrsListItem[]): string {
  const header = [
    "radicado",
    "fecha_radicado",
    "tipo",
    "secretaria",
    "estado_clasificacion",
    "estado_gestion",
    "validation_status",
    "nivel_riesgo",
    "dias_restantes_calendario"
  ];
  const lines = rows.map((r) =>
    [
      r.id_externo ?? r.id,
      r.fecha_radicado,
      r.tipo ?? "",
      "",
      r.estado_clasificacion,
      r.estado_gestion ?? "",
      r.validation_status ?? "",
      r.nivel_riesgo ?? "",
      diasCalendarioRestantes(r.fecha_limite)
    ]
      .map((c) => `"${String(c).replace(/"/g, '""')}"`)
      .join(",")
  );
  return [header.join(","), ...lines].join("\r\n");
}

function downloadCsv(filename: string, content: string) {
  const blob = new Blob(["\ufeff", content], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function HistorialView() {
  const [tipo, setTipo] = useState("");
  const [clasif, setClasif] = useState("");
  const [gestion, setGestion] = useState("");
  const [validacion, setValidacion] = useState("");
  const [riesgo, setRiesgo] = useState("");
  const [secretaria, setSecretaria] = useState("");
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [page, setPage] = useState(1);
  const perPage = 25;

  const [data, setData] = useState<Paginated<PqrsListItem> | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const buildParams = useCallback(
    (pg: number) => {
      const p = new URLSearchParams();
      p.set("page", String(pg));
      p.set("per_page", String(perPage));
      if (tipo) p.set("tipo", tipo);
      if (clasif) p.set("estado_clasificacion", clasif);
      if (gestion) p.set("estado_gestion", gestion);
      if (validacion) p.set("estado", validacion);
      if (riesgo) p.set("riesgo", riesgo);
      if (secretaria.trim()) p.set("secretaria", secretaria.trim().toUpperCase());
      if (desde) p.set("fecha_desde", desde);
      if (hasta) p.set("fecha_hasta", hasta);
      return p;
    },
    [tipo, clasif, gestion, validacion, riesgo, secretaria, desde, hasta, perPage]
  );

  const loadPage = useCallback(
    async (pg: number) => {
      setLoading(true);
      setErr(null);
      try {
        const qs = buildParams(pg).toString();
        const res = await apiFetch<Paginated<PqrsListItem>>(`/api/v1/pqrs?${qs}`);
        setData(res);
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Error");
        setData(null);
      } finally {
        setLoading(false);
      }
    },
    [buildParams]
  );

  useEffect(() => {
    void loadPage(page);
  }, [page, loadPage]);

  const exportCurrent = () => {
    if (!data?.items.length) return;
    downloadCsv(`pqrs_historial_p${page}.csv`, toCsv(data.items));
  };

  const exportAllPages = async () => {
    setLoading(true);
    setErr(null);
    try {
      const acc: PqrsListItem[] = [];
      let pg = 1;
      let total = Infinity;
      const base = buildParams(1);
      base.set("per_page", "200");
      while (acc.length < total && pg < 80) {
        base.set("page", String(pg));
        const chunk = await apiFetch<Paginated<PqrsListItem>>(`/api/v1/pqrs?${base.toString()}`);
        if (pg === 1) total = chunk.total;
        acc.push(...chunk.items);
        if (chunk.items.length === 0) break;
        pg += 1;
      }
      downloadCsv("pqrs_historial_filtrado.csv", toCsv(acc));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error exportando");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-card border border-neutral-100 bg-white p-4 shadow-card">
        <h2 className="text-base font-semibold text-neutral-900">Filtros</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <label className="text-xs text-neutral-600">
            Tipo
            <select
              value={tipo}
              onChange={(e) => setTipo(e.target.value)}
              className="mt-1 w-full rounded-lg border border-neutral-200 px-2 py-1.5 text-sm"
            >
              <option value="">Todos</option>
              <option value="P">P</option>
              <option value="Q">Q</option>
              <option value="R">R</option>
              <option value="S">S</option>
              <option value="D">D</option>
            </select>
          </label>
          <label className="text-xs text-neutral-600">
            Clasificación IA
            <select
              value={clasif}
              onChange={(e) => setClasif(e.target.value)}
              className="mt-1 w-full rounded-lg border border-neutral-200 px-2 py-1.5 text-sm"
            >
              <option value="">Todas</option>
              <option value="ACEPTADA">ACEPTADA</option>
              <option value="RECHAZADA_OFENSIVO">RECHAZADA_OFENSIVO</option>
              <option value="RECHAZADA_NO_ENTENDIBLE">RECHAZADA_NO_ENTENDIBLE</option>
            </select>
          </label>
          <label className="text-xs text-neutral-600">
            Estado gestión
            <select
              value={gestion}
              onChange={(e) => setGestion(e.target.value)}
              className="mt-1 w-full rounded-lg border border-neutral-200 px-2 py-1.5 text-sm"
            >
              <option value="">Todos</option>
              <option value="PENDIENTE">PENDIENTE</option>
              <option value="EN_TRAMITE">EN_TRAMITE</option>
              <option value="RESPONDIDA">RESPONDIDA</option>
              <option value="VENCIDA">VENCIDA</option>
            </select>
          </label>
          <label className="text-xs text-neutral-600">
            Validación humana
            <select
              value={validacion}
              onChange={(e) => setValidacion(e.target.value)}
              className="mt-1 w-full rounded-lg border border-neutral-200 px-2 py-1.5 text-sm"
            >
              <option value="">Todas</option>
              <option value="PENDING_VALIDATION">PENDING_VALIDATION</option>
              <option value="VALIDATED">VALIDATED</option>
              <option value="REJECTED_BY_OFFICER">REJECTED_BY_OFFICER</option>
              <option value="CORRECTION_REQUESTED">CORRECTION_REQUESTED</option>
            </select>
          </label>
          <label className="text-xs text-neutral-600">
            Riesgo
            <select
              value={riesgo}
              onChange={(e) => setRiesgo(e.target.value)}
              className="mt-1 w-full rounded-lg border border-neutral-200 px-2 py-1.5 text-sm"
            >
              <option value="">Todos</option>
              <option value="CRITICO">CRITICO</option>
              <option value="ALTO">ALTO</option>
              <option value="MEDIO">MEDIO</option>
              <option value="BAJO">BAJO</option>
            </select>
          </label>
          <label className="text-xs text-neutral-600">
            Secretaría (código)
            <input
              value={secretaria}
              onChange={(e) => setSecretaria(e.target.value)}
              className="mt-1 w-full rounded-lg border border-neutral-200 px-2 py-1.5 text-sm"
              placeholder="SDE"
            />
          </label>
          <label className="text-xs text-neutral-600">
            Fecha desde
            <input
              type="date"
              value={desde}
              onChange={(e) => setDesde(e.target.value)}
              className="mt-1 w-full rounded-lg border border-neutral-200 px-2 py-1.5 text-sm"
            />
          </label>
          <label className="text-xs text-neutral-600">
            Fecha hasta
            <input
              type="date"
              value={hasta}
              onChange={(e) => setHasta(e.target.value)}
              className="mt-1 w-full rounded-lg border border-neutral-200 px-2 py-1.5 text-sm"
            />
          </label>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => {
              setPage(1);
              void loadPage(1);
            }}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90"
          >
            Aplicar filtros
          </button>
          <button
            type="button"
            onClick={exportCurrent}
            disabled={!data?.items.length}
            className="rounded-lg border border-neutral-200 bg-white px-4 py-2 text-sm font-medium hover:bg-neutral-50 disabled:opacity-50"
          >
            Exportar CSV (página)
          </button>
          <button
            type="button"
            onClick={() => void exportAllPages()}
            className="rounded-lg border border-accent/50 bg-accent/15 px-4 py-2 text-sm font-medium text-neutral-900 hover:bg-accent/25"
          >
            Exportar CSV (todo el filtro)
          </button>
        </div>
      </div>

      {err ? (
        <p className="rounded-lg border border-danger/30 bg-danger/10 p-3 text-sm text-danger">{err}</p>
      ) : null}

      <div className="rounded-card border border-neutral-100 bg-white shadow-card">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-neutral-100 px-4 py-3">
          <p className="text-sm font-medium text-neutral-900">
            {data ? `Resultados: ${data.total} PQRS` : "Cargando…"}
          </p>
          {loading ? <span className="text-xs text-neutral-500">Actualizando…</span> : null}
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-neutral-50 text-xs font-semibold uppercase text-neutral-600">
              <tr>
                <th className="px-3 py-2">Radicado</th>
                <th className="px-3 py-2">Fecha</th>
                <th className="px-3 py-2">Tipo</th>
                <th className="px-3 py-2">Secretaría</th>
                <th className="px-3 py-2">Estado</th>
                <th className="px-3 py-2">Días rest.</th>
              </tr>
            </thead>
            <tbody>
              {(data?.items ?? []).map((r) => (
                <tr key={r.id} className="border-t border-neutral-100 hover:bg-neutral-50/80">
                  <td className="px-3 py-2 font-mono text-xs">{r.id_externo ?? r.id.slice(0, 8)}</td>
                  <td className="px-3 py-2 text-xs">{r.fecha_radicado?.slice(0, 10)}</td>
                  <td className="px-3 py-2">{r.tipo}</td>
                  <td className="px-3 py-2 text-neutral-500">—</td>
                  <td className="px-3 py-2 text-xs">
                    <div>{r.estado_clasificacion}</div>
                    <div className="text-neutral-500">{r.validation_status}</div>
                  </td>
                  <td className="px-3 py-2">{diasCalendarioRestantes(r.fecha_limite)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {data && data.total > perPage ? (
          <div className="flex items-center justify-between border-t border-neutral-100 px-4 py-3 text-sm">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="rounded-md border px-3 py-1 disabled:opacity-40"
            >
              Anterior
            </button>
            <span>
              Página {page} de {Math.max(1, Math.ceil(data.total / perPage))}
            </span>
            <button
              type="button"
              disabled={page * perPage >= data.total}
              onClick={() => setPage((p) => p + 1)}
              className="rounded-md border px-3 py-1 disabled:opacity-40"
            >
              Siguiente
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
