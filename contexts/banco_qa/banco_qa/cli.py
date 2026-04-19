"""CLI: python -m banco_qa.cli seed|validate."""

from __future__ import annotations

import os
from pathlib import Path

import typer
import yaml

from banco_qa.application.seed_catalog import SeedBancoQaCatalog
from banco_qa.domain.catalog import QaCatalogFile

app = typer.Typer(help="Banco Q&A — carga de catálogo YAML hacia Postgres.")


@app.command("validate")
def validate_command(
    file: Path = typer.Argument(
        Path("glosarios/banco_qa.yaml"),
        exists=True,
        readable=True,
        help="YAML del catálogo.",
    ),
) -> None:
    """Valida sintaxis y reglas de negocio del YAML sin tocar la base de datos."""
    data = yaml.safe_load(file.read_text(encoding="utf-8"))
    catalog = QaCatalogFile.model_validate(data)
    typer.echo(f"OK: {len(catalog.entries)} entradas en {file}")


@app.command("seed")
def seed_command(
    file: Path = typer.Option(
        Path("glosarios/banco_qa.yaml"),
        "--file",
        "-f",
        exists=True,
        readable=True,
        help="YAML con el catálogo (version + entries).",
    ),
    database_url: str | None = typer.Option(
        None,
        "--database-url",
        envvar="DATABASE_URL",
        help="DSN PostgreSQL (por defecto env DATABASE_URL).",
    ),
) -> None:
    """Reemplaza todo el contenido de `banco_qa` con las entradas del archivo."""
    dsn = database_url or os.environ.get("DATABASE_URL")
    if not dsn:
        raise typer.BadParameter(
            "Indique --database-url o defina la variable de entorno DATABASE_URL."
        )
    n = SeedBancoQaCatalog().execute(file, dsn)
    typer.echo(f"Insertadas {n} filas en banco_qa (tabla vaciada antes).")


if __name__ == "__main__":
    app()
