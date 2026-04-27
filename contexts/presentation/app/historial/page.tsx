import { HistorialView } from "@/components/HistorialView";

export const dynamic = "force-dynamic";

export default function HistorialPage() {
  return (
    <main className="space-y-6">
      <section className="rounded-2xl border border-[#1A4B8C]/20 bg-gradient-to-r from-[#1A4B8C] to-[#0077C8] px-6 py-6 text-white shadow-lg">
        <p className="text-xs font-semibold uppercase tracking-wide text-white/80">Módulo operativo</p>
        <h1 className="mt-1 text-2xl font-bold">Historial</h1>
        <p className="mt-1 text-sm text-white/90">
          Consulta de PQRS clasificadas con filtros, estado de gestión y detalle de trazabilidad.
        </p>
      </section>
      <HistorialView />
    </main>
  );
}
