"""Catálogo DCAT (`data.json`) de MEData — el portal ya no expone `/api/3/action` en la ruta antigua."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import httpx

from ingestion.domain.raw_pqrs import DataSource, RawPqrs


class MedataDataJsonClient:
    """Descarga https://medata.gov.co/data.json y extrae datasets relacionados con PQRS."""

    def __init__(
        self,
        catalog_url: str = "https://medata.gov.co/data.json",
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.catalog_url = catalog_url
        self._http = http_client or httpx.AsyncClient(timeout=60.0, follow_redirects=True)

    async def fetch_raw_pqrs(self) -> list[RawPqrs]:
        resp = await self._http.get(self.catalog_url)
        resp.raise_for_status()
        payload = resp.json()
        datasets = payload.get("dataset")
        if not isinstance(datasets, list):
            return []

        out: list[RawPqrs] = []
        for ds in datasets:
            if not isinstance(ds, dict):
                continue
            blob = json.dumps(ds, ensure_ascii=False).lower()
            if "pqrs" not in blob:
                continue
            title = (ds.get("title") or "Dataset PQRS").strip()
            desc = (ds.get("description") or "").strip()
            contenido = f"{title}\n\n{desc}".strip() or title
            ident = ds.get("identifier")
            id_externo = str(ident).strip() if ident else None
            fecha = _parse_catalog_date(ds)
            dist = ds.get("distribution")
            download = None
            if isinstance(dist, list) and dist and isinstance(dist[0], dict):
                download = dist[0].get("downloadURL")

            out.append(
                RawPqrs(
                    id_externo=id_externo,
                    contenido=contenido[:8000],
                    fecha_radicado=fecha,
                    source=DataSource.MEDATA_DCAT,
                    metadata={
                        "catalog": "medata.data.json",
                        "title": title,
                        "downloadURL": download,
                        "keyword": ds.get("keyword"),
                    },
                )
            )
        return out


def _parse_catalog_date(ds: dict) -> datetime:
    for key in ("modified", "temporal", "issued"):
        val = ds.get(key)
        if not val or not isinstance(val, str):
            continue
        v = val.strip()
        if "T" in v:
            try:
                if v.endswith("Z"):
                    return datetime.fromisoformat(v.replace("Z", "+00:00"))
                return datetime.fromisoformat(v)
            except ValueError:
                continue
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d-%m-%y"):
            try:
                part = v.split("T")[0][:10]
                return datetime.strptime(part, fmt).replace(tzinfo=UTC)
            except ValueError:
                continue
    return datetime.now(UTC)
