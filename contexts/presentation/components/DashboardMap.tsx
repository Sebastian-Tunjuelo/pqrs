"use client";

import type { Feature, FeatureCollection, Geometry } from "geojson";
import type { PathOptions } from "leaflet";
import L from "leaflet";
import { useEffect, useMemo, useState } from "react";
import { GeoJSON, MapContainer, TileLayer } from "react-leaflet";

import "leaflet/dist/leaflet.css";

export type EstadoComuna = {
  pendientes: number;
  en_tramite: number;
  respondidas: number;
  vencidas: number;
};

/** Escala azul por volumen (cuando hay PQRS pero sin buckets de gestión conocidos). */
function colorSoloVolumen(n: number, maxN: number): string {
  if (maxN <= 0 || n <= 0) return "#e2e8f0";
  const t = Math.min(1, n / maxN);
  const h = 210;
  const s = 70;
  const l = 92 - t * 38;
  return `hsl(${h} ${s}% ${l}%)`;
}

/**
 * Color por mezcla de estados en la comuna (no solo el mayor conteo).
 * Más rojo: más vencidas / carga pendiente y trámite; más verde: más respondidas.
 */
function colorPorSaludOperativa(est: EstadoComuna, n: number, maxN: number): string {
  if (n <= 0 || maxN <= 0) return "#e2e8f0";
  const sum = est.pendientes + est.en_tramite + est.respondidas + est.vencidas;
  if (sum <= 0) return colorSoloVolumen(n, maxN);
  const tension = est.vencidas * 4 + est.pendientes * 1.15 + est.en_tramite * 1.75;
  const alivio = est.respondidas * 2.4;
  let score = (tension - alivio) / sum;
  score = Math.max(-1.15, Math.min(2.6, score));
  const norm = (score + 1.15) / 3.75;
  const hue = 118 - norm * 118;
  const t = Math.min(1, n / maxN);
  const l = 84 - t * 40;
  const s = 52 + t * 22;
  return `hsl(${hue.toFixed(0)} ${s.toFixed(0)}% ${l.toFixed(0)}%)`;
}

export default function DashboardMap({
  countsByCodigo,
  estadosByCodigo
}: {
  countsByCodigo: Record<string, number>;
  estadosByCodigo: Record<string, EstadoComuna>;
}) {
  const [fc, setFc] = useState<FeatureCollection | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/geojson/comunas", { cache: "force-cache" });
        if (!res.ok) {
          const t = await res.text();
          throw new Error(t || res.statusText);
        }
        const data = (await res.json()) as FeatureCollection;
        if (!cancelled) setFc(data);
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : "Error cargando mapa");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const maxCount = useMemo(() => {
    return Math.max(0, ...Object.values(countsByCodigo));
  }, [countsByCodigo]);

  const styleFn = useMemo(() => {
    return (feature?: Feature<Geometry, { codigo?: string }>): PathOptions => {
      const code = feature?.properties?.codigo ?? "";
      const n = countsByCodigo[code] ?? 0;
      const est = estadosByCodigo[code] ?? {
        pendientes: 0,
        en_tramite: 0,
        respondidas: 0,
        vencidas: 0
      };
      return {
        fillColor: colorPorSaludOperativa(est, n, maxCount),
        color: "#64748b",
        weight: 1,
        fillOpacity: 0.88
      };
    };
  }, [countsByCodigo, estadosByCodigo, maxCount]);

  const onEach = useMemo(() => {
    return (feature: Feature<Geometry, { codigo?: string; nombre?: string }>, layer: L.Layer) => {
      const code = feature.properties?.codigo ?? "";
      const name = feature.properties?.nombre ?? "";
      const n = countsByCodigo[code] ?? 0;
      const est = estadosByCodigo[code] ?? {
        pendientes: 0,
        en_tramite: 0,
        respondidas: 0,
        vencidas: 0
      };
      const sum = est.pendientes + est.en_tramite + est.respondidas + est.vencidas;
      const mixLabel =
        n <= 0
          ? "Sin PQRS"
          : sum <= 0
            ? "Color por volumen (gestión no clasificada en P/E/R/V)"
            : "Color = mezcla operativa (rojo tensión, verde avance)";
      layer.bindPopup(
        `<strong>${name}</strong><br/>Código: ${code}<br/>PQRS: <b>${n}</b><br/><small>${mixLabel}<br/>` +
          `Pend: ${est.pendientes} · Trámite: ${est.en_tramite} · Resp: ${est.respondidas} · Venc: ${est.vencidas}</small>`
      );
    };
  }, [countsByCodigo, estadosByCodigo]);

  if (err) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <p className="font-medium">Mapa no disponible</p>
        <p className="mt-1 text-amber-800/90">{err}</p>
      </div>
    );
  }

  if (!fc) {
    return (
      <div className="flex h-[420px] items-center justify-center rounded-xl border border-slate-200 bg-white text-sm text-slate-500">
        Cargando comunas…
      </div>
    );
  }

  const center = L.latLng(6.25, -75.56);
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-4 py-3">
        <h2 className="text-base font-semibold text-slate-800">Mapa por comuna</h2>
        <p className="text-xs text-slate-500">
          Color por <strong>mezcla</strong> de estados en la comuna (vencidas y carga abren hacia rojo; respondidas hacia
          verde). La intensidad refleja también cuántas PQRS hay en la comuna.
        </p>
        <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-600">
          <li className="flex items-center gap-1">
            <span
              className="inline-block h-2.5 w-8 rounded-sm bg-gradient-to-r from-red-500 via-amber-300 to-emerald-500"
            />
            Peor situación → mejor situación
          </li>
          <li className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-sm bg-slate-200" />
            Sin PQRS
          </li>
          <li className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: "hsl(210 70% 58%)" }} />
            Solo volumen (sin P/E/R/V en BD)
          </li>
        </ul>
      </div>
      <MapContainer center={center} zoom={12} className="z-0 h-[420px] w-full" scrollWheelZoom>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <GeoJSON data={fc} style={styleFn} onEachFeature={onEach} />
      </MapContainer>
    </div>
  );
}
