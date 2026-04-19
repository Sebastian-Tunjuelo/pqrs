"""Job horario: PQRS con fecha límite en +3 días hábiles (CO) y sin validar → alerta."""

from __future__ import annotations

import logging
import os
from datetime import date

import psycopg
from apscheduler.schedulers.blocking import BlockingScheduler

from prioritization.infrastructure.calendario_colombia import fecha_limite_dias_habiles

logger = logging.getLogger(__name__)


def _db_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://pqrs:pqrs@localhost:5433/pqrs?sslmode=disable",
    )


def run_deadline_scan() -> int:
    """Inserta alertas PROXIMO_VENCIMIENTO. Devuelve filas insertadas."""
    hoy = date.today()
    objetivo = fecha_limite_dias_habiles(hoy, 3)
    inserted = 0
    with psycopg.connect(_db_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.id, p.id_externo
                FROM pqrs p
                WHERE p.fecha_limite = %s
                  AND p.validation_status::text != 'VALIDATED'
                  AND p.estado_clasificacion = 'ACEPTADA'
                """,
                (objetivo,),
            )
            rows = cur.fetchall()
            n_cand = len(rows)
            for pid, id_ext in rows:
                label = id_ext or str(pid)
                msg = (
                    f"PQRS {label}: vence en plazo objetivo {objetivo} (3 días hábiles desde hoy). "
                    "Pendiente de validación humana."
                )
                cur.execute(
                    """
                    INSERT INTO pqrs_alertas (pqrs_id, tipo, mensaje, activa)
                    SELECT %s, 'PROXIMO_VENCIMIENTO', %s, true
                    WHERE NOT EXISTS (
                        SELECT 1 FROM pqrs_alertas x
                        WHERE x.pqrs_id = %s
                          AND x.tipo = 'PROXIMO_VENCIMIENTO'
                          AND x.activa = true
                    )
                    """,
                    (pid, msg, pid),
                )
                inserted += cur.rowcount
        conn.commit()
    logger.info(
        "DeadlineMonitor: objetivo=%s candidatos=%s insertadas=%s",
        objetivo,
        n_cand,
        inserted,
    )
    return inserted


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    sched = BlockingScheduler()
    sched.add_job(run_deadline_scan, "interval", hours=1, id="deadline_monitor")
    logger.info("DeadlineMonitorJob cada 1h (primera corrida inmediata)")
    run_deadline_scan()
    sched.start()


if __name__ == "__main__":
    main()
