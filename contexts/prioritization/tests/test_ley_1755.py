from shared_kernel.value_objects.enums import NivelRiesgo, TipoPqrs

from prioritization.domain.ley_1755 import dias_habiles_sla


def test_critico_siempre_10() -> None:
    assert dias_habiles_sla(TipoPqrs.PETICION, NivelRiesgo.CRITICO) == 10
    assert dias_habiles_sla(TipoPqrs.SUGERENCIA, NivelRiesgo.CRITICO) == 10


def test_sugerencia_no_critico_30() -> None:
    assert dias_habiles_sla(TipoPqrs.SUGERENCIA, NivelRiesgo.MEDIO) == 30


def test_bajo_30() -> None:
    assert dias_habiles_sla(TipoPqrs.QUEJA, NivelRiesgo.BAJO) == 30


def test_queja_alto_15() -> None:
    assert dias_habiles_sla(TipoPqrs.QUEJA, NivelRiesgo.ALTO) == 15
