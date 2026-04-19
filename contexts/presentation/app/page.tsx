import Link from "next/link";

const cards = [
  {
    href: "/historial",
    title: "Historial",
    desc: "Consulta con filtros, tabla y exportación a CSV."
  },
  {
    href: "/secretarias",
    title: "Secretarías",
    desc: "Dependencias y PQRS asociadas por código de secretaría."
  },
  {
    href: "/gestion",
    title: "Gestión",
    desc: "Validación humana, alertas y colas operativas."
  },
  {
    href: "/dashboard",
    title: "Dashboard",
    desc: "Indicadores, riesgo y mapa por territorio."
  },
  {
    href: "/asistente",
    title: "Asistente",
    desc: "Apoyo a clasificación, riesgo, rechazo y borradores de mensaje."
  }
] as const;

export default function HomePage() {
  return (
    <main>
      <section className="mb-10 rounded-2xl bg-gradient-to-br from-primary to-primary-muted px-6 py-10 text-white shadow-lg">
        <p className="text-xs font-semibold uppercase tracking-wider text-white/80">Atención ciudadana</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight">PQRS Medellín</h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-white/90">
          Seguimiento municipal alineado a la{" "}
          <span className="font-semibold">Ley 1755 de 2015</span>: peticiones, quejas, reclamos,
          sugerencias y denuncias. Acceda a los módulos del panel desde las tarjetas siguientes.
        </p>
      </section>
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
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
