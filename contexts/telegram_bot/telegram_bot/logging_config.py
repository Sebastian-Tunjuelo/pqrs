import hashlib, json, logging, sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "chat_id_hash": getattr(record, "chat_id_hash", ""),
            "command": getattr(record, "command", ""),
            "result": getattr(record, "result", ""),
            "duration_ms": getattr(record, "duration_ms", 0),
            "message": record.getMessage(),
        }
        return json.dumps(log, ensure_ascii=False)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logging.root.setLevel(logging.INFO)
    logging.root.handlers = [handler]


def hash_chat_id(chat_id: int) -> str:
    return hashlib.sha256(str(chat_id).encode()).hexdigest()[:16]
