"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const links = [
  { href: "/gestion", label: "Gestión" },
  { href: "/historial", label: "Historial" },
  { href: "/secretarias", label: "Secretarías" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/asistente", label: "Asistente" }
] as const;

export function AppNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(true);

  return (
    <aside
      className={`hidden shrink-0 border-r border-neutral-100 bg-white transition-[width] duration-200 ease-out md:block ${
        open ? "w-56" : "w-[4.5rem]"
      }`}
    >
      <div className="sticky top-0 flex h-screen flex-col gap-4 px-2 py-6">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="mx-auto flex h-9 w-9 items-center justify-center rounded-lg border border-neutral-200 text-neutral-600 hover:bg-neutral-50"
          title={open ? "Contraer menú" : "Expandir menú"}
          aria-expanded={open}
        >
          {open ? "«" : "»"}
        </button>
        <Link
          href="/"
          className={`block px-2 ${!open ? "text-center" : ""} ${pathname === "/" ? "rounded-lg border border-primary/30 bg-primary/5 py-1" : ""}`}
          aria-current={pathname === "/" ? "page" : undefined}
        >
          <p className="text-[10px] font-semibold uppercase tracking-wide text-primary">
            {open ? "Alcaldía de Medellín" : "AM"}
          </p>
          <p className="mt-1 text-lg font-bold text-neutral-900">PQRS</p>
          {open ? <p className="text-xs text-neutral-900/50">Validación + IA</p> : null}
        </Link>
        <nav className="flex flex-col gap-1 text-sm font-medium" aria-label="Navegación principal">
          {links.map(({ href, label }) => {
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                key={href}
                href={href}
                title={!open ? label : undefined}
                aria-current={active ? "page" : undefined}
                className={`rounded-lg py-2 text-neutral-700 transition hover:bg-neutral-50 hover:text-primary ${
                  open ? "px-3" : "px-0 text-center text-xs"
                } ${active ? "border-l-2 border-primary bg-primary/5 font-semibold text-primary" : ""}`}
              >
                {open ? label : label.slice(0, 2)}
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
