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

/** Prioridad para desempate: peor estado operativo primero. */
function categoriaDominante(e: EstadoComuna): "vencida" | "pendiente" | "tramite" | "respondida" | "sin_datos" {
  const { pendientes, en_tramite, respondidas, vencidas } = e;
  const orden: Array<["vencida" | "pendiente" | "tramite" | "respondida", number]> = [
    ["vencida", vencidas],
    ["pendiente", pendientes],
    ["tramite", en_tramite],
    ["respondida", respondidas]
  ];
  let mejor: (typeof orden)[0][0] | "sin_datos" = "sin_datos";
  let nMax = -1;
  for (const [cat, n] of orden) {
    if (n > nMax) {
      nMax = n;
      mejor = cat;
    }
  }
  if (nMax <= 0) return "sin_datos";
  return mejor;
}

/** Color por estado de gestión dominante; intensidad según volumen vs máximo en el mapa. */
function colorPorEstado(
  categoria: ReturnType<typeof categoriaDominante>,
  n: number,
  maxN: number
): string {
  if (categoria === "sin_datos" || maxN <= 0 || n <= 0) return "#e2e8f0";
  const t = Math.min(1, n / maxN);
  const l = 88 - t * 42;
  switch (categoria) {
    case "vencida":
      return `hsl(0 72% ${l}%)`;
    case "pendiente":
      return `hsl(214 78% ${l}%)`;
    case "tramite":
      return `hsl(38 92% ${Math.max(38, l - 6)}%)`;
    case "respondida":
      return `hsl(152 55% ${l}%)`;
    default:
      return "#e2e8f0";
  }
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
      const cat = categoriaDominante(est);
      return {
        fillColor: colorPorEstado(cat, n, maxCount),
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
      const cat = categoriaDominante(est);
      const catLabel =
        cat === "sin_datos"
          ? "Sin PQRS"
          : cat === "vencida"
            ? "Predomina: vencidas"
            : cat === "pendiente"
              ? "Predomina: pendientes"
              : cat === "tramite"
                ? "Predomina: en trámite"
                : "Predomina: respondidas";
      layer.bindPopup(
        `<strong>${name}</strong><br/>Código: ${code}<br/>PQRS: <b>${n}</b><br/><small>${catLabel}<br/>` +
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
          Color según el estado de gestión predominante; intensidad según cantidad de PQRS en la comuna.
        </p>
        <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-600">
          <li className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: "hsl(0 72% 55%)" }} />
            Vencidas
          </li>
          <li className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: "hsl(214 78% 55%)" }} />
            Pendientes
          </li>
          <li className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: "hsl(38 92% 52%)" }} />
            En trámite
          </li>
          <li className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: "hsl(152 55% 50%)" }} />
            Respondidas
          </li>
          <li className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-sm bg-slate-200" />
            Sin PQRS
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
