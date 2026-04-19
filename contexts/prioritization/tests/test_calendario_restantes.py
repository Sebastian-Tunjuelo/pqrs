"""Días hábiles restantes (CO) hasta fecha límite."""

from __future__ import annotations

from datetime import date

from prioritization.infrastructure.calendario_colombia import (
    cuenta_dias_habiles_entre,
    dias_habiles_restantes_hasta,
)


def test_restantes_futuro() -> None:
    hoy = date(2026, 4, 7)  # martes
    lim = date(2026, 4, 10)  # viernes
    assert cuenta_dias_habiles_entre(hoy, lim) == 3
    assert dias_habiles_restantes_hasta(hoy, lim) == 3


def test_restantes_pasado_negativo() -> None:
    hoy = date(2026, 4, 10)
    lim = date(2026, 4, 7)
    assert dias_habiles_restantes_hasta(hoy, lim) < 0
