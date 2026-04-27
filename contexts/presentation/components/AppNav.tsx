"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const links = [
  { href: "/gestion", label: "Gestión" },
  { href: "/historial", label: "Historial" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/asistente", label: "Asistente" }
] as const;

export function AppNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(true);

  return (
    <aside
      className={`hidden shrink-0 border-r border-[#1A4B8C]/20 bg-gradient-to-b from-[#1A4B8C] to-[#0077C8] text-white transition-[width] duration-200 ease-out md:block ${
        open ? "w-56" : "w-[4.5rem]"
      }`}
    >
      <div className="sticky top-0 flex h-screen flex-col gap-4 px-2 py-6">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="mx-auto flex h-11 w-11 items-center justify-center rounded-xl border border-white/30 bg-white/10 text-white hover:bg-white/20"
          title={open ? "Contraer menú" : "Expandir menú"}
          aria-expanded={open}
        >
          {open ? "«" : "»"}
        </button>
        <Link
          href="/"
          className={`block rounded-xl px-2 py-2 ${!open ? "text-center" : ""} ${pathname === "/" ? "border border-white/40 bg-white/15" : "border border-transparent hover:bg-white/10"}`}
          aria-current={pathname === "/" ? "page" : undefined}
        >
          <p className="text-[10px] font-semibold uppercase tracking-wide text-white/80">
            {open ? "Alcaldía de Medellín" : "AM"}
          </p>
          <p className="mt-1 text-lg font-bold text-white">PQRS</p>
          {open ? <p className="text-xs text-white/75">Validación + IA</p> : null}
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
                className={`rounded-xl py-2.5 transition ${
                  open ? "px-3" : "px-0 text-center text-xs"
                } ${
                  active
                    ? "bg-white text-[#1A4B8C] shadow-sm"
                    : "text-white/85 hover:bg-white/15 hover:text-white"
                }`}
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
