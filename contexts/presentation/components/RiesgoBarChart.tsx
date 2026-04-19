"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";

const Plot = dynamic(() => import("react-plotly.js"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[380px] items-center justify-center rounded-xl border border-slate-200 bg-white text-sm text-slate-500">
      Cargando gráfico…
    </div>
  )
});

export function RiesgoBarChart({ porNivel }: { porNivel: Record<string, number> }) {
  const { x, y } = useMemo(() => {
    const entries = Object.entries(porNivel).sort(([a], [b]) => a.localeCompare(b));
    return {
      x: entries.map(([k]) => k),
      y: entries.map(([, v]) => v)
    };
  }, [porNivel]);

  if (!x.length || y.every((v) => v === 0)) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
        Sin datos de riesgo para graficar.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-2 px-2 text-base font-semibold text-slate-800">PQRS por nivel de riesgo</h2>
      <Plot
        data={[
          {
            type: "bar",
            x,
            y,
            marker: { color: "#00693E" }
          }
        ]}
        layout={{
          autosize: true,
          margin: { t: 24, r: 16, b: 72, l: 56 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "#f8fafc",
          title: "",
          yaxis: { title: "Cantidad", gridcolor: "#e2e8f0" },
          xaxis: { title: "Nivel", tickangle: -20, automargin: true },
          font: { family: "system-ui, sans-serif", size: 12, color: "#334155" }
        }}
        style={{ width: "100%", height: 380 }}
        useResizeHandler
        config={{ displayModeBar: false, responsive: true }}
      />
    </div>
  );
}
