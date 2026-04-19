import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { Inter } from "next/font/google";

import AppHeader from "@/components/AppHeader";
import { AppNav } from "@/components/AppNav";

import "./globals.css";

const mobileLinks = [
  ["/gestion", "Gestión"],
  ["/historial", "Historial"],
  ["/secretarias", "Secretarías"],
  ["/dashboard", "Dashboard"],
  ["/asistente", "Asistente"]
] as const;

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
export const metadata: Metadata = {
  title: "PQRS Medellín",
  description: "Historial, gestión, dashboard y asistente — Secretaría de Desarrollo Económico"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es" className={inter.variable}>
      <body className={`${inter.className} min-h-screen bg-neutral-50`}>
        <div className="bg-primary px-3 py-1.5 text-center text-[11px] font-medium text-white md:text-left">
          <a
            href="#contenido-principal"
            className="underline decoration-white/70 underline-offset-2 outline-none ring-offset-primary focus-visible:ring-2 focus-visible:ring-white"
          >
            Saltar al contenido
          </a>
          <span className="mx-2 hidden text-white/50 sm:inline" aria-hidden>
            ·
          </span>
          <span className="hidden sm:inline">Versión demo — Ley 1755 de 2015 (PQRS)</span>
        </div>
        <header className="border-b border-neutral-100 bg-white px-3 py-2 md:hidden">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <Link href="/" className="text-sm font-bold text-primary">
              PQRS Medellín
            </Link>
            <nav className="flex flex-wrap gap-2 text-xs font-medium">
              {mobileLinks.map(([href, label]) => (
                <Link key={href} href={href} className="text-neutral-700 hover:text-primary">
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
            <footer className="border-t border-neutral-100 bg-white py-3 text-center text-xs text-neutral-900/60">
              Alcaldía de Medellín — PQRS (demo técnico Ley 1755)
            </footer>
          </div>
        </div>
      </body>
    </html>
  );
}
