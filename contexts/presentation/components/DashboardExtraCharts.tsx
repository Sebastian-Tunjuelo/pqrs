"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";

import { tipoConSignificado } from "@/lib/tipoPqrs";
import type { MetricasDashboard } from "@/lib/types";

const Plot = dynamic(() => import("react-plotly.js"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[320px] items-center justify-center rounded-xl border border-neutral-100 bg-white text-sm text-neutral-500">
      Cargando gráfico…
    </div>
  )
});

const PRIMARY = "#00693E";
const ACCENT = "#F5A800";
const MUTED = "#94a3b8";

type Props = { metricas: MetricasDashboard };

export function DashboardExtraCharts({ metricas }: Props) {
  const tipoEntries = useMemo(() => {
    const porTipo = metricas.por_tipo ?? {};
    return Object.entries(porTipo).sort(([a], [b]) => a.localeCompare(b));
  }, [metricas.por_tipo]);
  const txLabels = tipoEntries.map(([k]) => tipoConSignificado(k));
  const ty = tipoEntries.map(([, v]) => Number(v));

  const tend = Array.isArray(metricas.tendencia_semanal) ? metricas.tendencia_semanal : [];
  const lx = tend.map((t) => t.semana);
  const ly = tend.map((t) => t.total);

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="rounded-card border border-neutral-100 bg-white p-4 shadow-card lg:col-span-2">
        <h2 className="mb-2 text-base font-semibold text-neutral-900">PQRS por tipo (volumen)</h2>
        <Plot
          data={[
            {
              type: "bar",
              x: txLabels,
              y: ty,
              marker: { color: PRIMARY }
            }
          ]}
          layout={{
            autosize: true,
            margin: { t: 16, r: 12, b: 56, l: 48 },
            paper_bgcolor: "transparent",
            plot_bgcolor: "#F4F4F4",
            yaxis: { title: "Cantidad", gridcolor: "#e5e5e5" },
            xaxis: { title: "Tipo PQRS", tickangle: 0 },
            font: { family: "Inter, system-ui, sans-serif", size: 11, color: "#1A1A1A" }
          }}
          style={{ width: "100%", height: 320 }}
          useResizeHandler
          config={{ displayModeBar: false, responsive: true }}
        />
      </div>
      <div className="rounded-card border border-neutral-100 bg-white p-4 shadow-card">
        <h2 className="mb-2 text-base font-semibold text-neutral-900">Distribución por tipo</h2>
        <Plot
          data={[
            {
              type: "pie",
              labels: txLabels,
              values: ty,
              hole: 0.45,
              marker: { colors: [PRIMARY, ACCENT, "#D32F2F", "#388E3C", MUTED, "#1A1A1A"] }
            }
          ]}
          layout={{
            autosize: true,
            margin: { t: 8, r: 8, b: 8, l: 8 },
            paper_bgcolor: "transparent",
            showlegend: true,
            legend: { orientation: "h" },
            font: { family: "Inter, system-ui, sans-serif", size: 11 }
          }}
          style={{ width: "100%", height: 320 }}
          useResizeHandler
          config={{ displayModeBar: false, responsive: true }}
        />
      </div>
      <div className="rounded-card border border-neutral-100 bg-white p-4 shadow-card lg:col-span-3">
        <h2 className="mb-2 text-base font-semibold text-neutral-900">Tendencia semanal (últimas 8 semanas)</h2>
        {lx.length === 0 ? (
          <p className="text-sm text-neutral-500">Sin datos de tendencia.</p>
        ) : (
          <Plot
            data={[
              {
                type: "scatter",
                mode: "lines+markers",
                x: lx,
                y: ly,
                line: { color: PRIMARY, width: 3 },
                marker: { color: ACCENT, size: 8 }
              }
            ]}
            layout={{
              autosize: true,
              margin: { t: 16, r: 16, b: 72, l: 56 },
              paper_bgcolor: "transparent",
              plot_bgcolor: "#F4F4F4",
              xaxis: { title: "Semana (inicio)", tickangle: -30, automargin: true },
              yaxis: { title: "PQRS radicadas", gridcolor: "#e5e5e5" },
              font: { family: "Inter, system-ui, sans-serif", size: 11 }
            }}
            style={{ width: "100%", height: 300 }}
            useResizeHandler
            config={{ displayModeBar: false, responsive: true }}
          />
        )}
      </div>
    </div>
  );
}
