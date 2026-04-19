from __future__ import annotations
import logging
import math

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from telegram_bot.domain.models import IngresoState
from telegram_bot.domain.exceptions import PqrsApiError
from telegram_bot.infrastructure.redis_session_store import RedisSessionStore
from telegram_bot.infrastructure.pqrs_api_client import PqrsApiClient
from telegram_bot.logging_config import hash_chat_id

logger = logging.getLogger(__name__)

SELECCIONAR_TIPO        = 0
INGRESAR_DESCRIPCION    = 1
INGRESAR_NOMBRE         = 2
SELECCIONAR_SECRETARIA  = 3
CONFIRMAR               = 4

TIPO_LABELS = {
    "P": "Petición",
    "Q": "Queja",
    "R": "Reclamo",
    "S": "Sugerencia",
    "D": "Denuncia",
}

PAGE_SIZE = 8   # secretarías por página de botones

_store: RedisSessionStore | None = None
_api: PqrsApiClient | None = None


def init_conversation_handlers(store: RedisSessionStore, api: PqrsApiClient) -> None:
    global _store, _api
    _store = store
    _api = api


def _log(chat_id: int, step: str, result: str) -> None:
    logger.info(
        "ingreso_pqrs",
        extra={
            "chat_id_hash": hash_chat_id(chat_id),
            "command": f"nueva_pqrs:{step}",
            "result": result,
            "duration_ms": 0,
        },
    )


def _secretaria_keyboard(secretarias: list[dict], page: int = 0) -> InlineKeyboardMarkup:
    """Construye teclado paginado de secretarías."""
    total_pages = math.ceil(len(secretarias) / PAGE_SIZE)
    start = page * PAGE_SIZE
    chunk = secretarias[start: start + PAGE_SIZE]

    rows = []
    for s in chunk:
        codigo = s.get("codigo", "")
        nombre = s.get("nombre", "")
        label = f"{codigo} — {nombre[:30]}"
        rows.append([InlineKeyboardButton(label, callback_data=f"sec:{codigo}:{nombre[:40]}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀ Anterior", callback_data=f"sec_page:{page-1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Siguiente ▶", callback_data=f"sec_page:{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton("❌ Cancelar", callback_data="ingreso:cancelar")])
    return InlineKeyboardMarkup(rows)


# ── Paso 1: /nueva_pqrs ──────────────────────────────────────────────────────

async def nueva_pqrs_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    state = IngresoState(chat_id=chat_id)
    await _store.save_ingreso(state)

    keyboard = [
        [InlineKeyboardButton("📄 Petición", callback_data="tipo:P"),
         InlineKeyboardButton("😤 Queja",    callback_data="tipo:Q")],
        [InlineKeyboardButton("⚠️ Reclamo",  callback_data="tipo:R"),
         InlineKeyboardButton("💡 Sugerencia", callback_data="tipo:S")],
        [InlineKeyboardButton("🚨 Denuncia", callback_data="tipo:D")],
    ]
    await update.message.reply_text(
        "📝 Radicar nueva PQRS\n\nSelecciona el tipo de solicitud:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    _log(chat_id, "start", "ok")
    return SELECCIONAR_TIPO


# ── Paso 2: seleccionar tipo ─────────────────────────────────────────────────

async def seleccionar_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    tipo = (query.data or "").split(":")[1]

    state = await _store.get_ingreso(chat_id) or IngresoState(chat_id=chat_id)
    state.tipo = tipo
    state.step = "descripcion"
    await _store.save_ingreso(state)

    await query.edit_message_text(
        f"Tipo: {TIPO_LABELS.get(tipo, tipo)}\n\n"
        "Describe tu solicitud con el mayor detalle posible:"
    )
    _log(chat_id, "tipo", tipo)
    return INGRESAR_DESCRIPCION


# ── Paso 3: descripción ───────────────────────────────────────────────────────

async def ingresar_descripcion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    texto = (update.message.text or "").strip()

    if not texto:
        await update.message.reply_text(
            "La descripción no puede estar vacía. Por favor escribe el detalle:"
        )
        return INGRESAR_DESCRIPCION

    state = await _store.get_ingreso(chat_id)
    if not state:
        await update.message.reply_text("La sesión expiró. Usa /nueva_pqrs para comenzar.")
        return ConversationHandler.END

    state.descripcion = texto
    state.step = "nombre"
    await _store.save_ingreso(state)

    await update.message.reply_text("¿Cuál es tu nombre completo?")
    _log(chat_id, "descripcion", "ok")
    return INGRESAR_NOMBRE


# ── Paso 4: nombre ────────────────────────────────────────────────────────────

async def ingresar_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    nombre = (update.message.text or "").strip()

    if not nombre:
        await update.message.reply_text("El nombre no puede estar vacío:")
        return INGRESAR_NOMBRE

    state = await _store.get_ingreso(chat_id)
    if not state:
        await update.message.reply_text("La sesión expiró. Usa /nueva_pqrs para comenzar.")
        return ConversationHandler.END

    state.nombre_solicitante = nombre
    state.step = "secretaria"
    await _store.save_ingreso(state)

    # Cargar secretarías y mostrar primera página
    try:
        secretarias = await _api.get_secretarias()
        # Guardar en context para no volver a consultar
        context.user_data["secretarias"] = secretarias
    except PqrsApiError:
        secretarias = []
        context.user_data["secretarias"] = []

    if not secretarias:
        await update.message.reply_text(
            "No se pudieron cargar las secretarías. Intenta de nuevo más tarde."
        )
        await _store.clear_ingreso(chat_id)
        return ConversationHandler.END

    keyboard = _secretaria_keyboard(secretarias, page=0)
    await update.message.reply_text(
        f"Hay {len(secretarias)} secretarías disponibles.\n"
        "Selecciona la secretaría a la que va dirigida tu PQRS:",
        reply_markup=keyboard,
    )
    _log(chat_id, "nombre", "ok")
    return SELECCIONAR_SECRETARIA


# ── Paso 5a: paginación de secretarías ───────────────────────────────────────

async def paginar_secretarias(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    page = int((query.data or "sec_page:0").split(":")[1])
    secretarias = context.user_data.get("secretarias", [])
    keyboard = _secretaria_keyboard(secretarias, page=page)
    await query.edit_message_reply_markup(reply_markup=keyboard)
    return SELECCIONAR_SECRETARIA


# ── Paso 5b: seleccionar secretaría ──────────────────────────────────────────

async def seleccionar_secretaria(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    # formato: sec:{codigo}:{nombre}
    parts = (query.data or "").split(":", 2)
    if len(parts) < 3:
        await query.answer("Selección inválida", show_alert=True)
        return SELECCIONAR_SECRETARIA

    codigo = parts[1].strip().upper()
    nombre_sel = parts[2].strip()

    # Validar que el código existe en la lista
    secretarias = context.user_data.get("secretarias", [])
    valida = any(s.get("codigo", "").upper() == codigo for s in secretarias)

    if not valida:
        await query.edit_message_text(
            f"La secretaría '{codigo}' no es válida. Usa /nueva_pqrs para intentar de nuevo."
        )
        await _store.clear_ingreso(chat_id)
        return ConversationHandler.END

    state = await _store.get_ingreso(chat_id)
    if not state:
        await query.edit_message_text("La sesión expiró. Usa /nueva_pqrs para comenzar.")
        return ConversationHandler.END

    state.secretaria_codigo = codigo
    state.secretaria_nombre = nombre_sel
    state.step = "confirmacion"
    await _store.save_ingreso(state)

    # Mostrar resumen completo
    resumen = (
        f"📋 Resumen de tu PQRS:\n\n"
        f"Tipo: {TIPO_LABELS.get(state.tipo or '', state.tipo or '—')}\n"
        f"Solicitante: {state.nombre_solicitante}\n"
        f"Secretaría: {codigo} — {nombre_sel}\n"
        f"Descripción:\n{(state.descripcion or '')[:400]}\n\n"
        "¿Confirmas el envío?"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirmar", callback_data="ingreso:confirmar"),
         InlineKeyboardButton("❌ Cancelar",  callback_data="ingreso:cancelar")],
    ])
    await query.edit_message_text(resumen, reply_markup=keyboard)
    _log(chat_id, "secretaria", codigo)
    return CONFIRMAR


# ── Paso 6: confirmar ─────────────────────────────────────────────────────────

async def confirmar_ingreso(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    accion = (query.data or "").split(":")[1]

    if accion == "cancelar":
        await _store.clear_ingreso(chat_id)
        await query.edit_message_text("Radicación cancelada.")
        _log(chat_id, "confirmacion", "cancelado")
        return ConversationHandler.END

    state = await _store.get_ingreso(chat_id)
    if not state:
        await query.edit_message_text("La sesión expiró. Usa /nueva_pqrs para comenzar.")
        return ConversationHandler.END

    try:
        payload = {
            "tipo": state.tipo,
            "contenido": state.descripcion,
            "nombre_solicitante": state.nombre_solicitante,
            "secretaria_codigo": state.secretaria_codigo,
            "canal": "telegram",
        }
        result = await _api.crear_pqrs(payload)
        await _store.clear_ingreso(chat_id)
        id_externo   = result.get("id_externo", "—")
        fecha_limite = result.get("fecha_limite", "—")
        await query.edit_message_text(
            f"✅ PQRS radicada exitosamente.\n\n"
            f"Radicado: {id_externo}\n"
            f"Secretaría: {state.secretaria_codigo} — {state.secretaria_nombre}\n"
            f"Fecha límite SLA: {fecha_limite}\n\n"
            "Recibirás respuesta dentro del plazo establecido por la Ley 1755."
        )
        _log(chat_id, "confirmacion", "ok")
    except PqrsApiError as e:
        await _store.clear_ingreso(chat_id)
        await query.edit_message_text(
            "No se pudo radicar la PQRS. Intente nuevamente o contacte al administrador."
        )
        _log(chat_id, "confirmacion", f"error_{e.status_code}")

    return ConversationHandler.END


# ── Cancelar en cualquier paso ────────────────────────────────────────────────

async def cancelar_ingreso(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    await _store.clear_ingreso(chat_id)
    await update.message.reply_text("Radicación cancelada.")
    _log(chat_id, "cancelar", "ok")
    return ConversationHandler.END


# ── Construir el ConversationHandler ─────────────────────────────────────────

def build_ingreso_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("nueva_pqrs", nueva_pqrs_start)],
        states={
            SELECCIONAR_TIPO: [
                CallbackQueryHandler(seleccionar_tipo, pattern="^tipo:"),
            ],
            INGRESAR_DESCRIPCION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ingresar_descripcion),
            ],
            INGRESAR_NOMBRE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ingresar_nombre),
            ],
            SELECCIONAR_SECRETARIA: [
                CallbackQueryHandler(paginar_secretarias,    pattern="^sec_page:"),
                CallbackQueryHandler(seleccionar_secretaria, pattern="^sec:"),
                CallbackQueryHandler(confirmar_ingreso,      pattern="^ingreso:cancelar"),
            ],
            CONFIRMAR: [
                CallbackQueryHandler(confirmar_ingreso, pattern="^ingreso:"),
            ],
        },
        fallbacks=[CommandHandler("cancelar", cancelar_ingreso)],
        allow_reentry=True,
    )
