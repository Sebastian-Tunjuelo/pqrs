"""Cálculo de días hábiles en Colombia (excluye sábado, domingo y festivos CO)."""

from __future__ import annotations

from datetime import date, timedelta

import holidays


def _es_dia_habil(d: date) -> bool:
    if d.weekday() >= 5:
        return False
    return d not in holidays.CO()


def fecha_limite_dias_habiles(fecha_radicado: date, dias_habiles: int) -> date:
    """
    Último día del plazo: avanza día a día desde el día siguiente a ``fecha_radicado``,
    contando solo días hábiles hasta agotar ``dias_habiles``.
    """
    if dias_habiles < 1:
        msg = "dias_habiles debe ser >= 1"
        raise ValueError(msg)
    d = fecha_radicado
    restantes = dias_habiles
    while restantes > 0:
        d += timedelta(days=1)
        if _es_dia_habil(d):
            restantes -= 1
    return d


def cuenta_dias_habiles_entre(inicio: date, fin: date) -> int:
    """Cuenta días hábiles estrictamente después de inicio hasta fin inclusive."""
    if fin < inicio:
        return 0
    n = 0
    d = inicio
    while d < fin:
        d += timedelta(days=1)
        if _es_dia_habil(d):
            n += 1
    return n


def dias_habiles_restantes_hasta(hoy: date, limite: date) -> int:
    """Días hábiles colombianos entre mañana (desde hoy) y ``limite`` inclusive; negativo si venció."""
    if limite < hoy:
        return -cuenta_dias_habiles_entre(limite, hoy)
    return cuenta_dias_habiles_entre(hoy, limite)
