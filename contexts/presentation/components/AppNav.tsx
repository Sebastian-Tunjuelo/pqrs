import Link from "next/link";

const links = [
  { href: "/gestion", label: "Gestión" },
  { href: "/historial", label: "Historial" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/banco-qa", label: "Banco Q&A" },
  { href: "/asistente", label: "Asistente" }
] as const;

export function AppNav() {
  return (
    <aside className="hidden w-56 shrink-0 border-r border-neutral-100 bg-white md:block">
      <div className="sticky top-0 flex h-screen flex-col gap-6 px-4 py-6">
        <Link href="/" className="block">
          <p className="text-xs font-semibold uppercase tracking-wide text-primary">Alcaldía de Medellín</p>
          <p className="mt-1 text-lg font-bold text-neutral-900">PQRS</p>
          <p className="text-xs text-neutral-900/50">Validación humana + IA</p>
        </Link>
        <nav className="flex flex-col gap-1 text-sm font-medium">
          {links.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className="rounded-lg px-3 py-2 text-neutral-700 transition hover:bg-neutral-50 hover:text-primary"
            >
              {label}
            </Link>
          ))}
        </nav>
      </div>
    </aside>
  );
}
