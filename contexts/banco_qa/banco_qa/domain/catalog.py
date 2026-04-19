"""Modelo del catálogo YAML."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

# Códigos alineados con `data/seed/seed_dim_secretaria.sql` / dim_secretaria.
CODIGOS_SECRETARIA = frozenset(
    {
        "SDE",
        "SED",
        "SSA",
        "SIF",
        "SGC",
        "SMA",
        "SMO",
        "SIS",
        "SMU",
        "SJU",
        "SCU",
        "SGO",
        "SHA",
        "SCO",
        "SID",
        "SGH",
        "SEV",
        "SGE",
        "SNR",
        "STU",
        "DAP",
        "DAGRD",
        "DAS",
        "SAG",
        "SPF",
        "SEJ",
    }
)


class QaEntry(BaseModel):
    pregunta: str = Field(min_length=3, max_length=8000)
    respuesta: str = Field(min_length=3, max_length=32000)
    secretaria_codigo: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("pregunta", "respuesta")
    @classmethod
    def strip_text(cls, v: str) -> str:
        t = v.strip()
        if len(t) < 3:
            raise ValueError("texto demasiado corto")
        return t

    @field_validator("secretaria_codigo")
    @classmethod
    def upper_codigo(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        c = v.strip().upper()
        if c not in CODIGOS_SECRETARIA:
            raise ValueError(f"secretaria_codigo desconocido: {c}")
        return c

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, v: list[str]) -> list[str]:
        out: list[str] = []
        for t in v:
            s = t.strip()
            if s:
                out.append(s)
        return out


class QaCatalogFile(BaseModel):
    version: int = 1
    entries: list[QaEntry] = Field(default_factory=list)
