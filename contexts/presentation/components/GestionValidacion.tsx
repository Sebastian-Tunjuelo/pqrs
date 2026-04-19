"use client";

import { useCallback, useEffect, useState } from "react";

import { PqrsCard } from "@/components/PqrsCard";
import { apiFetch, apiPatchJson } from "@/lib/api";
import type { Paginated, PqrsDetail, PqrsListItem, PqrsSummaryResponse } from "@/lib/types";

type Props = {
  initial: Paginated<PqrsListItem>;
};

function secretariaLabelFromItem(it: PqrsListItem): string | null {
  const n = it.secretaria_nombre?.trim();
  return n || null;
}

export function GestionValidacion({ initial }: Props) {
  const [items] = useState(initial.items);
  const [selected, setSelected] = useState<PqrsListItem | null>(items[0] ?? null);
  const [detail, setDetail] = useState<PqrsDetail | null>(null);
  const [summary, setSummary] = useState<PqrsSummaryResponse | null>(null);
  const [tab, setTab] = useState<"resumen" | "pre" | "original">("resumen");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const loadDetail = useCallback(async (id: string) => {
    setErr(null);
    setBusy(true);
    try {
      const d = await apiFetch<PqrsDetail>(`/api/v1/pqrs/${encodeURIComponent(id)}`);
      setDetail(d);
      setSummary(null);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error");
    } finally {
      setBusy(false);
    }
  }, []);

  const loadSummary = useCallback(async (id: string) => {
    setErr(null);
    setBusy(true);
    try {
      const s = await apiFetch<PqrsSummaryResponse>(
        `/api/v1/pqrs/${encodeURIComponent(id)}/summary`
      );
      setSummary(s);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error al cargar síntesis");
    } finally {
      setBusy(false);
    }
  }, []);

  const onSelect = (it: PqrsListItem) => {
    setSelected(it);
    void loadDetail(it.id);
    setTab("resumen");
    void loadSummary(it.id);
  };

  useEffect(() => {
    const first = items[0];
    if (!first) return;
    setSelected(first);
    void loadDetail(first.id);
    void loadSummary(first.id);
    // Intencional: solo al montar con datos del servidor.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const validate = async (action: "VALIDATE" | "REJECT" | "REQUEST_CORRECTION") => {
    if (!selected) return;
    setBusy(true);
    setErr(null);
    try {
      await apiPatchJson(`/api/v1/pqrs/${encodeURIComponent(selected.id)}/validate`, {
        action,
        officer_id: "demo-funcionario",
        correction_note:
          action === "REQUEST_CORRECTION"
            ? note || "Solicitud de corrección"
            : action === "REJECT"
              ? note || "Clasificación de IA rechazada por funcionario"
              : undefined
      });
      window.location.reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error");
    } finally {
      setBusy(false);
    }
  };

  const actionButtons = (
    <div className="flex flex-wrap gap-2">
      <button
        type="button"
        disabled={busy}
        onClick={() => void validate("VALIDATE")}
        className="rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-white hover:opacity-90 disabled:opacity-50"
      >
        Validar
      </button>
      <button
        type="button"
        disabled={busy}
        onClick={() => void validate("REJECT")}
        className="rounded-lg border border-danger bg-danger/10 px-3 py-2 text-xs font-semibold text-danger hover:bg-danger/20 disabled:opacity-50"
      >
        Rechazar
      </button>
      <button
        type="button"
        disabled={busy}
        onClick={() => void validate("REQUEST_CORRECTION")}
        className="rounded-lg border border-warning bg-warning/10 px-3 py-2 text-xs font-semibold text-warning hover:bg-warning/20 disabled:opacity-50"
      >
        Corregir
      </button>
    </div>
  );

  return (
    <div id="validacion" className="grid gap-6 lg:grid-cols-[1fr_380px]">
      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-neutral-900">Cola de validación</h2>
        <p className="text-sm text-neutral-900/60">
          PQRS clasificadas por IA pendientes de validación humana (Ley 1755).
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          {items.map((it) => (
            <div
              key={it.id}
              role="presentation"
              onClick={() => onSelect(it)}
              className={`cursor-pointer text-left ${selected?.id === it.id ? "ring-2 ring-primary/40 ring-offset-2 rounded-card" : ""}`}
            >
              <PqrsCard
                item={it}
                lead={it.contenido.slice(0, 120)}
                secretariaLabel={secretariaLabelFromItem(it)}
                onValidate={() => onSelect(it)}
                onCorrect={() => onSelect(it)}
              />
            </div>
          ))}
        </div>
      </div>
      <aside className="rounded-card border border-neutral-100 bg-white p-4 shadow-card">
        {!selected ? (
          <p className="text-sm text-neutral-900/60">Seleccione una PQRS.</p>
        ) : (
          <>
            <div className="flex gap-2 border-b border-neutral-100 pb-3">
              {(
                [
                  ["resumen", "Resumen IA"],
                  ["pre", "Pre-clasificación"],
                  ["original", "PQRS original"]
                ] as const
              ).map(([k, lab]) => (
                <button
                  key={k}
                  type="button"
                  onClick={() => {
                    setTab(k);
                    if (k === "resumen" && !summary) void loadSummary(selected.id);
                  }}
                  className={`rounded-md px-2 py-1 text-xs font-semibold ${
                    tab === k ? "bg-primary text-white" : "text-neutral-700 hover:bg-neutral-50"
                  }`}
                >
                  {lab}
                </button>
              ))}
            </div>
            {err ? <p className="mt-2 text-xs text-danger">{err}</p> : null}
            {busy ? <p className="mt-2 text-xs text-neutral-900/50">Cargando…</p> : null}
            <div className="mt-3 max-h-[420px] overflow-y-auto text-sm">
              {tab === "resumen" ? (
                summary ? (
                  <div className="space-y-3">
                    <p className="font-semibold text-primary">Lead</p>
                    <p>{summary.lead}</p>
                    <p className="font-semibold text-primary">Temas</p>
                    <ul className="list-disc pl-5">
                      {summary.temas.map((t) => (
                        <li key={t}>{t}</li>
                      ))}
                    </ul>
                    <p className="font-semibold text-primary">Resumen ejecutivo</p>
                    <p className="whitespace-pre-wrap text-neutral-900/90">{summary.resumen_ejecutivo}</p>
                  </div>
                ) : (
                  <p className="text-neutral-900/60">Pulse &quot;Resumen IA&quot; para generar o ver síntesis.</p>
                )
              ) : null}
              {tab === "pre" && detail ? (
                <div className="space-y-2">
                  <p>
                    <span className="font-semibold">Clasificación:</span> {detail.estado_clasificacion}
                  </p>
                  <p>
                    <span className="font-semibold">Confianza IA:</span>{" "}
                    {detail.confianza_clasificacion != null
                      ? `${Math.round(Number(detail.confianza_clasificacion) * 100)}%`
                      : "—"}
                  </p>
                  <p className="text-xs text-neutral-900/70">{detail.razon_rechazo || "Sin motivo de rechazo."}</p>
                </div>
              ) : null}
              {tab === "original" && detail ? (
                <div className="space-y-3">
                  <pre className="whitespace-pre-wrap text-xs text-neutral-900">{detail.contenido}</pre>
                  <div className="rounded-lg border border-neutral-200 bg-white p-2">{actionButtons}</div>
                </div>
              ) : null}
            </div>
            <div className="mt-4 space-y-2 border-t border-neutral-100 pt-4">
              <textarea
                className="w-full rounded-lg border border-neutral-200 p-2 text-xs"
                rows={3}
                placeholder="Nota para rechazo/corrección (opcional)"
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
              {actionButtons}
            </div>
          </>
        )}
      </aside>
    </div>
  );
}
