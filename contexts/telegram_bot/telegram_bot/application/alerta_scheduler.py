from __future__ import annotations
import asyncio
import logging
from datetime import date, datetime

from telegram import Bot
from telegram.error import TelegramError

from telegram_bot.domain.models import AlertaMessage
from telegram_bot.infrastructure.redis_session_store import RedisSessionStore
from telegram_bot.infrastructure.pqrs_api_client import PqrsApiClient
from telegram_bot.application.message_formatter import format_alerta

logger = logging.getLogger(__name__)


async def dispatch_alertas(
    bot: Bot,
    store: RedisSessionStore,
    api: PqrsApiClient,
) -> None:
    hoy = date.today().isoformat()
    try:
        items = await api.get_pendientes_prioridad(page=1, per_page=100)
    except Exception as e:
        logger.error("dispatch_alertas: error consultando API: %s", e)
        return

    funcionarios = await store.get_all_funcionarios()
    destinatarios = [f for f in funcionarios if f.alertas_activas]

    if not destinatarios:
        return

    ahora = datetime.utcnow()

    for snap in items:
        if not snap.fecha_limite:
            continue

        fecha_limite_dt = datetime.combine(snap.fecha_limite, datetime.min.time())
        horas_restantes = (fecha_limite_dt - ahora).total_seconds() / 3600

        if horas_restantes > 24:
            continue

        # Deduplicación
        if await store.alerta_ya_enviada(snap.id, hoy):
            continue

        es_urgente = (snap.nivel_riesgo or "").upper() == "CRITICO" and horas_restantes < 4

        alerta = AlertaMessage(
            chat_id=0,  # se sobreescribe por destinatario
            pqrs_id=snap.id,
            tipo=snap.tipo,
            nivel_riesgo=snap.nivel_riesgo,
            secretaria_nombre=snap.secretaria_nombre,
            fecha_limite=snap.fecha_limite,
            horas_restantes=max(horas_restantes, 0),
            es_urgente=es_urgente,
        )
        texto = format_alerta(alerta)

        for funcionario in destinatarios:
            try:
                await bot.send_message(
                    chat_id=funcionario.chat_id,
                    text=texto,
                    parse_mode="Markdown",
                )
            except TelegramError as e:
                logger.error(
                    "dispatch_alertas: error enviando a %s: %s",
                    funcionario.chat_id,
                    e,
                )

        await store.marcar_alerta_enviada(snap.id, hoy)


async def run_forever(
    bot: Bot,
    store: RedisSessionStore,
    api: PqrsApiClient,
    interval_seconds: int = 3600,
) -> None:
    logger.info("Worker de alertas iniciado. Intervalo: %ds", interval_seconds)
    while True:
        await dispatch_alertas(bot, store, api)
        await asyncio.sleep(interval_seconds)
