import { HistorialView } from "@/components/HistorialView";

export const dynamic = "force-dynamic";

export default function HistorialPage() {
  return (
    <main className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-neutral-900">Historial</h1>
      </div>
      <HistorialView />
    </main>
  );
}
