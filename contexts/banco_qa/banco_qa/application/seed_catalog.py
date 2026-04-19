"""Caso de uso: cargar catálogo YAML y persistir en Postgres."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from banco_qa.domain.catalog import QaCatalogFile
from banco_qa.infrastructure.postgres_writer import PostgresBancoQaWriter


class SeedBancoQaCatalog:
    def execute(self, yaml_path: Path, database_url: str) -> int:
        raw = yaml_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            raise ValueError("YAML raíz debe ser un objeto")
        try:
            catalog = QaCatalogFile.model_validate(data)
        except ValidationError as e:
            raise ValueError(f"catálogo inválido: {e}") from e
        if not catalog.entries:
            raise ValueError("el catálogo no tiene entradas; se aborta para no vaciar banco_qa sin datos.")
        writer = PostgresBancoQaWriter(database_url)
        return writer.replace_all(catalog.entries)
