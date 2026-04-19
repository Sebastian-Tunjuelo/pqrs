/**
 * Proxy transparente hacia la API Rust.
 * El browser llama a /api/proxy/api/v1/... y este handler lo reenvía
 * a NEXT_PUBLIC_API_URL con el header ngrok-skip-browser-warning.
 */
import { NextRequest, NextResponse } from "next/server";

function backendUrl(): string {
  return (
    process.env.API_URL?.replace(/\/$/, "") ||
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
    "http://127.0.0.1:8080"
  );
}

async function handler(req: NextRequest, { params }: { params: { path: string[] } }) {
  const path = (params.path ?? []).join("/");
  const search = req.nextUrl.search ?? "";
  const targetUrl = `${backendUrl()}/${path}${search}`;

  // Solo pasar headers necesarios — no forzar Content-Type en GETs
  const forwardHeaders: Record<string, string> = {
    "ngrok-skip-browser-warning": "true",
  };

  const contentType = req.headers.get("content-type");
  if (contentType) forwardHeaders["content-type"] = contentType;

  const auth = req.headers.get("authorization");
  if (auth) forwardHeaders["authorization"] = auth;

  const init: RequestInit = {
    method: req.method,
    headers: forwardHeaders,
    cache: "no-store",
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    const body = await req.text();
    if (body) init.body = body;
  }

  try {
    const res = await fetch(targetUrl, init);

    // Si ngrok devuelve HTML (página de advertencia), reportar error claro
    const ct = res.headers.get("content-type") ?? "";
    if (ct.includes("text/html")) {
      return NextResponse.json(
        { error: "ngrok no disponible — reinicia el túnel con scripts/redeploy.ps1" },
        { status: 503 }
      );
    }

    const body = await res.arrayBuffer();
    const responseHeaders: Record<string, string> = {
      "content-type": ct || "application/json",
    };
    const totalCount = res.headers.get("x-total-count");
    if (totalCount) responseHeaders["x-total-count"] = totalCount;

    return new NextResponse(body, {
      status: res.status,
      headers: responseHeaders,
    });
  } catch (e) {
    return NextResponse.json(
      { error: `Proxy error: ${e instanceof Error ? e.message : String(e)}` },
      { status: 502 }
    );
  }
}

export const GET = handler;
export const POST = handler;
export const PATCH = handler;
export const PUT = handler;
export const DELETE = handler;
