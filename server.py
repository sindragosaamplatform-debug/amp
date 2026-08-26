#!/usr/bin/env python3
"""Proof-of-concept web UI for the aff.ltd support bot.

Serves a small chat page and streams the agent's answer over SSE, so you can
watch it route through the knowledge base in real time.

    export ANTHROPIC_API_KEY=...
    .venv/bin/python server.py            # http://127.0.0.1:8765
"""

from __future__ import annotations

import json
import os
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List

from bot import SupportBot

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")
HOST = os.environ.get("AFF_BOT_HOST", "127.0.0.1")
PORT = int(os.environ.get("AFF_BOT_PORT", "8765"))

_bot: SupportBot = None  # type: ignore[assignment]  — set in main()
_sessions: Dict[str, List[Dict[str, Any]]] = {}
_lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    server_version = "aff-support-poc"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    # -- routing ------------------------------------------------------------ #
    def do_GET(self) -> None:  # noqa: N802 — BaseHTTPRequestHandler API
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            return self._send_file(os.path.join(STATIC, "index.html"), "text/html; charset=utf-8")
        if path == "/api/kb":
            return self._send_json(_bot.kb.stats())
        if path.startswith("/static/"):
            name = os.path.basename(path)
            candidate = os.path.join(STATIC, name)
            if os.path.isfile(candidate):
                ctype = "text/css" if name.endswith(".css") else "application/javascript"
                return self._send_file(candidate, ctype)
        self.send_error(404, "Not found")

    def do_POST(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] != "/api/chat":
            return self.send_error(404, "Not found")
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return self.send_error(400, "Bad JSON")

        message = (payload.get("message") or "").strip()
        if not message:
            return self.send_error(400, "Empty message")
        session_id = payload.get("session_id") or uuid.uuid4().hex

        with _lock:
            history = _sessions.setdefault(session_id, [])
        history.append({"role": "user", "content": message})

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        self._emit({"type": "session", "session_id": session_id})

        try:
            for event in _bot.stream(history):
                self._emit(event)
        except BrokenPipeError:
            return  # client navigated away mid-answer
        except Exception as exc:  # noqa: BLE001 — surface it in the UI
            self._emit({"type": "error", "text": f"{type(exc).__name__}: {exc}"})
        self._emit({"type": "end"})

    # -- helpers ------------------------------------------------------------ #
    def _emit(self, event: Dict[str, Any]) -> None:
        self.wfile.write(("data: " + json.dumps(event, ensure_ascii=False) + "\n\n").encode())
        self.wfile.flush()

    def _send_json(self, data: Any) -> None:
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: str, ctype: str) -> None:
        if not os.path.isfile(path):
            return self.send_error(404, "Not found")
        with open(path, "rb") as fh:
            body = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    global _bot
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        print("Set ANTHROPIC_API_KEY before starting the server.", file=sys.stderr)
        return 1
    _bot = SupportBot()
    stats = _bot.kb.stats()
    print(f"KB: {stats['articles']} articles {stats['categories']}")
    print(f"Model: {_bot.model} (effort={_bot.effort})")
    print(f"Listening on http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
