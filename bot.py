#!/usr/bin/env python3
"""Support bot over the aff.ltd help center.

The agent loop: the catalog of all 68 articles sits in the (cached) system
prompt as a router, and the model pulls whole articles on demand with the same
tools the MCP server exposes — so the bot and a human using Claude Code see
exactly the same knowledge base.

Run standalone for a terminal chat:
    .venv/bin/python bot.py
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, Iterator, List, Optional

import anthropic

from kb import get_kb
from kb_mcp import HANDLERS, TOOLS

MODEL = os.environ.get("AFF_BOT_MODEL", "claude-opus-4-8")
EFFORT = os.environ.get("AFF_BOT_EFFORT", "medium")  # low | medium | high | xhigh | max
MAX_TOKENS = int(os.environ.get("AFF_BOT_MAX_TOKENS", "16000"))
MAX_TOOL_ROUNDS = 8

# One source of truth for the persona: the same file the /aff-support slash
# command loads, so the bot and Claude Code behave identically.
PROMPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "support_prompt.md")

with open(PROMPT_PATH, encoding="utf-8") as _fh:
    INSTRUCTIONS = _fh.read()


def _anthropic_tools() -> List[Dict[str, Any]]:
    """Same tool contract as the MCP server, in Messages API shape."""
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": tool["inputSchema"],
        }
        for tool in TOOLS
    ]


class SupportBot:
    def __init__(self, model: str = MODEL, effort: str = EFFORT):
        self.client = anthropic.Anthropic()
        self.model = model
        self.effort = effort
        self.kb = get_kb()
        self.tools = _anthropic_tools()

    # -- prompt ------------------------------------------------------------- #
    def system_blocks(self) -> List[Dict[str, Any]]:
        # Stable prefix first, cache breakpoint on the last block: tools +
        # instructions + catalog are all cached together (~10k tokens).
        return [
            {"type": "text", "text": INSTRUCTIONS},
            {
                "type": "text",
                "text": "# Help center catalog\n\n" + self.kb.catalog(),
                "cache_control": {"type": "ephemeral"},
            },
        ]

    # -- agent loop --------------------------------------------------------- #
    def stream(self, messages: List[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
        """Run one turn, yielding UI events. `messages` is mutated in place."""
        for _ in range(MAX_TOOL_ROUNDS):
            with self.client.messages.stream(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=self.system_blocks(),
                messages=messages,
                tools=self.tools,
                thinking={"type": "adaptive"},
                output_config={"effort": self.effort},
            ) as stream:
                for event in stream:
                    if event.type == "content_block_delta" and event.delta.type == "text_delta":
                        yield {"type": "text", "text": event.delta.text}
                final = stream.get_final_message()

            # Keep the full content back in history — thinking blocks included.
            messages.append({"role": "assistant", "content": final.content})

            if final.stop_reason == "refusal":
                yield {"type": "error", "text": "Модель відхилила запит."}
                return
            if final.stop_reason != "tool_use":
                yield {"type": "done", "usage": _usage(final)}
                return

            results = []
            for block in final.content:
                if block.type != "tool_use":
                    continue
                yield {"type": "tool", "name": block.name, "input": block.input}
                handler = HANDLERS.get(block.name)
                if handler is None:
                    text, is_error = f"Unknown tool: {block.name}", True
                else:
                    try:
                        text, is_error = handler(dict(block.input)), False
                    except Exception as exc:  # noqa: BLE001 — feed it back to the model
                        text, is_error = f"Tool failed: {exc}", True
                yield {"type": "tool_result", "name": block.name,
                       "chars": len(text), "is_error": is_error}
                result: Dict[str, Any] = {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": text,
                }
                if is_error:
                    result["is_error"] = True
                results.append(result)
            messages.append({"role": "user", "content": results})

        yield {"type": "error", "text": "Забагато кроків пошуку — спробуйте переформулювати."}


def _usage(message: Any) -> Dict[str, int]:
    usage = message.usage
    return {
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cache_read": getattr(usage, "cache_read_input_tokens", 0) or 0,
        "cache_write": getattr(usage, "cache_creation_input_tokens", 0) or 0,
    }


def main() -> int:
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        print("Set ANTHROPIC_API_KEY first.", file=sys.stderr)
        return 1
    bot = SupportBot()
    print(f"KB: {len(bot.kb.articles)} статей · модель {bot.model} · Ctrl-C для виходу\n")
    messages: List[Dict[str, Any]] = []
    while True:
        try:
            user = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            return 0
        if not user:
            continue
        messages.append({"role": "user", "content": user})
        print()
        for event in bot.stream(messages):
            if event["type"] == "text":
                sys.stdout.write(event["text"])
                sys.stdout.flush()
            elif event["type"] == "tool":
                print(f"\n  [{event['name']}: {event['input']}]")
            elif event["type"] == "done":
                u = event["usage"]
                print(f"\n\n  ({u['input_tokens']} in / {u['output_tokens']} out, "
                      f"cache read {u['cache_read']})")
            elif event["type"] == "error":
                print(f"\n  ! {event['text']}")


if __name__ == "__main__":
    sys.exit(main())
