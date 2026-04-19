import Link from "next/link";

const links = [
  { href: "/historial", label: "Historial" },
  { href: "/gestion", label: "Gestión" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/banco-qa", label: "Banco Q&A" },
  { href: "/asistente", label: "Asistente" }
] as const;

export function AppNav() {
  return (
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <Link href="/" className="text-lg font-semibold text-brand-700">
          PQRS Medellín
        </Link>
        <nav className="flex flex-wrap gap-1 text-sm font-medium">
          {links.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className="rounded-md px-3 py-2 text-slate-600 transition hover:bg-brand-50 hover:text-brand-700"
            >
              {label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
