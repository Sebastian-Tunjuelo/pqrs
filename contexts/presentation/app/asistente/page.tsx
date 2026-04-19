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
        <h1 className="text-2xl font-bold text-slate-900">Asistente</h1>
      </div>
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <AsistentePanel initialTab={initialTab} />
      </section>
    </main>
  );
}
