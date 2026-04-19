import dynamic from "next/dynamic";

import { MetricCards } from "@/components/MetricCards";
import { RiesgoBarChart } from "@/components/RiesgoBarChart";
import { apiGetServer } from "@/lib/api";
import type { MetricasDashboard, TerritorioDashboard } from "@/lib/types";

const DashboardMap = dynamic(() => import("@/components/DashboardMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[420px] items-center justify-center rounded-xl border border-slate-200 bg-white text-sm text-slate-500">
      Cargando mapa…
    </div>
  )
});

export default async function DashboardPage() {
  let metricas: MetricasDashboard;
  let territorios: TerritorioDashboard[];
  try {
    [metricas, territorios] = await Promise.all([
      apiGetServer<MetricasDashboard>("/api/v1/dashboard/metricas"),
      apiGetServer<TerritorioDashboard[]>("/api/v1/dashboard/territorios")
    ]);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Error desconocido";
    return (
      <main>
        <h1 className="mb-2 text-2xl font-bold text-slate-900">Dashboard</h1>
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
          <p className="font-medium">No se pudo cargar la API</p>
          <p className="mt-1">{msg}</p>
        </div>
      </main>
    );
  }

  const countsByCodigo = Object.fromEntries(
    territorios.map((t) => [t.codigo, t.pqrs_count])
  );
  const estadosByCodigo = Object.fromEntries(
    territorios.map((t) => [
      t.codigo,
      {
        pendientes: t.pendientes ?? 0,
        en_tramite: t.en_tramite ?? 0,
        respondidas: t.respondidas ?? 0,
        vencidas: t.vencidas ?? 0
      }
    ])
  );

  return (
    <main className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-600">
          Resumen operativo y territorio (comunas Medellín + datos de Postgres).
        </p>
      </div>
      <MetricCards data={metricas} />
      <div className="grid gap-8 lg:grid-cols-2">
        <DashboardMap countsByCodigo={countsByCodigo} estadosByCodigo={estadosByCodigo} />
        <RiesgoBarChart porNivel={metricas.por_riesgo ?? metricas.por_nivel_riesgo} />
      </div>
    </main>
  );
}
