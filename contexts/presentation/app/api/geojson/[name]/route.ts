import { readFile } from "fs/promises";
import path from "path";
import { NextResponse } from "next/server";

const FILES: Record<string, string> = {
  comunas: "comunas_medellin.geojson",
  corregimientos: "corregimientos_medellin.geojson"
};

export async function GET(
  _request: Request,
  { params }: { params: { name: string } }
) {
  const base = FILES[params.name];
  if (!base) {
    return new NextResponse("Not found", { status: 404 });
  }
  const filePath = path.join(process.cwd(), "..", "..", "data", "geojson", base);
  try {
    const raw = await readFile(filePath, "utf-8");
    return new NextResponse(raw, {
      status: 200,
      headers: {
        "Content-Type": "application/geo+json",
        "Cache-Control": "public, max-age=3600"
      }
    });
  } catch {
    return new NextResponse(
      JSON.stringify({
        error: "GeoJSON no encontrado. Ejecuta el proyecto desde el monorepo (data/geojson)."
      }),
      { status: 404, headers: { "Content-Type": "application/json" } }
    );
  }
}
