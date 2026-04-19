"""SLA en días hábiles según Ley 1755 de 2015 (heurística por tipo + nivel)."""

from __future__ import annotations

from shared_kernel.value_objects.enums import NivelRiesgo, TipoPqrs


def dias_habiles_sla(tipo: TipoPqrs, nivel: NivelRiesgo) -> int:
    """
    Retorna días hábiles de respuesta.

    - Riesgo crítico (vida, menores, emergencias): 10 días hábiles.
    - Consultas / bajo impacto: 30 días hábiles (incluye sugerencias de carácter consultivo).
    - Peticiones, quejas, reclamos y denuncias en riesgo medio/alto: 15 días hábiles por defecto.
    """
    if nivel == NivelRiesgo.CRITICO:
        return 10
    if nivel == NivelRiesgo.BAJO or tipo == TipoPqrs.SUGERENCIA:
        return 30
    return 15
