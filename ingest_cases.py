#!/usr/bin/env python3
"""Turn the CSM dashboard CSV (team chat requests) into a second KB category.

The CSV is a log of operational requests from brand/affiliate teams to the AMP
platform team. It is internal material: it carries partner ids, emails, brand
domains, Jira keys and people's chat handles. This script strips those and
writes one redacted case per file into the knowledge base, flagged internal so
the bot uses them as background — never as something to quote at a client.

    python3 ingest_cases.py "~/Downloads/CSM DASHBOARD ... .csv"

The source CSV is never copied into the project.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from typing import Dict, List

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kb-uk", "team-cases")

# Handles belonging to the platform side of the conversation.
PLATFORM_HANDLES = {"skylight", "amp", "frost"}

HANDLE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.\-]{1,19}$")

# Telegram/Slack exports put the author on its own line with a timestamp:
#   "Kateryna Dud [7:47 PM]"   "Валерія, [05.08.2026 16:33]"
# Those are real names — always a speaker line, never content.
TIMESTAMPED_SPEAKER_RE = re.compile(
    r"^(?P<who>.{1,40}?)\s*,?\s*\[\s*\d{1,2}[.:]\d{2}(?:[.:]\d{2,4})?"
    r"(?:\s+\d{1,2}:\d{2})?\s*(?:AM|PM)?\s*\]\s*:?$", re.I)

# "nicky: далі текст" — author glued to the start of a content line.
INLINE_SPEAKER_RE = re.compile(r"^(?P<who>[A-Za-z][\w.\-]{1,19}):\s+(?=\S)")

NOISE_RE = re.compile(
    r"^\s*(\d+\s+repl(y|ies)|media omitted|.*\.(png|jpg|jpeg|gif|pdf|mp4))\s*$", re.I)


def collect_handles(rows: List[Dict[str, str]]) -> set:
    """Work out which bare words are chat handles rather than content.

    A single word on its own line is a speaker if it opens a message block or
    recurs across cases — otherwise it is content (an answer like `click_id`
    looks exactly like a handle, and must not be eaten).
    """
    definite, counts = set(), {}
    for row in rows:
        for field in ("Питання", "Відповідь"):
            lines = [l.strip() for l in (row.get(field) or "").replace("\r", "").split("\n")]
            lines = [l for l in lines if l]
            if lines and HANDLE_RE.match(lines[0]):
                definite.add(lines[0].lower())
            for line in lines:
                if HANDLE_RE.match(line):
                    counts[line.lower()] = counts.get(line.lower(), 0) + 1
    return definite | {tok for tok, n in counts.items() if n >= 2}


def redact(text: str) -> str:
    """Strip identifiers that must never reach a partner-facing answer."""
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[email]", text)
    text = re.sub(r"https?://jira\.[^\s)]+", "[jira]", text)
    text = re.sub(r"\bAFF-\d+\b", "[jira]", text)
    # keep help-center and admin links, drop everything else
    text = re.sub(
        r"https?://(?!help\.aff\.ltd|aff\.ltd)[^\s)]+", "[посилання]", text)
    text = re.sub(r"\s*\[\s*\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?\s*\]", "", text, flags=re.I)
    text = re.sub(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", "[ip]", text)
    text = re.sub(r"(?<!\d)\d{5,8}(?!\d)", "[id]", text)
    return text


def clean_dialogue(text: str, handles: set) -> str:
    """Normalise a pasted chat block: drop noise, anonymise speakers."""
    out: List[str] = []
    for raw in text.replace("\r", "").split("\n"):
        line = raw.rstrip()
        if not line.strip():
            if out and out[-1] != "":
                out.append("")
            continue
        if NOISE_RE.match(line):
            continue
        stripped = line.strip()

        timestamped = TIMESTAMPED_SPEAKER_RE.match(stripped)
        who = None
        if timestamped:
            who = timestamped.group("who")
        elif stripped.lower() in handles:
            who = stripped
        if who is not None:
            speaker = "[AMP]" if who.strip().lower() in PLATFORM_HANDLES else "[команда]"
            if out and out[-1] != "":
                out.append("")
            out.append(f"{speaker}:")
            continue

        inline = INLINE_SPEAKER_RE.match(stripped)
        if inline:
            speaker = "[AMP]" if inline.group("who").lower() in PLATFORM_HANDLES else "[команда]"
            line = f"{speaker}: " + stripped[inline.end():]
        out.append(line)
    return redact("\n".join(out)).strip()


# Openers that carry no topic — a title made of these is useless for search.
_FILLER = (r"привіт|вітаю|доброго|добрий|доброї|хай|hi|hello|дякую|"
           r"підкажи(ть)?(\s+(ще|будь\s+ласка))*[\s,]*(питання)?|"
           r"я\s+перепрошую|пару\s+питань|ще\s+питання|питання")
FILLER_RE = re.compile(r"^(%s)\b[\s,.!)]*$" % _FILLER, re.I)
# A line that merely *opens* with pleasantries is still weak as a title.
FILLER_START_RE = re.compile(r"^(%s)\b" % _FILLER, re.I)


def question_lines(question: str) -> List[str]:
    """Content lines of the question, best-first for titling."""
    lines = []
    for line in question.split("\n"):
        line = re.sub(r"\s+", " ", line.strip(" :-—"))
        if len(line) < 15 or line.startswith("[") or line.startswith("http"):
            continue
        if FILLER_RE.match(line) or TIMESTAMPED_SPEAKER_RE.match(line):
            continue
        lines.append(line)
    return lines


def make_title(question: str, category: str, index: int) -> str:
    lines = question_lines(question)
    if not lines:
        return f"{category or 'Кейс'} #{index}"
    # prefer the line that actually states the problem, not a lead-in
    def weight(line: str) -> int:
        words = len(re.findall(r"[а-яіїєґa-z]{4,}", line, re.I))
        return words - (6 if FILLER_START_RE.match(line) else 0)

    best = max(lines[:4], key=weight)
    return (best[:95] + "…") if len(best) > 95 else best


def make_summary(question: str, extra: List[str], limit: int = 220) -> str:
    """Searchable gist of the request — cases have no editorial summary."""
    gist = " ".join(question_lines(question))[:limit].strip()
    parts = [p for p in extra if p]
    if gist:
        parts.append(gist + ("…" if len(gist) >= limit else ""))
    return " · ".join(parts) if parts else "внутрішній кейс"


def convert(csv_path: str, out_dir: str) -> int:
    with open(csv_path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        print("empty CSV", file=sys.stderr)
        return 1

    os.makedirs(out_dir, exist_ok=True)
    for name in os.listdir(out_dir):
        if name.endswith(".md"):
            os.remove(os.path.join(out_dir, name))

    handles = collect_handles(rows)
    written: List[Dict[str, str]] = []
    for i, row in enumerate(rows, start=1):
        question = clean_dialogue(row.get("Питання", ""), handles)
        answer = clean_dialogue(row.get("Відповідь", ""), handles)
        if not question.strip():
            continue
        category = (row.get("Категорія") or "").strip()
        kind = (row.get("Тип запиту") or "").strip()
        status = (row.get("Статус (якщо баг)") or "").strip()
        date = (row.get("Дата") or "").strip()
        title = make_title(question, category, i)

        summary = make_summary(question, [kind, date, f"статус: {status}" if status else ""])
        body = [
            "> ВНУТРІШНІЙ КЕЙС. Робоче листування команд з платформою AMP.",
            "> Використовувати як контекст; не цитувати клієнту й не переказувати",
            "> як офіційну інструкцію — офіційне джерело це статті довідкового центру.",
            "",
            "## Запит",
            question,
        ]
        if answer.strip():
            body += ["", "## Відповідь платформи", answer]
        else:
            body += ["", "## Відповідь платформи", "(у вивантаженні відповіді немає)"]

        slug = f"case-{i:02d}"
        head = [
            f"# {title}",
            "Category: team-cases",
            f"Section: {category or 'Інше'}",
            f"Summary: {summary}",
        ]
        with open(os.path.join(out_dir, slug + ".md"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(head) + "\n\n" + "\n".join(body).strip() + "\n")
        written.append({"slug": slug, "title": title, "section": category or "Інше",
                        "summary": summary})

    index = [
        "# 🗂 Кейси з робочих чатів (внутрішнє)",
        "Summary: Реальні запити команд до платформи AMP і відповіді платформи. "
        "Внутрішній контекст: не цитувати клієнту.",
        "",
        f"{len(written)} кейсів.",
        "",
    ]
    current = None
    for case in written:
        if case["section"] != current:
            current = case["section"]
            index += ["", f"## {current}"]
        index.append(f"- {case['slug']}.md — {case['title']}: {case['summary']}")
    with open(os.path.join(out_dir, "_index.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(index).strip() + "\n")

    print(f"wrote {len(written)} cases to {out_dir}/", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", help="path to the CSM dashboard CSV export")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output directory")
    args = ap.parse_args()
    return convert(os.path.expanduser(args.csv), args.out)


if __name__ == "__main__":
    sys.exit(main())
