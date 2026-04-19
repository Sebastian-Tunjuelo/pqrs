from __future__ import annotations
import httpx
from datetime import date
from typing import Optional
from telegram_bot.domain.models import PqrsSnapshot
from telegram_bot.domain.exceptions import PqrsApiError


def _parse_snapshot_from_list_item(d: dict) -> PqrsSnapshot:
    fl = d.get("fecha_limite")
    return PqrsSnapshot(
        id=str(d.get("id", "")),
        tipo=d.get("tipo"),
        estado_clasificacion=d.get("estado_clasificacion", ""),
        estado_gestion=d.get("estado_gestion"),
        nivel_riesgo=d.get("nivel_riesgo"),
        secretaria_nombre=d.get("secretaria_nombre"),
        fecha_limite=date.fromisoformat(fl) if fl else None,
        summary_executive=None,
    )


def _parse_snapshot_from_detail(d: dict) -> PqrsSnapshot:
    fl = d.get("fecha_limite")
    return PqrsSnapshot(
        id=str(d.get("id", "")),
        tipo=d.get("tipo"),
        estado_clasificacion=d.get("estado_clasificacion", ""),
        estado_gestion=d.get("estado_gestion"),
        nivel_riesgo=d.get("nivel_riesgo"),
        secretaria_nombre=None,  # detail no tiene secretaria_nombre directamente
        fecha_limite=date.fromisoformat(fl) if fl else None,
        summary_executive=d.get("summary_executive"),
    )


class PqrsApiClient:
    def __init__(self, base_url: str, timeout: float = 15.0):
        self._base = base_url.rstrip("/")
        self._timeout = timeout

    async def get_pqrs(self, pqrs_id: str) -> Optional[PqrsSnapshot]:
        """Busca por UUID o por id_externo (ej: DEMO-00030)."""
        import re
        is_uuid = bool(re.fullmatch(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            pqrs_id.strip(),
        ))
        if is_uuid:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                r = await client.get(f"{self._base}/pqrs/{pqrs_id.strip()}")
                if r.status_code == 404:
                    return None
                if r.status_code != 200:
                    raise PqrsApiError(r.status_code, r.text)
                return _parse_snapshot_from_detail(r.json())
        else:
            # Buscar por id_externo en la lista
            return await self._find_by_id_externo(pqrs_id.strip().upper())

    async def _find_by_id_externo(self, id_externo: str) -> Optional[PqrsSnapshot]:
        """Recorre páginas hasta encontrar el id_externo o agotar resultados."""
        page = 1
        while True:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                r = await client.get(
                    f"{self._base}/pqrs",
                    params={"page": page, "per_page": 50},
                )
                if r.status_code != 200:
                    raise PqrsApiError(r.status_code, r.text)
            data = r.json()
            items = data.get("items", [])
            total = data.get("total", 0)
            for item in items:
                if (item.get("id_externo") or "").upper() == id_externo:
                    # Obtener detalle completo por UUID
                    uuid = item.get("id", "")
                    snap = _parse_snapshot_from_list_item(item)
                    # Intentar enriquecer con detalle
                    try:
                        async with httpx.AsyncClient(timeout=self._timeout) as client:
                            rd = await client.get(f"{self._base}/pqrs/{uuid}")
                            if rd.status_code == 200:
                                snap = _parse_snapshot_from_detail(rd.json())
                                snap.secretaria_nombre = item.get("secretaria_nombre")
                    except Exception:
                        pass
                    return snap
            fetched = page * 50
            if fetched >= total or not items:
                return None
            page += 1

    async def get_pendientes_prioridad(self, page: int = 1, per_page: int = 10) -> list[PqrsSnapshot]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(
                f"{self._base}/pqrs/pendientes/prioridad",
                params={"page": page, "per_page": per_page},
            )
            if r.status_code != 200:
                raise PqrsApiError(r.status_code, r.text)
            data = r.json()
            items = data.get("items", data) if isinstance(data, dict) else data
            return [_parse_snapshot_from_list_item(i) for i in items]

    async def get_metricas(self) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(f"{self._base}/dashboard/metricas")
            if r.status_code != 200:
                raise PqrsApiError(r.status_code, r.text)
            return r.json()

    async def get_secretarias(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(f"{self._base}/secretarias")
            if r.status_code != 200:
                raise PqrsApiError(r.status_code, r.text)
            return r.json()

    async def get_pqrs_por_secretaria(self, codigo: str, per_page: int = 10) -> Optional[list[PqrsSnapshot]]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(
                f"{self._base}/secretarias/{codigo}/pqrs",
                params={"per_page": per_page},
            )
            if r.status_code == 404:
                return None
            if r.status_code != 200:
                raise PqrsApiError(r.status_code, r.text)
            data = r.json()
            items = data.get("items", data) if isinstance(data, dict) else data
            return [_parse_snapshot_from_list_item(i) for i in items]

    async def crear_pqrs(self, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(f"{self._base}/pqrs", json=payload)
            if r.status_code not in (200, 201):
                raise PqrsApiError(r.status_code, r.text)
            return r.json()

    async def assist_mensaje_gestion(self, mensaje: str, contexto: list[dict], rol: str) -> str:
        # El endpoint /assist/ollama/mensaje-gestion requiere pqrs_id (UUID).
        # Para chat libre usamos Ollama directamente.
        raise PqrsApiError(501, "El asistente de chat libre no está disponible en la API actual")
