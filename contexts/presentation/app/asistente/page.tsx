import { AsistentePanel } from "@/components/AsistentePanel";

import type { AssistMode } from "@/lib/assistOllama";

type Props = { searchParams?: { tab?: string } };

const ALLOWED: AssistMode[] = ["gestion", "riesgo", "clasificacion", "rechazo"];

export default function AsistentePage({ searchParams }: Props) {
  const raw = searchParams?.tab;
  const initialTab: AssistMode | undefined = ALLOWED.includes(raw as AssistMode)
    ? (raw as AssistMode)
    : undefined;

  return (
    <main className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Asistente Ollama</h1>
        <p className="mt-1 text-sm text-slate-600">
          Clasificación, riesgo, rechazo y borrador para gestión — modelo local vía Next.js (no depende de rutas
          extra en la API Rust).
        </p>
      </div>
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <AsistentePanel initialTab={initialTab} />
      </section>
    </main>
  );
}
