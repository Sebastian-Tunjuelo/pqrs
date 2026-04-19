import os, sys
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_FUNCIONARIO_SECRET = os.getenv("TELEGRAM_FUNCIONARIO_SECRET", "")
PQRS_API_URL = os.getenv("PQRS_API_URL", "http://127.0.0.1:8080/api/v1")
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")


def validate():
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN no está definida", file=sys.stderr)
        sys.exit(1)
