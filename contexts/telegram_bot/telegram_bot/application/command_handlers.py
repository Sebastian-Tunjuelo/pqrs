from __future__ import annotations
import asyncio
import logging
import time
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from telegram_bot import config
from telegram_bot.domain.models import UserProfile
from telegram_bot.domain.exceptions import PqrsApiError
from telegram_bot.infrastructure.redis_session_store import RedisSessionStore
from telegram_bot.infrastructure.pqrs_api_client import PqrsApiClient
from telegram_bot.infrastructure.ollama_client import OllamaClient
from telegram_bot.application.message_formatter import (
    format_pqrs_detail,
    format_pqrs_list_item,
    format_metricas,
    format_secretaria_list,
)
from telegram_bot.logging_config import hash_chat_id

logger = logging.getLogger(__name__)

# Instancias compartidas (inicializadas en bot.py)
_store: RedisSessionStore | None = None
_api: PqrsApiClient | None = None
_ollama: OllamaClient | None = None


def init_handlers(store: RedisSessionStore, api: PqrsApiClient, ollama: OllamaClient) -> None:
    global _store, _api, _ollama
    _store = store
    _api = api
    _ollama = ollama


def _log(chat_id: int, command: str, result: str, duration_ms: float = 0) -> None:
    logger.info(
        "handled",
        extra={
            "chat_id_hash": hash_chat_id(chat_id),
            "command": command,
            "result": result,
            "duration_ms": round(duration_ms),
        },
    )


async def _get_user(chat_id: int) -> UserProfile | None:
    return await _store.get_user(chat_id)


async def _require_funcionario(update: Update) -> bool:
    user = await _get_user(update.effective_chat.id)
    if not user or user.rol != "funcionario":
        await update.message.reply_text("Este comando está disponible solo para funcionarios.")
        return False
    return True


# ── /start ──────────────────────────────────────────────────────────────────

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    t0 = time.monotonic()

    user = await _store.get_user(chat_id)
    rol_actual = f" (rol actual: *{user.rol}*)" if user else ""

    keyboard = [
        [InlineKeyboardButton("👤 Ciudadano", callback_data="rol:ciudadano")],
        [InlineKeyboardButton("🏛️ Funcionario", callback_data="rol:funcionario")],
    ]
    await update.message.reply_text(
        f"🏙️ *Bot PQRS Alcaldía de Medellín*{rol_actual}\n\n"
        "Puedes consultar el estado de PQRS, recibir alertas y radicar nuevas solicitudes.\n\n"
        "¿Cuál es tu rol?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
    _log(chat_id, "/start", "ok", (time.monotonic() - t0) * 1000)


async def rol_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    data = query.data or ""

    if not data.startswith("rol:"):
        return

    rol = data.split(":", 1)[1]

    if rol == "ciudadano":
        profile = UserProfile(chat_id=chat_id, rol="ciudadano")
        await _store.save_user(profile)
        await query.edit_message_text(
            "✅ Registrado como ciudadano.\n\n"
            "Comandos disponibles:\n"
            "• /pqrs <id> — consultar una PQRS\n"
            "• /nueva_pqrs — radicar una nueva PQRS\n"
            "• Escribe cualquier pregunta para el asistente IA",
        )
        _log(chat_id, "rol_callback", "ciudadano")

    elif rol == "funcionario":
        # Verificar si está bloqueado
        if await _store.esta_bloqueado(chat_id):
            await query.edit_message_text(
                "🔒 Demasiados intentos fallidos. Intenta de nuevo en 10 minutos."
            )
            return
        # Guardar estado en Redis en lugar de context.user_data
        await _store._redis.set(f"bot:esperando_codigo:{chat_id}", "1", ex=300)
        await query.edit_message_text(
            "🔐 Ingresa el código de acceso de funcionario:"
        )
        _log(chat_id, "rol_callback", "esperando_codigo_funcionario")


async def codigo_funcionario_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el texto cuando se espera el código de funcionario."""
    chat_id = update.effective_chat.id

    esperando = await _store._redis.get(f"bot:esperando_codigo:{chat_id}")
    if not esperando:
        return  # No estamos en este flujo

    codigo = (update.message.text or "").strip()

    if await _store.esta_bloqueado(chat_id):
        await update.message.reply_text("🔒 Cuenta bloqueada temporalmente. Intenta en 10 minutos.")
        await _store._redis.delete(f"bot:esperando_codigo:{chat_id}")
        return

    if codigo == config.TELEGRAM_FUNCIONARIO_SECRET:
        profile = UserProfile(chat_id=chat_id, rol="funcionario")
        await _store.save_user(profile)
        await _store.reset_intentos(chat_id)
        await _store._redis.delete(f"bot:esperando_codigo:{chat_id}")
        await update.message.reply_text(
            "✅ Registrado como funcionario.\n\n"
            "Comandos disponibles:\n"
            "• /pqrs <id> — detalle de PQRS\n"
            "• /pendientes — PQRS pendientes priorizadas\n"
            "• /metricas — métricas del sistema\n"
            "• /secretarias — listar secretarías\n"
            "• /secretaria <codigo> — PQRS por secretaría\n"
            "• /alertas on|off — activar/desactivar alertas\n"
            "• /nueva_pqrs — radicar nueva PQRS",
        )
        _log(chat_id, "codigo_funcionario", "ok")
    else:
        intentos = await _store.incrementar_intentos(chat_id)
        restantes = 3 - intentos
        if intentos >= 3:
            await _store.bloquear(chat_id)
            await _store._redis.delete(f"bot:esperando_codigo:{chat_id}")
            await update.message.reply_text(
                "🔒 Código incorrecto. Cuenta bloqueada por 10 minutos."
            )
            _log(chat_id, "codigo_funcionario", "bloqueado")
        else:
            await update.message.reply_text(
                f"❌ Código incorrecto. Te quedan {restantes} intento(s)."
            )
            _log(chat_id, "codigo_funcionario", f"fallo_{intentos}")


# ── /pqrs <id> ───────────────────────────────────────────────────────────────

async def pqrs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    t0 = time.monotonic()
    args = context.args or []
    if not args:
        await update.message.reply_text("Uso: /pqrs <id>")
        return
    pqrs_id = args[0].strip()
    try:
        snap = await _api.get_pqrs(pqrs_id)
        if snap is None:
            await update.message.reply_text("No se encontró una PQRS con el identificador indicado.")
            _log(chat_id, "/pqrs", "not_found", (time.monotonic() - t0) * 1000)
            return
        await update.message.reply_text(format_pqrs_detail(snap))
        _log(chat_id, "/pqrs", "ok", (time.monotonic() - t0) * 1000)
    except PqrsApiError:
        await update.message.reply_text("El servicio no está disponible en este momento. Intente más tarde.")
        _log(chat_id, "/pqrs", "error", (time.monotonic() - t0) * 1000)


# ── /pendientes ───────────────────────────────────────────────────────────────

async def pendientes_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    t0 = time.monotonic()
    if not await _require_funcionario(update):
        return
    try:
        items = await _api.get_pendientes_prioridad(page=1, per_page=10)
        if not items:
            await update.message.reply_text("No hay PQRS pendientes en este momento.")
            return
        lines = ["📋 *PQRS pendientes priorizadas:*\n"]
        for i, snap in enumerate(items, 1):
            lines.append(format_pqrs_list_item(snap, i))
        keyboard = None
        # Verificar si hay más páginas
        all_items = await _api.get_pendientes_prioridad(page=1, per_page=11)
        if len(all_items) > 10:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("Ver más →", callback_data="pendientes:2")
            ]])
        await update.message.reply_text(
            "\n".join(lines),
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
        _log(chat_id, "/pendientes", "ok", (time.monotonic() - t0) * 1000)
    except PqrsApiError:
        await update.message.reply_text("El servicio no está disponible en este momento. Intente más tarde.")
        _log(chat_id, "/pendientes", "error", (time.monotonic() - t0) * 1000)


async def pendientes_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    page = int((query.data or "pendientes:2").split(":")[1])
    try:
        items = await _api.get_pendientes_prioridad(page=page, per_page=10)
        if not items:
            await query.edit_message_text("No hay más PQRS pendientes.")
            return
        lines = [f"📋 *PQRS pendientes — página {page}:*\n"]
        for i, snap in enumerate(items, 1):
            lines.append(format_pqrs_list_item(snap, i))
        next_items = await _api.get_pendientes_prioridad(page=page, per_page=11)
        keyboard = None
        if len(next_items) > 10:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(f"Ver más →", callback_data=f"pendientes:{page+1}")
            ]])
        await query.edit_message_text("\n".join(lines), parse_mode="MarkdownV2", reply_markup=keyboard)
    except PqrsApiError:
        await query.edit_message_text("El servicio no está disponible en este momento.")


# ── /metricas ─────────────────────────────────────────────────────────────────

async def metricas_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    t0 = time.monotonic()
    if not await _require_funcionario(update):
        return
    try:
        data = await _api.get_metricas()
        await update.message.reply_text(format_metricas(data), parse_mode="Markdown")
        _log(chat_id, "/metricas", "ok", (time.monotonic() - t0) * 1000)
    except PqrsApiError:
        await update.message.reply_text("No se pudieron obtener las métricas en este momento.")
        _log(chat_id, "/metricas", "error", (time.monotonic() - t0) * 1000)


# ── /secretarias / /secretaria <codigo> ──────────────────────────────────────

async def secretarias_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    t0 = time.monotonic()
    if not await _require_funcionario(update):
        return
    try:
        secs = await _api.get_secretarias()
        await update.message.reply_text(format_secretaria_list(secs), parse_mode="Markdown")
        _log(chat_id, "/secretarias", "ok", (time.monotonic() - t0) * 1000)
    except PqrsApiError:
        await update.message.reply_text("El servicio no está disponible en este momento. Intente más tarde.")
        _log(chat_id, "/secretarias", "error", (time.monotonic() - t0) * 1000)


async def secretaria_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    t0 = time.monotonic()
    if not await _require_funcionario(update):
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Uso: /secretaria <codigo>")
        return
    codigo = args[0].strip().upper()
    try:
        items = await _api.get_pqrs_por_secretaria(codigo)
        if items is None:
            await update.message.reply_text("No se encontró la secretaría con el código indicado.")
            return
        if not items:
            await update.message.reply_text(f"No hay PQRS para la secretaría {codigo}.")
            return
        lines = [f"🏛️ *PQRS — Secretaría {codigo}:*\n"]
        for i, snap in enumerate(items, 1):
            lines.append(format_pqrs_list_item(snap, i))
        await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")
        _log(chat_id, "/secretaria", "ok", (time.monotonic() - t0) * 1000)
    except PqrsApiError:
        await update.message.reply_text("El servicio no está disponible en este momento. Intente más tarde.")
        _log(chat_id, "/secretaria", "error", (time.monotonic() - t0) * 1000)


# ── /alertas on|off ───────────────────────────────────────────────────────────

async def alertas_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if not await _require_funcionario(update):
        return
    args = context.args or []
    if not args or args[0].lower() not in ("on", "off"):
        await update.message.reply_text("Uso: /alertas on  o  /alertas off")
        return
    activo = args[0].lower() == "on"
    user = await _store.get_user(chat_id)
    if user:
        user.alertas_activas = activo
        await _store.save_user(user)
    estado = "activadas ✅" if activo else "desactivadas ❌"
    await update.message.reply_text(f"Alertas automáticas {estado}.")
    _log(chat_id, "/alertas", f"{'on' if activo else 'off'}")


# ── /nueva_consulta ───────────────────────────────────────────────────────────

async def nueva_consulta_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await _store.clear_session(chat_id)
    await update.message.reply_text("🔄 Sesión del asistente reiniciada. ¿En qué puedo ayudarte?")
    _log(chat_id, "/nueva_consulta", "ok")


# ── /cancelar ─────────────────────────────────────────────────────────────────

async def cancelar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await _store.clear_ingreso(chat_id)
    await _store._redis.delete(f"bot:esperando_codigo:{chat_id}")
    await update.message.reply_text("❌ Operación cancelada.")
    _log(chat_id, "/cancelar", "ok")


# ── Fallback — Asistente IA ───────────────────────────────────────────────────

async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    t0 = time.monotonic()

    # Si estamos esperando código de funcionario (estado en Redis), delegar
    esperando = await _store._redis.get(f"bot:esperando_codigo:{chat_id}")
    if esperando:
        await codigo_funcionario_handler(update, context)
        return

    texto = (update.message.text or "").strip()
    if not texto:
        return

    user = await _store.get_user(chat_id)

    # Si no está registrado, pedir que use /start primero
    if not user:
        context.user_data.pop("esperando_codigo", None)
        await update.message.reply_text(
            "👋 Para comenzar, usa el comando /start para registrarte."
        )
        return

    rol = user.rol
    historial = await _store.get_session(chat_id)

    # Mensaje de espera si tarda
    wait_sent = False

    async def _send_wait():
        nonlocal wait_sent
        await asyncio.sleep(30)
        if not wait_sent:
            wait_sent = True
            await update.message.reply_text("⏳ El asistente está procesando tu consulta, por favor espera...")

    wait_task = asyncio.create_task(_send_wait())

    try:
        respuesta = await asyncio.wait_for(
            _ollama.mensaje_gestion(texto, historial, rol),
            timeout=60.0,
        )
        wait_task.cancel()
        await _store.append_session(chat_id, {"role": "user", "content": texto})
        await _store.append_session(chat_id, {"role": "assistant", "content": respuesta})
        await update.message.reply_text(respuesta)
        _log(chat_id, "fallback_ia", "ok", (time.monotonic() - t0) * 1000)
    except (asyncio.TimeoutError, PqrsApiError):
        wait_task.cancel()
        await update.message.reply_text(
            "El asistente no está disponible en este momento. "
            "Puedes usar los comandos directos como /pqrs <id>."
        )
        _log(chat_id, "fallback_ia", "error", (time.monotonic() - t0) * 1000)
