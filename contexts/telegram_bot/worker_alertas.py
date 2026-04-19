"""Worker de alertas SLA — proceso independiente."""
import asyncio
import logging

from telegram import Bot

from telegram_bot.config import validate, TELEGRAM_BOT_TOKEN, PQRS_API_URL, REDIS_URL
from telegram_bot.logging_config import setup_logging
from telegram_bot.infrastructure.redis_session_store import RedisSessionStore
from telegram_bot.infrastructure.pqrs_api_client import PqrsApiClient
from telegram_bot.application.alerta_scheduler import run_forever

setup_logging()
logger = logging.getLogger(__name__)


async def main() -> None:
    validate()
    store = RedisSessionStore(REDIS_URL)
    api = PqrsApiClient(PQRS_API_URL)
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    logger.info("Iniciando worker de alertas...")
    await run_forever(bot, store, api)


if __name__ == "__main__":
    asyncio.run(main())
