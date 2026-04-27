import type { MetricasDashboard } from "@/lib/types";

export function MetricCards({ data }: { data: MetricasDashboard }) {
  const cards = [
    { label: "Total PQRS", value: data.total_pqrs, tone: "bg-gradient-to-br from-[#1A4B8C] to-[#0077C8] text-white" },
    {
      label: "Pendientes",
      value: data.pendientes ?? data.pendientes_gestion,
      tone: "bg-gradient-to-br from-[#FF8C00] to-[#F57C00] text-white",
    },
    { label: "En trámite", value: data.en_tramite, tone: "bg-gradient-to-br from-[#0077C8] to-[#00A8E8] text-white" },
    { label: "Respondidas", value: data.respondidas, tone: "bg-gradient-to-br from-[#388E3C] to-[#00693E] text-white" },
    { label: "Vencidas", value: data.vencidas, tone: "bg-gradient-to-br from-[#D32F2F] to-[#9A0007] text-white" }
  ] as const;

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
      {cards.map((c) => (
        <div
          key={c.label}
          className={`rounded-xl px-4 py-4 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md ${c.tone}`}
        >
          <p className="text-xs font-medium uppercase tracking-wide opacity-90">{c.label}</p>
          <p className="mt-1 text-2xl font-bold tabular-nums">{c.value}</p>
        </div>
      ))}
    </div>
  );
}
