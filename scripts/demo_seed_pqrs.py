#!/usr/bin/env python3
"""
Inserta PQRS sintéticas para demo (metadata.demo = true, id_externo DEMO-#####).

Requisitos: Postgres con migración warehouse aplicada y seeds de dim_secretaria
y dim_territorio cargados.

Uso (desde la raíz del repo):
  DATABASE_URL=postgresql://pqrs:pqrs@localhost:5432/pqrs?sslmode=disable \\
    python scripts/demo_seed_pqrs.py

Opciones:
  --count N   (default 200)
  --purge     Elimina filas demo previas antes de insertar.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import uuid
from datetime import UTC, date, datetime, timedelta

import psycopg

DEMO_FLAG = {"demo": True}

TIPOS = ["P", "Q", "R", "S", "D"]
ACEPTADAS = "ACEPTADA"
RECHAZO_O = "RECHAZADA_OFENSIVO"
RECHAZO_NE = "RECHAZADA_NO_ENTENDIBLE"
PENDIENTE_C = "PENDIENTE"

GESTIONES = ["PENDIENTE", "EN_TRAMITE", "RESPONDIDA", "VENCIDA"]
RIESGOS = ["BAJO", "MEDIO", "ALTO", "CRITICO", None]

FRASES = [
    "Solicito información sobre el trámite de {} en la comuna.",
    "Queja por demora en la respuesta del trámite {}.",
    "Reclamo por servicio de {} no prestado según cronograma.",
    "Sugerencia de mejora en el canal de atención para {}.",
    "Denuncia relacionada con {} en espacio público.",
]
TRAMITES = [
    "licencia de construcción",
    "pico y placa",
    "matrícula escolar",
    "recolección de residuos",
    "parques y bibliotecas",
    "salud preventiva",
    "emprendimiento local",
]


def _hash_contenido(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser(description="Demo: insertar PQRS sintéticas.")
    p.add_argument("--count", type=int, default=200, help="Número de filas (default 200).")
    p.add_argument(
        "--purge",
        action="store_true",
        help="Borra pqrs con metadata.demo=true antes de insertar.",
    )
    args = p.parse_args()
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("ERROR: defina DATABASE_URL", flush=True)
        return 1
    if args.count < 1 or args.count > 5000:
        print("ERROR: --count debe estar entre 1 y 5000", flush=True)
        return 1

    rng = random.Random(42)

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM dim_secretaria")
            if cur.fetchone()[0] == 0:
                print("ERROR: dim_secretaria vacía. Cargue data/seed/seed_dim_secretaria.sql", flush=True)
                return 1
            cur.execute("SELECT codigo FROM dim_secretaria ORDER BY codigo")
            secretarias = [r[0] for r in cur.fetchall()]
            cur.execute("SELECT id FROM dim_territorio ORDER BY id")
            territorios = [r[0] for r in cur.fetchall()]
            if not territorios:
                print("ERROR: dim_territorio vacía. Cargue seed de territorio.", flush=True)
                return 1

        inserted = 0
        with conn.transaction():
            with conn.cursor() as cur:
                if args.purge:
                    cur.execute(
                        """
                        DELETE FROM pqrs_secretaria WHERE pqrs_id IN (
                          SELECT id FROM pqrs WHERE metadata @> %s::jsonb
                        )
                        """,
                        (json.dumps(DEMO_FLAG),),
                    )
                    cur.execute(
                        "DELETE FROM pqrs_historial WHERE pqrs_id IN (SELECT id FROM pqrs WHERE metadata @> %s::jsonb)",
                        (json.dumps(DEMO_FLAG),),
                    )
                    cur.execute(
                        "DELETE FROM pqrs WHERE metadata @> %s::jsonb",
                        (json.dumps(DEMO_FLAG),),
                    )
                    print("Purge: filas demo eliminadas.", flush=True)

                for i in range(1, args.count + 1):
                    pid = uuid.uuid4()
                    id_ext = f"DEMO-{i:05d}"
                    tipo = rng.choice(TIPOS)
                    tramite = rng.choice(TRAMITES)
                    plantilla = rng.choice(FRASES)
                    contenido = plantilla.format(tramite) + f" Ref. interna demo #{i}."
                    h = _hash_contenido(contenido + str(pid))
                    terr_id = rng.choice(territorios)
                    lon = -75.58 + rng.random() * 0.06
                    lat = 6.22 + rng.random() * 0.08
                    rad = datetime.now(UTC) - timedelta(days=rng.randint(0, 120))
                    lim = date.today() + timedelta(days=rng.randint(5, 60))

                    r_clf = rng.random()
                    if r_clf < 0.72:
                        estado_clf = ACEPTADAS
                        estado_ges = rng.choice(GESTIONES)
                        riesgo = rng.choice(RIESGOS)
                        razon = None
                        conf = round(rng.uniform(0.55, 0.99), 2)
                    elif r_clf < 0.86:
                        estado_clf = RECHAZO_NE
                        estado_ges = "PENDIENTE"
                        riesgo = None
                        razon = "Texto insuficiente o ilegible (demo)."
                        conf = 0.9
                    elif r_clf < 0.93:
                        estado_clf = RECHAZO_O
                        estado_ges = "PENDIENTE"
                        riesgo = None
                        razon = "Coincidencia glosario (demo)."
                        conf = 1.0
                    else:
                        estado_clf = PENDIENTE_C
                        estado_ges = "PENDIENTE"
                        riesgo = rng.choice(RIESGOS)
                        razon = None
                        conf = round(rng.uniform(0.4, 0.7), 2)

                    meta = {**DEMO_FLAG, "synthetic_index": i, "tramite": tramite}

                    cur.execute(
                        """
                        INSERT INTO pqrs (
                          id, id_externo, tipo, contenido, contenido_hash,
                          fecha_radicado, fecha_limite, estado_clasificacion,
                          estado_gestion, nivel_riesgo, territorio_id, punto_geo,
                          confianza_clasificacion, razon_rechazo, metadata
                        ) VALUES (
                          %(id)s, %(ext)s, %(tipo)s, %(cont)s, %(hash)s,
                          %(rad)s, %(lim)s, %(eclf)s,
                          %(eges)s, %(riesgo)s, %(tid)s,
                          ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326),
                          %(conf)s, %(razon)s, %(meta)s::jsonb
                        )
                        """,
                        {
                            "id": pid,
                            "ext": id_ext,
                            "tipo": tipo,
                            "cont": contenido,
                            "hash": h,
                            "rad": rad,
                            "lim": lim if estado_clf == ACEPTADAS else None,
                            "eclf": estado_clf,
                            "eges": estado_ges,
                            "riesgo": riesgo,
                            "tid": terr_id,
                            "lon": lon,
                            "lat": lat,
                            "conf": conf,
                            "razon": razon,
                            "meta": json.dumps(meta),
                        },
                    )
                    if estado_clf == ACEPTADAS and rng.random() < 0.85:
                        sec = rng.choice(secretarias)
                        cur.execute(
                            """
                            INSERT INTO pqrs_secretaria (pqrs_id, secretaria_codigo, es_lider, score, motivo)
                            VALUES (%s, %s, true, %s, %s)
                            """,
                            (
                                pid,
                                sec,
                                round(rng.uniform(0.35, 0.95), 2),
                                "Coincidencia keywords (demo).",
                            ),
                        )
                    inserted += 1

    print(f"OK: insertadas {inserted} PQRS demo (id_externo DEMO-#####).", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
