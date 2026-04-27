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
      <section className="rounded-2xl border border-[#1A4B8C]/20 bg-gradient-to-r from-[#1A4B8C] to-[#0077C8] px-6 py-6 text-white shadow-lg">
        <p className="text-xs font-semibold uppercase tracking-wide text-white/80">Módulo IA</p>
        <h1 className="mt-1 text-2xl font-bold">Asistente IA</h1>
        <p className="mt-1 text-sm text-white/90">
          Soporte para redacción, análisis operativo y clasificación asistida con Ollama.
        </p>
      </section>
      <section className="rounded-xl border border-[#1A4B8C]/20 bg-white p-6 shadow-sm">
        <AsistentePanel initialTab={initialTab} />
      </section>
    </main>
  );
}
