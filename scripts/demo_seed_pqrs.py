#!/usr/bin/env python3
"""
Inserta PQRS sintéticas para demo (metadata.demo = true, id_externo DEMO-#####).

Los textos siguen tres arquetipos inspirados en criterios de radicación de la
Alcaldía de Medellín (petición formal aceptada, redacción ilegible, lenguaje ofensivo).

Requisitos: Postgres con migración warehouse aplicada y seeds de dim_secretaria
y dim_territorio cargados.

Uso (desde la raíz del repo):
  DATABASE_URL=postgresql://pqrs:pqrs@localhost:5433/pqrs?sslmode=disable \\
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

ACEPTADA = "ACEPTADA"
RECHAZO_O = "RECHAZADA_OFENSIVO"
RECHAZO_NE = "RECHAZADA_NO_ENTENDIBLE"

GESTIONES_ACEPTADAS = ["PENDIENTE", "EN_TRAMITE", "RESPONDIDA", "VENCIDA"]
RIESGOS = ["BAJO", "MEDIO", "ALTO", "CRITICO", None]


def _hash_contenido(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _contenido_aceptada(i: int, id_ext: str) -> str:
    comuna = 10 + (i % 9)
    return f"""Estimada Alcaldía de Medellín,

Por medio de este documento solicito información referente a los proyectos de
infraestructura vial ejecutados en la comuna {comuna} durante el año 2023.

Específicamente requiero:
- Presupuesto asignado
- Estado de avance
- Cronograma de ejecución
- Responsable del proyecto

Cordialmente,
Juan Carlos Pérez González
CC: {1000000000 + i}

Referencia interna: {id_ext}."""


def _contenido_ilegible(i: int, id_ext: str) -> str:
    variantes = [
        (
            "xola k tal esto es sobre eso dk la vía xq ayer pasé y noooo m enendí "
            "y entonces q paso q el señor ese dijo k pa q mañana o pasado xa cuando "
            "vuelva a pasar x hay pero eso no es claro sabe parece k ay un hoyo "
            "o algo x la cra 30 y ndie ha hecho nada desde el año pasado q dije "
            "algo ahora q vuelvo a decir q hagan algo porfa muchas gracias"
        ),
        (
            "buenas tardes es q necesito q me ayuden con eso del parque xq va mal "
            "y no se sabe ni cuando ni pa cuando y yo ya pregunté y nada q me dicen "
            "claro entonces q hago yo si ndie responde y eso lleva meses ya gracias"
        ),
        (
            "hola miren es q hay un problema con el arbol q cayó y eso y entonces "
            "yo llamé y me dijeron k ya pero no vino nadie y sigue igual entonces "
            "xq no hacen nada si eso es peligroso pa los niños del barrio gracias"
        ),
    ]
    cuerpo = variantes[i % len(variantes)]
    return f"{cuerpo}\n\nRadicado interno: {id_ext}."


def _contenido_ofensivo(i: int, id_ext: str) -> str:
    """Texto de reclamo con lenguaje irrespetuoso (solo entorno demo / clasificador)."""
    variantes = [
        (
            "¡¿QUÉ VAINA ES ESTA?! Ustedes son unos inútiles de mierda, hace tres meses "
            "reporté un problema de agua en la vereda y no han hecho un carajo. "
            "Mientras tanto, el alcalde se lleva la plata robada como siempre y los "
            "trabajadores son unos maricones que no hacen nada. Dejen de ser tan jodidos "
            "y arreglen esto de una vez o voy a hacer un escándalo en redes. "
            "Esto es una porquería de administración, ¡qué patanes son todos!"
        ),
        (
            "Esto es un desastre y ustedes son unos imbéciles que no sirven para nada. "
            "Llevo semanas esperando respuesta y solo dan excusas de mierda. "
            "Si no arreglan el tema del basurero voy a denunciar a todos estos ladrones. "
            "¡Qué jodida es esta vaina!"
        ),
        (
            "No aguanto más esta porquería de servicio. Son unos inútiles, unos patanes, "
            "y el que atendió fue un idiota. Hagan algo de una vez o la vaina se les va "
            "a ir de las manos, carajo."
        ),
    ]
    cuerpo = variantes[i % len(variantes)]
    return f"{cuerpo}\n\nIdentificador demo: {id_ext}."


def _clasificacion_por_indice(i: int) -> str:
    """Reparto cíclico: aceptada / ilegible / ofensivo (~un tercio cada una)."""
    r = (i - 1) % 3
    if r == 0:
        return ACEPTADA
    if r == 1:
        return RECHAZO_NE
    return RECHAZO_O


def main() -> int:
    p = argparse.ArgumentParser(description="Demo: insertar PQRS sintéticas (arquetipos Medellín).")
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
                    estado_clf = _clasificacion_por_indice(i)

                    if estado_clf == ACEPTADA:
                        tipo = "P"
                        contenido = _contenido_aceptada(i, id_ext)
                        estado_ges = rng.choice(GESTIONES_ACEPTADAS)
                        riesgo = rng.choice(RIESGOS)
                        razon = None
                        conf = round(rng.uniform(0.86, 0.99), 2)
                    elif estado_clf == RECHAZO_NE:
                        tipo = rng.choice(["Q", "R"])
                        contenido = _contenido_ilegible(i, id_ext)
                        estado_ges = "PENDIENTE"
                        riesgo = None
                        razon = (
                            "Falta de claridad redaccional, sin estructura, sin datos de "
                            "identificación claros. Texto tipo mensajería difícil de entender (demo)."
                        )
                        conf = round(rng.uniform(0.88, 0.95), 2)
                    else:
                        tipo = "R"
                        contenido = _contenido_ofensivo(i, id_ext)
                        estado_ges = "PENDIENTE"
                        riesgo = None
                        razon = (
                            "Lenguaje vulgar, ofensivo e irrespetuoso. Incumplimiento de normas de "
                            "cortesía en peticiones oficiales (demo)."
                        )
                        conf = round(rng.uniform(0.96, 1.0), 2)

                    h = _hash_contenido(contenido + str(pid))
                    terr_id = rng.choice(territorios)
                    lon = -75.58 + rng.random() * 0.06
                    lat = 6.22 + rng.random() * 0.08
                    rad = datetime.now(UTC) - timedelta(days=rng.randint(0, 120))
                    lim = date.today() + timedelta(days=rng.randint(5, 60)) if estado_clf == ACEPTADA else None

                    meta = {
                        **DEMO_FLAG,
                        "synthetic_index": i,
                        "arquetipo_demo": (
                            "aceptada_informacion_vial"
                            if estado_clf == ACEPTADA
                            else ("ilegible_chat" if estado_clf == RECHAZO_NE else "ofensivo_reclamo")
                        ),
                    }

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
                            "lim": lim,
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
                    if estado_clf == ACEPTADA and rng.random() < 0.92:
                        sec = rng.choice(secretarias)
                        cur.execute(
                            """
                            INSERT INTO pqrs_secretaria (pqrs_id, secretaria_codigo, es_lider, score, motivo)
                            VALUES (%s, %s, true, %s, %s)
                            """,
                            (
                                pid,
                                sec,
                                round(rng.uniform(0.55, 0.95), 2),
                                "Coincidencia temática con secretaría (demo).",
                            ),
                        )
                    inserted += 1

    print(
        f"OK: insertadas {inserted} PQRS demo (ciclo aceptada / ilegible / ofensivo; id_externo DEMO-#####).",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
