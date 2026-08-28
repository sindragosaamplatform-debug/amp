#!/usr/bin/env python3
"""MCP server exposing the help.aff.ltd knowledge base.

Speaks MCP over stdio (JSON-RPC 2.0, newline-delimited). Implemented against
the wire protocol with the standard library only, because the official MCP SDK
requires Python 3.10+ and this machine ships 3.9.

Tools:
    kb_search(query, limit, category)  — find relevant articles
    kb_get_article(article_id, lang)   — read one article in full
    kb_list(category)                  — browse the catalog

Register it with Claude Code / any MCP client as:
    command: /path/to/.venv/bin/python
    args:    ["/path/to/kb_mcp.py"]
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, Optional

from kb import INTERNAL_CATEGORIES, LANGUAGES, get_kb

SERVER_NAME = "aff-kb"
SERVER_VERSION = "0.1.0"
SUPPORTED_PROTOCOLS = ("2025-06-18", "2025-03-26", "2024-11-05")

TOOLS = [
    {
        "name": "kb_search",
        "description": (
            "Search the aff.ltd knowledge base. It holds two kinds of entries: "
            "help-center articles (admin-panel, aff-area, additional-resources) "
            "and `team-cases` — redacted logs of real requests teams sent the "
            "platform, which are INTERNAL background, never quotable to a "
            "partner. Use it when the catalog does not obviously name the right "
            "article, or to find where a specific term (a button, a GET "
            "parameter, a status) is documented. Returns ids, titles, summaries "
            "and matching excerpts."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search terms, any language."},
                "limit": {"type": "integer", "description": "Max results (default 5)."},
                "category": {
                    "type": "string",
                    "description": "Restrict to one category: admin-panel, aff-area, additional-resources, team-cases.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "kb_get_article",
        "description": (
            "Read one entry in full, by id (e.g. 'aff-area/balance' or "
            "'team-cases/case-03'). Always read the whole article before walking "
            "a user through a procedure — the steps are numbered and must not be "
            "guessed at. Entries from `team-cases` come with an internal-use "
            "banner: honour it."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "article_id": {"type": "string", "description": "Article id: '<category>/<slug>'."},
                "lang": {
                    "type": "string",
                    "enum": list(LANGUAGES),
                    "description": "Locale for the returned help-center link (default uk).",
                },
            },
            "required": ["article_id"],
        },
    },
    {
        "name": "kb_list",
        "description": (
            "List the catalog: every article id, title and summary, grouped by "
            "category and section. Useful for orientation."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Optional category filter.",
                },
            },
        },
    },
]


# --------------------------------------------------------------------------- #
# tool implementations
# --------------------------------------------------------------------------- #
MIN_HELP_CENTER_HITS = 2


def tool_kb_search(args: Dict[str, Any]) -> str:
    kb = get_kb()
    query = args.get("query", "")
    limit = int(args.get("limit") or 5)
    category = args.get("category")
    results = kb.search(query, limit=limit, category=category)

    # There are far more chat cases than articles, so a plain top-N can come
    # back all-cases. Keep a couple of slots for the citable source.
    if not category:
        found = sum(1 for r in results if r["category"] not in INTERNAL_CATEGORIES)
        if found < MIN_HELP_CENTER_HITS:
            top_up = kb.search(query, limit=MIN_HELP_CENTER_HITS, exclude_internal=True)
            have = {r["id"] for r in results}
            extra = [r for r in top_up if r["id"] not in have]
            if extra:
                results = (results[:max(0, limit - len(extra))] + extra)
                results.sort(key=lambda r: -r["score"])
    if not results:
        return "No matching articles. Try different wording or call kb_list."
    out = []
    for r in results:
        flag = "  [ВНУТРІШНЄ — не цитувати клієнту]\n" if r["category"] in INTERNAL_CATEGORIES else ""
        out.append(
            flag +
            f"{r['id']} — {r['title']}\n"
            f"  section: {r['category']} / {r['section']}\n"
            f"  summary: {r['summary']}\n"
            f"  url: {r['url']}\n"
            f"  excerpt: {r['excerpt']}"
        )
    return "\n\n".join(out)


def tool_kb_get_article(args: Dict[str, Any]) -> str:
    kb = get_kb()
    article = kb.get(args.get("article_id", ""))
    if article is None:
        return (
            f"No article with id {args.get('article_id')!r}. "
            "Call kb_search or kb_list to find the right id."
        )
    return article.render(lang=args.get("lang") or "uk")


def tool_kb_list(args: Dict[str, Any]) -> str:
    kb = get_kb()
    category = args.get("category")
    if category and category not in kb.categories:
        return f"Unknown category {category!r}. Known: {', '.join(kb.categories)}"
    catalog = kb.catalog()
    if not category:
        return catalog
    blocks = catalog.split("\n## ")
    for block in blocks:
        if f"[{category}]" in block.splitlines()[0]:
            return "## " + block.strip()
    return catalog


HANDLERS = {
    "kb_search": tool_kb_search,
    "kb_get_article": tool_kb_get_article,
    "kb_list": tool_kb_list,
}


# --------------------------------------------------------------------------- #
# JSON-RPC / MCP plumbing
# --------------------------------------------------------------------------- #
def _result(request_id: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle(message: dict) -> Optional[dict]:
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}

    if method == "initialize":
        requested = params.get("protocolVersion")
        version = requested if requested in SUPPORTED_PROTOCOLS else SUPPORTED_PROTOCOLS[0]
        kb = get_kb()
        return _result(request_id, {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            "instructions": (
                f"Knowledge base of the aff.ltd help center: {len(kb.articles)} "
                f"articles across {', '.join(kb.categories)}. Search or list to "
                "find an article id, then read it in full before answering."
            ),
        })

    if method in ("notifications/initialized", "notifications/cancelled"):
        return None  # notifications get no response

    if method == "ping":
        return _result(request_id, {})

    if method == "tools/list":
        return _result(request_id, {"tools": TOOLS})

    if method == "tools/call":
        name = params.get("name")
        handler = HANDLERS.get(name)
        if handler is None:
            return _result(request_id, {
                "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
                "isError": True,
            })
        try:
            text = handler(params.get("arguments") or {})
            return _result(request_id, {"content": [{"type": "text", "text": text}]})
        except Exception as exc:  # noqa: BLE001 — report to the client, keep serving
            return _result(request_id, {
                "content": [{"type": "text", "text": f"Tool failed: {exc}"}],
                "isError": True,
            })

    if request_id is None:
        return None
    return _error(request_id, -32601, f"Method not found: {method}")


def main() -> int:
    get_kb()  # fail fast if the corpus is missing
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle(message)
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
