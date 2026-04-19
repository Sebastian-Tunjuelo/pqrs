"""Resolución de rutas del monorepo."""

from __future__ import annotations

from pathlib import Path


def find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "glosarios" / "riesgo_poblacional.yaml").is_file():
            return parent
    msg = "No se encontró la raíz del repo (falta glosarios/riesgo_poblacional.yaml)"
    raise FileNotFoundError(msg)


def glosarios_dir() -> Path:
    return find_repo_root() / "glosarios"


def prioritizer_prompt_path() -> Path:
    return find_repo_root() / "orchestration" / "prompts" / "prioritizer.md"
