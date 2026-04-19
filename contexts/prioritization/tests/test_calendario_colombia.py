from datetime import date

import holidays

from prioritization.infrastructure.calendario_colombia import (
    cuenta_dias_habiles_entre,
    fecha_limite_dias_habiles,
)


def test_un_dia_habil_desde_viernes() -> None:
    rad = date(2025, 1, 3)
    assert rad.weekday() == 4
    lim = fecha_limite_dias_habiles(rad, 1)
    assert lim == date(2025, 1, 7)


def test_navidad_2025_salta_festivo() -> None:
    co = holidays.CO(years=[2025])
    assert date(2025, 12, 25) in co
    rad = date(2025, 12, 24)
    lim = fecha_limite_dias_habiles(rad, 1)
    assert lim == date(2025, 12, 26)


def test_cuenta_dias_habiles_entre() -> None:
    a = date(2025, 1, 7)
    b = date(2025, 1, 10)
    assert cuenta_dias_habiles_entre(a, b) == 3
