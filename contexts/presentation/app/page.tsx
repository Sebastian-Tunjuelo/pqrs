import Link from "next/link";

type ModuleCard = {
  href: string;
  title: string;
  description: string;
  accentClass: string;
  topBorderClass: string;
  iconBgClass: string;
  icon: JSX.Element;
};

const modules: ModuleCard[] = [
  {
    href: "/historial",
    title: "Historial de PQRS",
    description:
      "Consulta todas las PQRS clasificadas por la IA. Filtra por estado, tipo y secretaría.",
    accentClass: "text-[#1D4ED8]",
    topBorderClass: "border-t-[#1D4ED8]",
    iconBgClass: "bg-[#DBEAFE]",
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor">
        <path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    )
  },
  {
    href: "/gestion",
    title: "Gestión y Validación",
    description:
      "Revisa la cola de priorización, valida clasificaciones y gestiona respuestas pendientes.",
    accentClass: "text-[#2563EB]",
    topBorderClass: "border-t-[#2563EB]",
    iconBgClass: "bg-[#E0ECFF]",
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor">
        <path d="m5 13 4 4L19 7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    )
  },
  {
    href: "/dashboard",
    title: "Dashboard Analítico",
    description:
      "Métricas de riesgo, distribución por comunas en mapa interactivo y tendencias temporales.",
    accentClass: "text-[#0EA5E9]",
    topBorderClass: "border-t-[#0EA5E9]",
    iconBgClass: "bg-[#E0F2FE]",
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor">
        <path d="M4 20h16M7 16v-5M12 16V8M17 16v-3" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    )
  },
  {
    href: "/asistente",
    title: "Asistente IA",
    description:
      "Consulta al asistente Ollama para análisis de PQRS, resúmenes y clasificación manual.",
    accentClass: "text-[#3B82F6]",
    topBorderClass: "border-t-[#3B82F6]",
    iconBgClass: "bg-[#EAF3FF]",
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor">
        <path d="M8 10h8M8 14h8M9 5h6l2 3v8l-2 3H9l-2-3V8l2-3ZM9 19v2M15 19v2" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    )
  }
];

export default function HomePage() {
  return (
    <main className="mx-auto w-full max-w-7xl space-y-10 overflow-x-hidden px-4 pb-8 sm:px-6 lg:px-8">
      <section className="rounded-3xl bg-gradient-to-br from-[#1A4B8C] to-[#0077C8] px-6 py-12 text-center shadow-[0_20px_45px_-25px_rgba(26,75,140,0.65)] md:py-14">
        <h1 className="text-3xl font-bold tracking-tight text-white md:text-4xl">Panel de Gestión PQRSD</h1>
        <p className="mx-auto mt-3 max-w-3xl text-sm leading-relaxed text-white/90 md:text-base">
          Medellín — Sistema de seguimiento de Peticiones, Quejas, Reclamos, Sugerencias y Denuncias
        </p>
        <p className="mx-auto mt-6 max-w-2xl text-sm leading-relaxed text-white/90 md:text-base">
          Este portal organiza y facilita la atencion de solicitudes ciudadanas, ayudando a dar
          seguimiento, responder a tiempo y mejorar el servicio a la comunidad.
        </p>
      </section>

      <section>
        <h2 className="text-center text-2xl font-bold tracking-tight text-neutral-900">Módulos del sistema</h2>
        <p className="mt-1 text-center text-sm text-neutral-500">Accede a cada area de gestion</p>
        <div className="mx-auto mt-5 grid w-full max-w-5xl grid-cols-1 gap-5 md:grid-cols-2">
          {modules.map((module) => (
            <Link
              key={module.href}
              href={module.href}
              className={`group flex min-h-11 h-full flex-col rounded-2xl border border-[#DBEAFE] border-t-[5px] ${module.topBorderClass} bg-white/95 p-7 shadow-[0_16px_36px_-24px_rgba(29,78,216,0.45)] backdrop-blur transition-all duration-300 hover:-translate-y-0.5 hover:border-[#93C5FD] hover:shadow-[0_22px_44px_-22px_rgba(29,78,216,0.5)]`}
            >
              <div className="flex items-start justify-between gap-4">
                <span className={`inline-flex h-11 w-11 items-center justify-center rounded-full ${module.iconBgClass} ${module.accentClass}`}>
                  {module.icon}
                </span>
                <span className={`translate-x-0 text-xl font-semibold ${module.accentClass} transition-transform duration-200 group-hover:translate-x-1`} aria-hidden="true">
                  →
                </span>
              </div>
              <h3 className="mt-5 text-xl font-semibold tracking-tight text-neutral-900">{module.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-neutral-600">{module.description}</p>
            </Link>
          ))}
        </div>
      </section>

      <section className="rounded-xl bg-neutral-50 p-6">
        <h2 className="text-2xl font-semibold text-neutral-900">Marco legal</h2>
        <div className="mt-4 grid grid-cols-1 gap-6 md:grid-cols-2">
          <article>
            <h3 className="text-lg font-semibold text-neutral-900">Ley 1755 de 2015</h3>
            <p className="mt-2 text-sm leading-relaxed text-neutral-600">
              Regula el derecho fundamental de petición en Colombia. Establece plazos de respuesta obligatorios para entidades públicas.
            </p>
            <ul className="mt-3 space-y-1.5 text-sm text-neutral-700">
              <li>Peticiones de interés general: 15 días hábiles</li>
              <li>Quejas y reclamos: 15 días hábiles</li>
              <li>Consultas a autoridades: 30 días hábiles</li>
              <li>Información entre entidades: 10 días hábiles</li>
            </ul>
          </article>
          <article>
            <h3 className="text-lg font-semibold text-neutral-900">Artículo 23 — Constitución</h3>
            <p className="mt-2 text-sm leading-relaxed text-neutral-600">
              Toda persona tiene derecho a presentar peticiones respetuosas a las autoridades por motivos de interés general o particular.
            </p>
            <p className="mt-3 rounded-lg bg-white p-4 text-sm text-neutral-700 shadow-sm">
              Este derecho es gratuito, no requiere abogado y puede ser ejercido por cualquier persona.
            </p>
          </article>
        </div>
      </section>

      <section className="rounded-xl bg-[#1A4B8C] px-6 py-6 text-center text-white">
        <p className="text-base font-semibold">Sistema PQRSD — Alcaldía de Medellín</p>
        <p className="mt-1 text-sm text-white/90">Demo técnico — Ley 1755 de 2015 — API Rust + Postgres + Ollama</p>
      </section>
    </main>
  );
}
