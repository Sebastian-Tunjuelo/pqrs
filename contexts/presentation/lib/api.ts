/**
 * Cliente HTTP hacia la API Rust (Axum).
 */
import type { Paginated, PqrsListItem } from "@/lib/types";

export function apiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8080";
}

function fullUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${apiBaseUrl()}${p}`;
}

/** Uso preferido en Server Components. `revalidateSeconds <= 0` fuerza datos frescos (sin caché). */
export async function apiGetServer<T>(path: string, revalidateSeconds = 30): Promise<T> {
  const init =
    revalidateSeconds <= 0
      ? { cache: "no-store" as const }
      : { next: { revalidate: revalidateSeconds } };
  const res = await fetch(fullUrl(path), init);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

/** Cliente o rutas donde no aplica caché de Next. */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(fullUrl(path), { ...init, cache: init?.cache ?? "no-store" });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

export async function apiPostJson<T>(path: string, body: unknown): Promise<T> {
  return apiFetch<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
}

/** Asistente Ollama vía ruta Next (`/api/assist/ollama`), sin depender de endpoints assist en la API Rust. */
export async function apiPostAssist<T>(body: { pqrs_id: string; mode: string }): Promise<T> {
  const res = await fetch("/api/assist/ollama", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store"
  });
  if (!res.ok) {
    const raw = await res.text();
    let msg = `Asistente ${res.status}`;
    try {
      const j = JSON.parse(raw) as { error?: string; hint?: string };
      if (j.error) msg += `: ${j.error}`;
      if (j.hint) msg += ` — ${j.hint}`;
    } catch {
      msg += `: ${raw.slice(0, 220)}`;
    }
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

/** Pagina la API Rust hasta traer todas las filas (hasta ~12k), desde el navegador. */
export async function apiFetchAllPqrsList(pathWithoutQuery: string): Promise<PqrsListItem[]> {
  const per = 200;
  let page = 1;
  let total = Number.POSITIVE_INFINITY;
  const out: PqrsListItem[] = [];
  while (out.length < total) {
    const sep = pathWithoutQuery.includes("?") ? "&" : "?";
    const url = `${pathWithoutQuery}${sep}page=${page}&per_page=${per}`;
    const data = await apiFetch<Paginated<PqrsListItem>>(url);
    if (page === 1) total = data.total;
    out.push(...data.items);
    if (data.items.length === 0) break;
    page += 1;
    if (page > 60) break;
  }
  return out;
}

/** Igual que `apiFetchAllPqrsList` pero en Server Components (`apiGetServer`, sin caché). */
export async function apiGetServerAllPqrs(
  pathWithoutQuery: string
): Promise<{ items: PqrsListItem[]; total: number }> {
  const per = 200;
  let page = 1;
  let total = 0;
  const out: PqrsListItem[] = [];
  while (true) {
    const sep = pathWithoutQuery.includes("?") ? "&" : "?";
    const data = await apiGetServer<Paginated<PqrsListItem>>(
      `${pathWithoutQuery}${sep}page=${page}&per_page=${per}`,
      0
    );
    if (page === 1) total = data.total;
    out.push(...data.items);
    if (out.length >= total || data.items.length === 0) break;
    page += 1;
    if (page > 60) break;
  }
  return { items: out, total };
}
