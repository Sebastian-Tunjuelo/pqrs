from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import Literal


@dataclass
class UserProfile:
    chat_id: int
    rol: Literal["ciudadano", "funcionario"]
    alertas_activas: bool = True
    registered_at: datetime = field(default_factory=datetime.utcnow)
    intentos_fallidos: int = 0
    bloqueado_hasta: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "chat_id": str(self.chat_id),
            "rol": self.rol,
            "alertas_activas": "1" if self.alertas_activas else "0",
            "registered_at": self.registered_at.isoformat(),
            "intentos_fallidos": str(self.intentos_fallidos),
            "bloqueado_hasta": self.bloqueado_hasta.isoformat() if self.bloqueado_hasta else "",
        }

    @classmethod
    def from_dict(cls, d: dict) -> UserProfile:
        return cls(
            chat_id=int(d["chat_id"]),
            rol=d["rol"],
            alertas_activas=d.get("alertas_activas", "1") == "1",
            registered_at=datetime.fromisoformat(d["registered_at"]),
            intentos_fallidos=int(d.get("intentos_fallidos", "0")),
            bloqueado_hasta=datetime.fromisoformat(d["bloqueado_hasta"]) if d.get("bloqueado_hasta") else None,
        )


@dataclass
class PqrsSnapshot:
    id: str
    tipo: str | None = None
    estado_clasificacion: str = ""
    estado_gestion: str | None = None
    nivel_riesgo: str | None = None
    secretaria_nombre: str | None = None
    fecha_limite: date | None = None
    summary_executive: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo": self.tipo or "",
            "estado_clasificacion": self.estado_clasificacion,
            "estado_gestion": self.estado_gestion or "",
            "nivel_riesgo": self.nivel_riesgo or "",
            "secretaria_nombre": self.secretaria_nombre or "",
            "fecha_limite": self.fecha_limite.isoformat() if self.fecha_limite else "",
            "summary_executive": self.summary_executive or "",
        }

    @classmethod
    def from_dict(cls, d: dict) -> PqrsSnapshot:
        return cls(
            id=d["id"],
            tipo=d.get("tipo") or None,
            estado_clasificacion=d.get("estado_clasificacion", ""),
            estado_gestion=d.get("estado_gestion") or None,
            nivel_riesgo=d.get("nivel_riesgo") or None,
            secretaria_nombre=d.get("secretaria_nombre") or None,
            fecha_limite=date.fromisoformat(d["fecha_limite"]) if d.get("fecha_limite") else None,
            summary_executive=d.get("summary_executive") or None,
        )


@dataclass
class IngresoState:
    chat_id: int
    tipo: str | None = None
    descripcion: str | None = None
    nombre_solicitante: str | None = None
    secretaria_codigo: str | None = None
    secretaria_nombre: str | None = None
    step: Literal["tipo", "descripcion", "nombre", "secretaria", "confirmacion"] = "tipo"
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "chat_id": str(self.chat_id),
            "tipo": self.tipo or "",
            "descripcion": self.descripcion or "",
            "nombre_solicitante": self.nombre_solicitante or "",
            "secretaria_codigo": self.secretaria_codigo or "",
            "secretaria_nombre": self.secretaria_nombre or "",
            "step": self.step,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> IngresoState:
        return cls(
            chat_id=int(d["chat_id"]),
            tipo=d.get("tipo") or None,
            descripcion=d.get("descripcion") or None,
            nombre_solicitante=d.get("nombre_solicitante") or None,
            secretaria_codigo=d.get("secretaria_codigo") or None,
            secretaria_nombre=d.get("secretaria_nombre") or None,
            step=d.get("step", "tipo"),
            created_at=datetime.fromisoformat(d["created_at"]),
        )


@dataclass
class AlertaMessage:
    chat_id: int
    pqrs_id: str
    tipo: str | None
    nivel_riesgo: str | None
    secretaria_nombre: str | None
    fecha_limite: date | None
    horas_restantes: float
    es_urgente: bool = False


@dataclass
class TelegramMessage:
    message_id: int
    chat_id: int
    text: str | None
    date: int

    def to_dict(self) -> dict:
        return {"message_id": self.message_id, "chat_id": self.chat_id, "text": self.text, "date": self.date}

    @classmethod
    def from_dict(cls, d: dict) -> TelegramMessage:
        return cls(
            message_id=d["message_id"],
            chat_id=d["chat"]["id"] if "chat" in d else d["chat_id"],
            text=d.get("text"),
            date=d["date"],
        )


@dataclass
class TelegramCallbackQuery:
    id: str
    chat_id: int
    data: str | None
    message_id: int

    def to_dict(self) -> dict:
        return {"id": self.id, "chat_id": self.chat_id, "data": self.data, "message_id": self.message_id}

    @classmethod
    def from_dict(cls, d: dict) -> TelegramCallbackQuery:
        return cls(
            id=d["id"],
            chat_id=d["message"]["chat"]["id"],
            data=d.get("data"),
            message_id=d["message"]["message_id"],
        )


@dataclass
class TelegramUpdate:
    update_id: int
    message: TelegramMessage | None = None
    callback_query: TelegramCallbackQuery | None = None

    def to_dict(self) -> dict:
        d: dict = {"update_id": self.update_id}
        if self.message:
            d["message"] = {
                "message_id": self.message.message_id,
                "chat": {"id": self.message.chat_id},
                "text": self.message.text,
                "date": self.message.date,
            }
        if self.callback_query:
            d["callback_query"] = {
                "id": self.callback_query.id,
                "message": {"chat": {"id": self.callback_query.chat_id}, "message_id": self.callback_query.message_id},
                "data": self.callback_query.data,
            }
        return d

    @classmethod
    def from_dict(cls, d: dict) -> TelegramUpdate:
        msg = TelegramMessage.from_dict(d["message"]) if "message" in d else None
        cbq = TelegramCallbackQuery.from_dict(d["callback_query"]) if "callback_query" in d else None
        return cls(update_id=d["update_id"], message=msg, callback_query=cbq)
