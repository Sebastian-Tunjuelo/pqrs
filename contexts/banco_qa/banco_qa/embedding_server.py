"""Microservicio mínimo HTTP: POST /embed {\"text\":\"...\"} -> {\"embedding\":[384 floats]}.

Ejecutar (tras `pip install -e \"contexts/banco_qa[embedding]\"`):
  python -m banco_qa.embedding_server
"""

from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

from banco_qa.infrastructure.embedding import embed_text

logger = logging.getLogger(__name__)


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        logger.info(fmt, *args)

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path != "/embed":
            self.send_response(404)
            self.end_headers()
            return
        try:
            ln = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            ln = 0
        raw = self.rfile.read(ln) if ln > 0 else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._reply(400, {"error": "JSON inválido"})
            return
        text = (body.get("text") or "").strip()
        if not text:
            self._reply(400, {"error": "text vacío"})
            return
        try:
            emb = embed_text(text)
        except Exception as exc:  # noqa: BLE001
            logger.exception("embed")
            self._reply(500, {"error": str(exc)})
            return
        self._reply(200, {"embedding": emb})

    def _reply(self, code: int, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main(host: str = "0.0.0.0", port: int = 8765) -> None:
    logging.basicConfig(level=logging.INFO)
    httpd = HTTPServer((host, port), _Handler)
    logger.info("embedding_server en http://%s:%s (POST /embed)", host, port)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
