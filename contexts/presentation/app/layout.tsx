import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { Manrope } from "next/font/google";

import AppHeader from "@/components/AppHeader";
import { AppNav } from "@/components/AppNav";

import "./globals.css";

const mobileLinks = [
  ["/gestion", "Gestión"],
  ["/historial", "Historial"],
  ["/dashboard", "Dashboard"],
  ["/asistente", "Asistente"]
] as const;

const manrope = Manrope({ subsets: ["latin"], variable: "--font-manrope" });
export const metadata: Metadata = {
  title: "PQRS Medellín",
  description: "Historial, gestión, dashboard y asistente — Secretaría de Desarrollo Económico"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es" className={manrope.variable}>
      <body className={`${manrope.className} min-h-screen bg-gradient-to-b from-[#eff6ff] via-white to-[#f4f4f4]`}>
        <div className="bg-gradient-to-r from-[#1A4B8C] to-[#0077C8] px-3 py-1.5 text-center text-[11px] font-medium text-white md:text-left">
          <a
            href="#contenido-principal"
            className="underline decoration-white/70 underline-offset-2 outline-none ring-offset-[#1A4B8C] focus-visible:ring-2 focus-visible:ring-white"
          >
            Saltar al contenido
          </a>
          <span className="mx-2 hidden text-white/50 sm:inline" aria-hidden>
            ·
          </span>
          <span className="hidden sm:inline">Versión demo — Ley 1755 de 2015 (PQRS)</span>
        </div>
        <header className="border-b border-[#1A4B8C]/10 bg-white/90 px-3 py-2 backdrop-blur md:hidden">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <Link href="/" className="text-sm font-bold text-[#1A4B8C]">
              PQRS Medellín
            </Link>
            <nav className="flex flex-wrap gap-2 text-xs font-medium">
              {mobileLinks.map(([href, label]) => (
                <Link
                  key={href}
                  href={href}
                  className="inline-flex min-h-11 items-center rounded-lg px-2 text-neutral-700 hover:bg-[#1A4B8C]/5 hover:text-[#1A4B8C]"
                >
                  {label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <div className="flex min-h-screen">
          <AppNav />
          <div className="flex min-h-0 min-w-0 flex-1 flex-col">
            <AppHeader />
            <main
              id="contenido-principal"
              tabIndex={-1}
              className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 outline-none"
            >
              {children}
            </main>
            <footer className="border-t border-[#1A4B8C]/10 bg-white/80 py-3 text-center text-xs text-neutral-900/70">
              Alcaldía de Medellín — PQRS (demo técnico Ley 1755)
            </footer>
          </div>
        </div>
      </body>
    </html>
  );
}
