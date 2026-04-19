"""Raw PQRS entity from upstream sources."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DataSource(str, Enum):
    MEDATA_API = "medata_api"
    MEDATA_SCRAPE = "medata_scrape"


class RawPqrs(BaseModel):
    id_externo: str | None = None
    contenido: str = Field(min_length=1)
    fecha_radicado: datetime
    source: DataSource
    metadata: dict[str, object] = Field(default_factory=dict)
