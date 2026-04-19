import { NextResponse } from "next/server";

import { systemPrompt, userPrompt, type AssistMode, type PqrsDetailPayload } from "@/lib/assistOllama";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function apiBackendUrl(): string {
  return (
    process.env.API_URL?.replace(/\/$/, "") ||
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
    "http://127.0.0.1:8080"
  );
}

function ollamaUrl(): string {
  return process.env.OLLAMA_URL?.replace(/\/$/, "") || "http://127.0.0.1:11434";
}

function ollamaModel(): string {
  return process.env.OLLAMA_MODEL || "llama3.2:3b";
}

const MODES: AssistMode[] = ["rechazo", "gestion", "riesgo", "clasificacion"];

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
  const detailRes = await fetch(`${base}/api/v1/pqrs/${encodeURIComponent(pqrsId)}`, {
    cache: "no-store"
  });

  if (detailRes.status === 404) {
    return NextResponse.json({ error: "PQRS no encontrada en la API" }, { status: 404 });
  }
  if (!detailRes.ok) {
    const t = await detailRes.text();
    return NextResponse.json(
      { error: `API PQRS ${detailRes.status}: ${t.slice(0, 300)}` },
      { status: 502 }
    );
  }

  const pqrs = (await detailRes.json()) as PqrsDetailPayload;

  const ollamaBase = ollamaUrl();
  const model = ollamaModel();
  const chatUrl = `${ollamaBase}/api/chat`;

  const ollamaRes = await fetch(chatUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify({
      model,
      stream: false,
      messages: [
        { role: "system", content: systemPrompt(mode) },
        { role: "user", content: userPrompt(mode, pqrs) }
      ]
    })
  });

  if (!ollamaRes.ok) {
    const t = await ollamaRes.text();
    return NextResponse.json(
      {
        error: `Ollama ${ollamaRes.status} en ${chatUrl}: ${t.slice(0, 400)}`,
        hint: "¿Docker arriba y modelo descargado? docker compose exec ollama ollama pull llama3.2:3b"
      },
      { status: 502 }
    );
  }

  let parsed: { message?: { content?: string } };
  try {
    parsed = (await ollamaRes.json()) as { message?: { content?: string } };
  } catch {
    return NextResponse.json({ error: "Respuesta Ollama no es JSON" }, { status: 502 });
  }

  const content = parsed.message?.content?.trim();
  if (!content) {
    return NextResponse.json({ error: "Ollama no devolvió texto" }, { status: 502 });
  }

  return NextResponse.json({ respuesta: content, modelo: model });
}
