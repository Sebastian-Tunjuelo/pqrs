"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  plazoBarFillClass,
  plazoBarPct,
  plazoBarTone,
  plazoCalendarioRestante
} from "@/lib/plazoPqrs";
import type { PqrsListItem } from "@/lib/types";

type DiasBar = { label: string; pct: number; tone: "ok" | "aviso" | "critico" | "sin" };

function tipoBadge(t: string | null | undefined) {
  const v = (t || "?").toUpperCase();
  const map: Record<string, string> = {
    P: "bg-primary/10 text-primary ring-1 ring-primary/20",
    Q: "bg-accent/20 text-neutral-900 ring-1 ring-accent/40",
    R: "bg-danger/10 text-danger ring-1 ring-danger/20",
    S: "bg-success/10 text-success ring-1 ring-success/25",
    D: "bg-warning/15 text-warning ring-1 ring-warning/30"
  };
  return map[v] ?? "bg-neutral-100 text-neutral-900 ring-1 ring-neutral-200";
}

function riesgoBadge(r: string | null | undefined) {
  const v = (r || "").toUpperCase();
  const map: Record<string, string> = {
    CRITICO: "bg-danger text-white",
    ALTO: "bg-warning text-white",
    MEDIO: "bg-accent text-neutral-900",
    BAJO: "bg-success text-white"
  };
  return map[v] ?? "bg-neutral-200 text-neutral-900";
}

function diasBar(fechaLimite: string | null): DiasBar {
  const p = plazoCalendarioRestante(fechaLimite);
  if (p.variante === "sin") {
    return { label: "Sin fecha límite", pct: 0, tone: "sin" };
  }
  const pct = plazoBarPct(p.dias);
  const label =
    p.dias != null && p.dias < 0
      ? `${p.etiqueta} (cal.)`
      : p.dias != null
        ? `${p.dias} días cal. aprox.`
        : "—";
  return { label, pct, tone: plazoBarTone(p.variante) };
}

type Props = {
  item: PqrsListItem;
  lead?: string | null;
  secretariaLabel?: string | null;
  onValidate?: () => void;
  onCorrect?: () => void;
};

export function PqrsCard({ item, lead, secretariaLabel, onValidate, onCorrect }: Props) {
  const conf = item.confianza_clasificacion;
  const confPct =
    conf != null ? `${Math.round(Number(conf) * 100)}%` : "—";
  const [bar, setBar] = useState<DiasBar>(() =>
    item.fecha_limite
      ? { label: "Plazo (calculando…)", pct: 0, tone: "ok" }
      : { label: "Sin fecha límite", pct: 0, tone: "sin" }
  );
  useEffect(() => {
    setBar(diasBar(item.fecha_limite));
  }, [item.fecha_limite]);
  const ext = item.id_externo || item.id.slice(0, 8);

  return (
    <article className="rounded-xl border border-[#1A4B8C]/20 bg-white p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={`inline-flex rounded-md px-2 py-0.5 text-xs font-semibold ${tipoBadge(item.tipo)}`}
          >
            {item.tipo || "?"}
          </span>
          {item.nivel_riesgo ? (
            <span
              className={`inline-flex rounded-md px-2 py-0.5 text-xs font-semibold ${riesgoBadge(item.nivel_riesgo)}`}
            >
              {item.nivel_riesgo}
            </span>
          ) : null}
          <span className="text-xs text-neutral-900/50">{ext}</span>
        </div>
        <span className="text-xs font-medium text-primary">
          {item.validation_status?.replaceAll("_", " ") ?? ""}
        </span>
      </div>
      <p className="mt-3 line-clamp-2 text-sm font-semibold text-neutral-900">
        {lead?.trim() || item.contenido.slice(0, 140)}
        {!lead && item.contenido.length > 140 ? "…" : null}
      </p>
      <p className="mt-2 text-xs text-neutral-900/70">
        <span className="font-medium text-primary">IA sugerencia:</span>{" "}
        {secretariaLabel ?? "Secretaría —"} <span className="text-primary">— {confPct}</span>
      </p>
      <div className="mt-3">
        <div className="mb-1 flex justify-between text-xs text-neutral-900/60">
          <span>Plazo</span>
          <span
            className={
              bar.tone === "critico"
                ? "font-semibold text-danger"
                : bar.tone === "aviso"
                  ? "font-medium text-warning"
                  : bar.tone === "ok"
                    ? "font-medium text-success"
                    : ""
            }
          >
            {bar.label}
          </span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-neutral-100">
          <div
            className={`h-full rounded-full transition-all ${plazoBarFillClass(bar.tone)}`}
            style={{ width: `${bar.pct}%` }}
          />
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onValidate?.();
          }}
          className="min-h-11 rounded-lg bg-gradient-to-r from-[#1A4B8C] to-[#0077C8] px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition-all hover:shadow-md"
        >
          Validar ✓
        </button>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onCorrect?.();
          }}
          className="min-h-11 rounded-lg border border-[#1A4B8C]/20 bg-white px-3 py-1.5 text-xs font-semibold text-[#1A4B8C] transition-colors hover:bg-[#eff6ff]"
        >
          Corregir ✏
        </button>
        <Link
          href={`/pqrs/${item.id}`}
          onClick={(e) => e.stopPropagation()}
          className="inline-flex min-h-11 items-center rounded-lg px-3 py-1.5 text-xs font-semibold text-[#1A4B8C] underline-offset-2 hover:bg-[#eff6ff] hover:underline"
        >
          Ver detalle →
        </Link>
      </div>
    </article>
  );
}
