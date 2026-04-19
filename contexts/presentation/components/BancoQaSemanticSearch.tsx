"use client";

import { useState, type FormEvent } from "react";

import { apiPostJson } from "@/lib/api";
import type { BancoQaSemanticRow } from "@/lib/types";

export function BancoQaSemanticSearch() {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [rows, setRows] = useState<BancoQaSemanticRow[] | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      const data = await apiPostJson<BancoQaSemanticRow[]>("/api/v1/banco-qa/buscar-semantico", {
        query: q
      });
      setRows(data);
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Error en búsqueda semántica");
      setRows(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={onSubmit} className="flex flex-col gap-2 sm:flex-row sm:items-end">
        <div className="flex-1">
          <label htmlFor="bqs" className="mb-1 block text-xs font-medium text-neutral-600">
            Búsqueda semántica (pgvector + embeddings locales)
          </label>
          <input
            id="bqs"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            placeholder="Ej. plazos ley 1755, emprendimiento comuna…"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white shadow hover:opacity-90 disabled:opacity-60"
        >
          {loading ? "Buscando…" : "Buscar semántico"}
        </button>
      </form>
      {err ? (
        <p className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-neutral-900">
          {err}
          <span className="mt-1 block text-xs text-neutral-600">
            Requiere API con <code className="rounded bg-white/80 px-1">EMBEDDING_URL</code> y{" "}
            <code className="rounded bg-white/80 px-1">python -m banco_qa.embedding_server</code>.
          </span>
        </p>
      ) : null}
      {rows && (
        <ul className="space-y-3">
          {rows.length === 0 && <li className="text-sm text-neutral-500">Sin resultados con embedding.</li>}
          {rows.map((r) => (
            <li key={r.id} className="rounded-lg border border-neutral-100 bg-white p-4 shadow-card">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <p className="text-sm font-semibold text-neutral-900">{r.pregunta}</p>
                <span className="rounded-full bg-accent/25 px-2 py-0.5 text-xs font-semibold text-neutral-900">
                  similitud {(r.similarity * 100).toFixed(1)}%
                </span>
              </div>
              <p className="mt-2 text-sm text-neutral-700">{r.respuesta}</p>
              <div className="mt-2 flex flex-wrap gap-2 text-xs text-neutral-500">
                {r.secretaria_codigo ? <span>Secretaría: {r.secretaria_codigo}</span> : null}
                <span className="rounded bg-success/15 px-2 py-0.5 font-medium text-success">
                  Precedente validado
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
