import { BancoQaSearch } from "@/components/BancoQaSearch";
import { apiGetServer } from "@/lib/api";
import type { BancoQaRow } from "@/lib/types";

export default async function BancoQaPage() {
  let rows: BancoQaRow[];
  try {
    rows = await apiGetServer<BancoQaRow[]>("/api/v1/banco-qa");
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Error desconocido";
    return (
      <main>
        <h1 className="mb-2 text-2xl font-bold text-slate-900">Banco Q&A</h1>
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
          <p className="font-medium">No se pudo cargar la API</p>
          <p className="mt-1">{msg}</p>
        </div>
      </main>
    );
  }

  return (
    <main className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Banco Q&A</h1>
        <p className="mt-1 text-sm text-slate-600">
          Respuestas frecuentes por secretaría. Búsqueda vía{" "}
          <code className="rounded bg-slate-100 px-1 text-xs">POST /api/v1/banco-qa/buscar</code>.
        </p>
      </div>
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-base font-semibold text-slate-800">Buscar</h2>
        <BancoQaSearch />
      </section>
      <section>
        <h2 className="mb-3 text-base font-semibold text-slate-800">Catálogo ({rows.length})</h2>
        <ul className="space-y-3">
          {rows.length === 0 && (
            <li className="rounded-lg border border-amber-100 bg-amber-50/80 p-4 text-sm text-amber-950">
              <p className="font-medium">La tabla está vacía</p>
              <p className="mt-1 text-amber-900/90">
                Cargue el semillero SQL (recomendado con el resto de seeds) o use el CLI Python desde la raíz del repo:
              </p>
              <pre className="mt-2 overflow-x-auto rounded-md bg-white/80 p-2 text-xs text-slate-800">
                {`REM En CMD.exe (símbolo del sistema):
scripts\\seed_banco_qa.cmd

REM En PowerShell:
Get-Content .\\data\\seed\\seed_banco_qa.sql -Raw | docker compose exec -T postgres psql -U pqrs -d pqrs -v ON_ERROR_STOP=1

REM Alternativa Python:
# pip install -e .\\contexts\\banco_qa
# py -3.12 -m banco_qa.cli seed --file glosarios\\banco_qa.yaml`}
              </pre>
            </li>
          )}
          {rows.map((r) => (
            <li key={r.id} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-semibold text-slate-800">{r.pregunta}</p>
              <p className="mt-2 text-sm text-slate-600">{r.respuesta}</p>
              <p className="mt-2 text-xs text-slate-400">
                {r.secretaria_codigo ? `Secretaría: ${r.secretaria_codigo}` : "General"}
                {r.tags?.length ? ` · Tags: ${r.tags.join(", ")}` : ""}
              </p>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
