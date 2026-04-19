import { NextResponse } from "next/server";

const FILES: Record<string, string> = {
  comunas: "comunas_medellin.geojson",
  corregimientos: "corregimientos_medellin.geojson"
};

export async function GET(
  request: Request,
  { params }: { params: { name: string } }
) {
  const base = FILES[params.name];
  if (!base) {
    return new NextResponse("Not found", { status: 404 });
  }

  // En Vercel los archivos estáticos se sirven desde /public directamente.
  // Redirigimos al archivo estático para que funcione tanto local como en producción.
  const url = new URL(request.url);
  const staticUrl = `${url.protocol}//${url.host}/${base}`;

  try {
    const res = await fetch(staticUrl, { cache: "force-cache" });
    if (!res.ok) throw new Error("not found");
    const raw = await res.text();
    return new NextResponse(raw, {
      status: 200,
      headers: {
        "Content-Type": "application/geo+json",
        "Cache-Control": "public, max-age=3600"
      }
    });
  } catch {
    return new NextResponse(
      JSON.stringify({ error: "GeoJSON no disponible." }),
      { status: 404, headers: { "Content-Type": "application/json" } }
    );
  }
}
