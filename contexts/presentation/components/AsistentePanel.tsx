"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { apiFetch, apiPostJson } from "@/lib/api";
import type { AssistOllamaReply, Paginated, PqrsListItem } from "@/lib/types";

type Tab = "rechazo" | "gestion";

export function AsistentePanel({ initialTab }: { initialTab?: Tab }) {
  const [tab, setTab] = useState<Tab>(initialTab === "gestion" ? "gestion" : "rechazo");
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
      let data: Paginated<PqrsListItem>;
      let usaTodas = false;
      if (tab === "rechazo") {
        data = await apiFetch<Paginated<PqrsListItem>>(
          "/api/v1/pqrs/historial/rechazadas?page=1&per_page=80"
        );
        if (data.items.length === 0) {
          data = await apiFetch<Paginated<PqrsListItem>>("/api/v1/pqrs?page=1&per_page=80");
          usaTodas = true;
        }
      } else {
        data = await apiFetch<Paginated<PqrsListItem>>("/api/v1/pqrs?page=1&per_page=80");
      }
      setRechazoUsaTodas(usaTodas);
      setItems(data.items);
      setSelectedId((id) => {
        if (id && data.items.some((x) => x.id === id)) return id;
        return data.items[0]?.id ?? "";
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
      const path =
        tab === "rechazo"
          ? "/api/v1/assist/ollama/explicar-rechazo"
          : "/api/v1/assist/ollama/mensaje-gestion";
      const r = await apiPostJson<AssistOllamaReply>(path, { pqrs_id: selectedId });
      setOut(r.respuesta);
      setModelo(r.modelo);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error al consultar Ollama");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-3">
        <button
          type="button"
          onClick={() => setTab("rechazo")}
          className={`rounded-lg px-4 py-2 text-sm font-medium ${
            tab === "rechazo"
              ? "bg-brand-600 text-white shadow"
              : "bg-slate-100 text-slate-700 hover:bg-slate-200"
          }`}
        >
          Por qué rechazo (Ollama)
        </button>
        <button
          type="button"
          onClick={() => setTab("gestion")}
          className={`rounded-lg px-4 py-2 text-sm font-medium ${
            tab === "gestion"
              ? "bg-brand-600 text-white shadow"
              : "bg-slate-100 text-slate-700 hover:bg-slate-200"
          }`}
        >
          Mensaje para gestión
        </button>
      </div>

      <p className="text-sm text-slate-600">
        {tab === "rechazo"
          ? rechazoUsaTodas
            ? "No hay rechazadas en la muestra: se listan PQRS generales. Ollama usa texto, estado de clasificación y razón de rechazo si existe."
            : "Lista de PQRS con clasificación rechazada. Ollama usa el texto, el estado y la razón registrada en base de datos."
          : "Cualquier PQRS reciente: se redacta un borrador interno para el equipo de gestión (requiere Ollama en marcha, p. ej. Docker)."}
      </p>

      {listErr && (
        <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">{listErr}</p>
      )}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="min-w-0 flex-1">
          <label htmlFor="pqrs-pick" className="mb-1 block text-xs font-medium text-slate-600">
            PQRS
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
        <button
          type="button"
          disabled={loading || loadingList || !selectedId}
          onClick={() => void runAssist()}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-brand-700 disabled:opacity-60"
        >
          {loading ? "Consultando…" : tab === "rechazo" ? "Preguntar a Ollama" : "Generar borrador"}
        </button>
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

      <p className="text-xs text-slate-500">
        Variables de entorno en la API:{" "}
        <code className="rounded bg-slate-100 px-1">OLLAMA_URL</code> (default{" "}
        <code className="rounded bg-slate-100 px-1">http://127.0.0.1:11434</code>) y{" "}
        <code className="rounded bg-slate-100 px-1">OLLAMA_MODEL</code>.{" "}
        <Link href="/gestion" className="text-brand-700 underline">
          Volver a gestión
        </Link>
      </p>
    </div>
  );
}
