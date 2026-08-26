#!/usr/bin/env python3
"""ASGI entrypoint — the app Vercel runs, and the one to run locally.

Vercel's Python runtime loads the `app` variable from this file. Everything is
stateless: the browser holds the conversation and posts it back each turn, so
any instance can serve any request.

Local:
    export ANTHROPIC_API_KEY=...
    .venv/bin/python -m uvicorn app:app --reload --port 8765
"""

from __future__ import annotations

import hmac
import json
import os
from typing import Any, Dict, Iterator, List

from fastapi import Cookie, FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from bot import SupportBot

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")

# Set ACCESS_CODE in the Vercel project to put the bot behind a shared code.
# Left unset (local dev) the app is open.
ACCESS_CODE = os.environ.get("ACCESS_CODE", "")
COOKIE = "aff_access"

# The browser sends the whole conversation back; cap it so a long session
# cannot grow past the 4.5 MB request-body limit (or quietly cost a fortune).
MAX_HISTORY_MESSAGES = 30

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

# Built once per cold start: loads the knowledge base and the Anthropic client.
_bot = SupportBot()


# --------------------------------------------------------------------------- #
# access gate
# --------------------------------------------------------------------------- #
def authorised(code: str) -> bool:
    if not ACCESS_CODE:
        return True
    return bool(code) and hmac.compare_digest(code, ACCESS_CODE)


def _page(name: str) -> str:
    with open(os.path.join(STATIC, name), encoding="utf-8") as fh:
        return fh.read()


@app.get("/", response_class=HTMLResponse)
def index(aff_access: str = Cookie(default="")) -> HTMLResponse:
    if not authorised(aff_access):
        return HTMLResponse(_page("login.html"), status_code=401)
    return HTMLResponse(_page("index.html"))


@app.post("/api/login")
async def login(request: Request) -> Response:
    payload = await request.json()
    code = (payload or {}).get("code", "")
    if not authorised(code):
        return JSONResponse({"error": "invalid code"}, status_code=401)
    response = JSONResponse({"ok": True})
    response.set_cookie(
        COOKIE, code,
        httponly=True, samesite="lax",
        secure=bool(os.environ.get("VERCEL")),  # https in production only
        max_age=60 * 60 * 24 * 30,
    )
    return response


@app.get("/api/kb")
def kb_stats(aff_access: str = Cookie(default="")) -> Response:
    if not authorised(aff_access):
        return JSONResponse({"error": "unauthorised"}, status_code=401)
    return JSONResponse(_bot.kb.stats())


# --------------------------------------------------------------------------- #
# chat
# --------------------------------------------------------------------------- #
def serialise(messages: List[Any]) -> List[Dict[str, Any]]:
    """Make the turn JSON-safe: SDK content blocks become plain dicts.

    Thinking and tool_use blocks have to survive the round trip — the model
    needs them back verbatim to continue a tool call.
    """
    out = []
    for message in messages:
        content = message["content"]
        if isinstance(content, list):
            content = [_block(block) for block in content]
        out.append({"role": message["role"], "content": content})
    return out


def _block(block: Any) -> Any:
    if not hasattr(block, "model_dump"):
        return block
    # drop nulls: the SDK fills in optional fields the API does not accept back
    return {k: v for k, v in block.model_dump().items() if v is not None}


def sse(event: Dict[str, Any]) -> str:
    return "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"


@app.post("/api/chat")
async def chat(request: Request, aff_access: str = Cookie(default="")) -> Response:
    if not authorised(aff_access):
        return JSONResponse({"error": "unauthorised"}, status_code=401)

    payload = await request.json()
    message = (payload.get("message") or "").strip()
    if not message:
        return JSONResponse({"error": "empty message"}, status_code=400)

    history: List[Dict[str, Any]] = payload.get("messages") or []
    if len(history) > MAX_HISTORY_MESSAGES:
        history = history[-MAX_HISTORY_MESSAGES:]
    history.append({"role": "user", "content": message})

    def stream() -> Iterator[str]:
        try:
            for event in _bot.stream(history):
                yield sse(event)
        except Exception as exc:  # noqa: BLE001 — surface it in the UI
            yield sse({"type": "error", "text": f"{type(exc).__name__}: {exc}"})
        # hand the conversation back to the browser — it is the only store
        yield sse({"type": "history", "messages": serialise(history)})
        yield sse({"type": "end"})

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
