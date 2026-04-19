/**
 * Ruta del asistente Ollama.
 * Delega a la API Rust (que corre Ollama localmente) en lugar de llamar
 * Ollama directamente — así funciona desde Vercel sin exponer Ollama por ngrok.
 */
import { NextResponse } from "next/server";
import type { AssistMode } from "@/lib/assistOllama";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function apiBackendUrl(): string {
  return (
    process.env.API_URL?.replace(/\/$/, "") ||
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
    "http://127.0.0.1:8080"
  );
}

function backendHeaders(url: string): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (url.includes("ngrok")) h["ngrok-skip-browser-warning"] = "true";
  return h;
}

const MODES: AssistMode[] = ["rechazo", "gestion", "riesgo", "clasificacion"];

// Mapeo de modo → endpoint de la API Rust
function rustEndpoint(mode: AssistMode): string {
  // rechazo → explicar-rechazo
  // todos los demás → mensaje-gestion (la API Rust lo usa para redactar borradores)
  return mode === "rechazo" ? "explicar-rechazo" : "mensaje-gestion";
}

export async function POST(req: Request) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "JSON inválido" }, { status: 400 });
  }

  const b = body as { pqrs_id?: string; mode?: string };
  const pqrsId = typeof b.pqrs_id === "string" ? b.pqrs_id.trim() : "";
  const mode = (typeof b.mode === "string" ? b.mode : "rechazo") as AssistMode;

  if (!pqrsId) {
    return NextResponse.json({ error: "pqrs_id es obligatorio" }, { status: 400 });
  }
  if (!MODES.includes(mode)) {
    return NextResponse.json({ error: `mode inválido: use ${MODES.join(", ")}` }, { status: 400 });
  }

  const base = apiBackendUrl();
  const endpoint = rustEndpoint(mode);
  const url = `${base}/api/v1/assist/ollama/${endpoint}`;

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: backendHeaders(base),
      cache: "no-store",
      body: JSON.stringify({ pqrs_id: pqrsId }),
    });

    if (!res.ok) {
      const t = await res.text();
      let msg = `Ollama ${res.status}`;
      try {
        const j = JSON.parse(t) as { error?: string };
        if (j.error) msg = j.error;
      } catch { /* noop */ }
      return NextResponse.json({ error: msg }, { status: res.status >= 500 ? 502 : res.status });
    }

    const data = (await res.json()) as { respuesta: string; modelo: string };
    return NextResponse.json({ respuesta: data.respuesta, modelo: data.modelo });

  } catch (e) {
    return NextResponse.json(
      { error: `No se pudo contactar la API: ${e instanceof Error ? e.message : String(e)}` },
      { status: 502 }
    );
  }
}
