import Link from "next/link";

const cards = [
  {
    href: "/historial",
    title: "Historial",
    desc: "PQRS aceptadas y rechazadas (clasificación)."
  },
  {
    href: "/gestion",
    title: "Gestión",
    desc: "Respondidas, pendientes y cola por prioridad."
  },
  {
    href: "/dashboard",
    title: "Dashboard",
    desc: "Métricas, riesgo y mapa por comuna (Leaflet + Plotly)."
  },
  {
    href: "/banco-qa",
    title: "Banco Q&A",
    desc: "Preguntas frecuentes y búsqueda semántica ligera."
  }
] as const;

export default function HomePage() {
  return (
    <main>
      <section className="mb-10 rounded-2xl bg-gradient-to-br from-brand-700 to-brand-900 px-6 py-10 text-white shadow-lg">
        <h1 className="text-3xl font-bold tracking-tight">PQRS Medellín</h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-brand-50">
          Panel de seguimiento para peticiones, quejas, reclamos y sugerencias. Los datos provienen
          de la API Rust (<code className="rounded bg-white/10 px-1">/api/v1</code>) y Postgres.
        </p>
      </section>
      <ul className="grid gap-4 sm:grid-cols-2">
        {cards.map((c) => (
          <li key={c.href}>
            <Link
              href={c.href}
              className="block h-full rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-brand-300 hover:shadow-md"
            >
              <h2 className="text-lg font-semibold text-brand-700">{c.title}</h2>
              <p className="mt-2 text-sm text-slate-600">{c.desc}</p>
              <span className="mt-3 inline-block text-sm font-medium text-brand-600">Abrir →</span>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
