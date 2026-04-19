"use client";

import { useState, type FormEvent } from "react";

import { apiPostJson } from "@/lib/api";
import type { BancoQaRow } from "@/lib/types";

export function BancoQaSearch() {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [rows, setRows] = useState<BancoQaRow[] | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      const data = await apiPostJson<BancoQaRow[]>("/api/v1/banco-qa/buscar", { query: q });
      setRows(data);
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Error al buscar");
      setRows(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={onSubmit} className="flex flex-col gap-2 sm:flex-row sm:items-end">
        <div className="flex-1">
          <label htmlFor="bq" className="mb-1 block text-xs font-medium text-slate-600">
            Buscar en preguntas y respuestas
          </label>
          <input
            id="bq"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            placeholder="Ej. trámite, plazo, secretaría…"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-brand-700 disabled:opacity-60"
        >
          {loading ? "Buscando…" : "Buscar"}
        </button>
      </form>
      {err && (
        <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">{err}</p>
      )}
      {rows && (
        <ul className="space-y-3">
          {rows.length === 0 && <li className="text-sm text-slate-500">Sin resultados.</li>}
          {rows.map((r) => (
            <li key={r.id} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-semibold text-slate-800">{r.pregunta}</p>
              <p className="mt-2 text-sm text-slate-600">{r.respuesta}</p>
              <p className="mt-2 text-xs text-slate-400">
                {r.secretaria_codigo ? `Secretaría: ${r.secretaria_codigo}` : "General"}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
