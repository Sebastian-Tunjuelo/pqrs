import type { MetricasDashboard } from "@/lib/types";

export function MetricCards({ data }: { data: MetricasDashboard }) {
  const cards = [
    { label: "Total PQRS", value: data.total_pqrs, tone: "bg-slate-800 text-white" },
    { label: "Pendientes", value: data.pendientes_gestion, tone: "bg-amber-500 text-white" },
    { label: "En trámite", value: data.en_tramite, tone: "bg-brand-600 text-white" },
    { label: "Respondidas", value: data.respondidas, tone: "bg-emerald-600 text-white" },
    { label: "Vencidas", value: data.vencidas, tone: "bg-rose-600 text-white" }
  ] as const;

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
      {cards.map((c) => (
        <div
          key={c.label}
          className={`rounded-xl px-4 py-4 shadow-sm ${c.tone}`}
        >
          <p className="text-xs font-medium uppercase tracking-wide opacity-90">{c.label}</p>
          <p className="mt-1 text-2xl font-bold tabular-nums">{c.value}</p>
        </div>
      ))}
    </div>
  );
}
