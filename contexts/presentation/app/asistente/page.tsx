import { AsistentePanel } from "@/components/AsistentePanel";

type Props = { searchParams?: { tab?: string } };

export default function AsistentePage({ searchParams }: Props) {
  const initialTab = searchParams?.tab === "gestion" ? "gestion" : "rechazo";
  return (
    <main className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Asistente Ollama</h1>
        <p className="mt-1 text-sm text-slate-600">
          Seleccione una PQRS y consulte al modelo local (sin enviar datos a la nube si Ollama corre en su máquina).
        </p>
      </div>
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <AsistentePanel initialTab={initialTab} />
      </section>
    </main>
  );
}
