"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import type { AssistMode } from "@/lib/assistOllama";
import { apiFetchAllPqrsList, apiPostAssist } from "@/lib/api";
import type { AssistOllamaReply, PqrsListItem } from "@/lib/types";

const TABS: { id: AssistMode; label: string; hint: string }[] = [
  {
    id: "clasificacion",
    label: "Clasificación",
    hint: "Por qué está aceptada, rechazada o pendiente de clasificación (y la confianza)."
  },
  {
    id: "riesgo",
    label: "Riesgo",
    hint: "Por qué el nivel de riesgo (BAJO/MEDIO/ALTO/CRÍTICO) y qué implica para plazos y prioridad."
  },
  {
    id: "rechazo",
    label: "Rechazo",
    hint: "Enfocado en rechazos ofensivo / no entendible y la razón registrada."
  },
  {
    id: "gestion",
    label: "Mensaje gestión",
    hint: "Borrador interno para el equipo de gestión."
  }
];

export function AsistentePanel({ initialTab }: { initialTab?: AssistMode }) {
  const validInitial =
    initialTab && TABS.some((t) => t.id === initialTab) ? initialTab : ("rechazo" as AssistMode);
  const [tab, setTab] = useState<AssistMode>(validInitial);

  useEffect(() => {
    if (initialTab && TABS.some((t) => t.id === initialTab)) setTab(initialTab);
  }, [initialTab]);
  const [items, setItems] = useState<PqrsListItem[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [listErr, setListErr] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [out, setOut] = useState<string | null>(null);
  const [modelo, setModelo] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [rechazoUsaTodas, setRechazoUsaTodas] = useState(false);

  const loadList = useCallback(async () => {
    setListErr(null);
    setLoadingList(true);
    try {
      let rows: PqrsListItem[];
      let usaTodas = false;
      if (tab === "rechazo") {
        rows = await apiFetchAllPqrsList("/api/v1/pqrs/historial/rechazadas");
        if (rows.length === 0) {
          rows = await apiFetchAllPqrsList("/api/v1/pqrs");
          usaTodas = true;
        }
      } else {
        rows = await apiFetchAllPqrsList("/api/v1/pqrs");
      }
      setRechazoUsaTodas(usaTodas);
      setItems(rows);
      setSelectedId((id) => {
        if (id && rows.some((x) => x.id === id)) return id;
        return rows[0]?.id ?? "";
      });
    } catch (e) {
      setListErr(e instanceof Error ? e.message : "Error al cargar PQRS");
      setItems([]);
      setSelectedId("");
    } finally {
      setLoadingList(false);
    }
  }, [tab]);

  useEffect(() => {
    void loadList();
  }, [loadList]);

  async function runAssist() {
    setErr(null);
    setOut(null);
    setModelo(null);
    if (!selectedId) {
      setErr("Seleccione una PQRS.");
      return;
    }
    setLoading(true);
    try {
      const r = await apiPostAssist<AssistOllamaReply>({ pqrs_id: selectedId, mode: tab });
      setOut(r.respuesta);
      setModelo(r.modelo);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error al consultar Ollama");
    } finally {
      setLoading(false);
    }
  }

  const tabMeta = TABS.find((t) => t.id === tab);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-3">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-lg px-3 py-2 text-sm font-medium ${
              tab === t.id
                ? "bg-brand-600 text-white shadow"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <p className="text-sm text-slate-600">
        {tab === "rechazo" && rechazoUsaTodas
          ? "No hay rechazadas: se listan todas las PQRS. Puede usar pestaña Clasificación o Riesgo para cualquier caso."
          : tabMeta?.hint}
      </p>

      {listErr && (
        <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">{listErr}</p>
      )}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="min-w-0 flex-1">
          <label htmlFor="pqrs-pick" className="mb-1 block text-xs font-medium text-slate-600">
            PQRS ({items.length} cargadas)
          </label>
          <select
            id="pqrs-pick"
            disabled={loadingList || !items.length}
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            className="w-full max-w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            {!items.length && <option value="">—</option>}
            {items.map((p) => (
              <option key={p.id} value={p.id}>
                {(p.id_externo ?? p.id.slice(0, 8)) + "…"} · {p.estado_clasificacion} ·{" "}
                {p.contenido.slice(0, 56)}
                {p.contenido.length > 56 ? "…" : ""}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            disabled={loading || loadingList || !selectedId}
            onClick={() => void runAssist()}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-brand-700 disabled:opacity-60"
          >
            {loading ? "Consultando Ollama…" : "Consultar Ollama"}
          </button>
          {selectedId ? (
            <Link
              href={`/pqrs/${selectedId}`}
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-brand-700 shadow-sm hover:bg-slate-50"
            >
              Ver texto completo
            </Link>
          ) : null}
        </div>
      </div>

      {err && (
        <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">{err}</p>
      )}

      {out && (
        <section className="rounded-xl border border-slate-200 bg-slate-50/80 p-4 shadow-sm">
          {modelo && <p className="mb-2 text-xs text-slate-500">Modelo: {modelo}</p>}
          <div className="whitespace-pre-wrap text-sm text-slate-800">{out}</div>
        </section>
      )}
    </div>
  );
}
