"""Punto de entrada principal del bot de Telegram PQRS Medellín."""
import logging

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from telegram_bot.config import validate, TELEGRAM_BOT_TOKEN, PQRS_API_URL, REDIS_URL, OLLAMA_URL
from telegram_bot.logging_config import setup_logging
from telegram_bot.infrastructure.redis_session_store import RedisSessionStore
from telegram_bot.infrastructure.pqrs_api_client import PqrsApiClient
from telegram_bot.infrastructure.ollama_client import OllamaClient
from telegram_bot.application import command_handlers as ch
from telegram_bot.application.conversation_handlers import (
    build_ingreso_conversation,
    init_conversation_handlers,
)

setup_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    validate()

    store = RedisSessionStore(REDIS_URL)
    api = PqrsApiClient(PQRS_API_URL)
    ollama = OllamaClient(OLLAMA_URL)

    ch.init_handlers(store, api, ollama)
    init_conversation_handlers(store, api)

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversación /nueva_pqrs (debe registrarse antes que los handlers genéricos)
    app.add_handler(build_ingreso_conversation())

    # Comandos
    app.add_handler(CommandHandler("start", ch.start_handler))
    app.add_handler(CommandHandler("pqrs", ch.pqrs_handler))
    app.add_handler(CommandHandler("pendientes", ch.pendientes_handler))
    app.add_handler(CommandHandler("metricas", ch.metricas_handler))
    app.add_handler(CommandHandler("secretarias", ch.secretarias_handler))
    app.add_handler(CommandHandler("secretaria", ch.secretaria_handler))
    app.add_handler(CommandHandler("alertas", ch.alertas_handler))
    app.add_handler(CommandHandler("nueva_consulta", ch.nueva_consulta_handler))
    app.add_handler(CommandHandler("cancelar", ch.cancelar_handler))

    # Callbacks inline
    app.add_handler(CallbackQueryHandler(ch.rol_callback_handler, pattern="^rol:"))
    app.add_handler(CallbackQueryHandler(ch.pendientes_page_callback, pattern="^pendientes:"))

    # Fallback — texto libre → asistente IA
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ch.fallback_handler))

    logger.info("Bot @AlcaldiaMedellinPQRSD_bot iniciado en modo polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
