from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GEOJSON_DIR = ROOT / "data" / "geojson"
OUT_SQL = ROOT / "data" / "seed" / "seed_dim_territorio.sql"


def _rows(path: Path, tipo: str) -> list[tuple[str, str, str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows: list[tuple[str, str, str, str]] = []
    for feat in data.get("features", []):
        props = feat.get("properties", {})
        codigo = props.get("codigo")
        nombre = props.get("nombre")
        geom = feat.get("geometry")
        if not codigo or not nombre or not geom:
            continue
        geom_json = json.dumps(geom, ensure_ascii=False, separators=(",", ":"))
        rows.append((tipo, str(codigo), str(nombre), geom_json))
    return rows


def _sql_escape(value: str) -> str:
    return value.replace("'", "''")


def main() -> None:
    comunas = _rows(GEOJSON_DIR / "comunas_medellin.geojson", "COMUNA")
    correg = _rows(GEOJSON_DIR / "corregimientos_medellin.geojson", "CORREGIMIENTO")
    rows = comunas + correg

    lines = [
        "-- Generated from official Medellin GeoJSON (ArcGIS REST service)",
        "INSERT INTO dim_territorio (tipo, codigo, nombre, geometria) VALUES",
    ]
    values: list[str] = []
    for tipo, codigo, nombre, geom_json in rows:
        values.append(
            "('{tipo}', '{codigo}', '{nombre}', ST_SetSRID(ST_Multi(ST_GeomFromGeoJSON('{geom}')), 4326))".format(
                tipo=_sql_escape(tipo),
                codigo=_sql_escape(codigo),
                nombre=_sql_escape(nombre),
                geom=_sql_escape(geom_json),
            )
        )
    lines.append(",\n".join(values))
    lines.append("ON CONFLICT (codigo) DO UPDATE")
    lines.append(
        "SET tipo = EXCLUDED.tipo, nombre = EXCLUDED.nombre, geometria = EXCLUDED.geometria;"
    )
    OUT_SQL.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
