import { HistorialView } from "@/components/HistorialView";

export const dynamic = "force-dynamic";

export default function HistorialPage() {
  return (
    <main className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-neutral-900">Historial</h1>
        <p className="mt-1 text-sm text-neutral-600">
          Filtros sobre <code className="rounded bg-neutral-100 px-1 text-xs">GET /api/v1/pqrs</code>, tabla y
          exportación CSV. Requiere API en marcha.
        </p>
      </div>
      <HistorialView />
    </main>
  );
}
