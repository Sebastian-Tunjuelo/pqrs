"""Enums del agregado PQRS (ARCHITECTURE §4.1)."""

from enum import Enum


class TipoPqrs(str, Enum):
    PETICION = "P"
    QUEJA = "Q"
    RECLAMO = "R"
    SUGERENCIA = "S"
    DENUNCIA = "D"


class EstadoClasificacion(str, Enum):
    PENDIENTE = "PENDIENTE"
    ACEPTADA = "ACEPTADA"
    RECHAZADA_OFENSIVO = "RECHAZADA_OFENSIVO"
    RECHAZADA_NO_ENTENDIBLE = "RECHAZADA_NO_ENTENDIBLE"


class NivelRiesgo(str, Enum):
    CRITICO = "CRITICO"
    ALTO = "ALTO"
    MEDIO = "MEDIO"
    BAJO = "BAJO"


class EstadoGestion(str, Enum):
    PENDIENTE = "PENDIENTE"
    EN_TRAMITE = "EN_TRAMITE"
    RESPONDIDA = "RESPONDIDA"
    VENCIDA = "VENCIDA"
