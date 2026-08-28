#!/usr/bin/env python3
"""Turn the CSM dashboard CSV (team chat requests) into a second KB category.

The CSV is a log of operational requests from brand/affiliate teams to the AMP
platform team. It is internal material: it carries partner ids, emails, brand
domains, Jira keys and people's chat handles. This script strips those and
writes one redacted case per file into the knowledge base, flagged internal so
the bot uses them as background — never as something to quote at a client.

    python3 ingest_cases.py "~/Downloads/CSM DASHBOARD"*.csv

Handles every export variant seen so far: the column names drift between
monthly and quarterly sheets, and the quarterly "All" sheets repeat the months
they cover, so identical requests are de-duplicated by question text.

The source CSVs are never copied into the project.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import sys
from typing import Dict, Iterable, List, Optional, Tuple

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kb-uk", "team-cases")

# Handles belonging to the platform side of the conversation.
PLATFORM_HANDLES = {"skylight", "amp", "frost", "raskolnikov", "iskrynka",
                    "cania710", "vel", "hope"}

# The export's column names drift between sheets; map every variant we've seen.
COLUMNS = {
    "date": ("Дата",),
    "team": ("Чат команди", "Команда"),
    "category": ("Категорія",),
    "kind": ("Тип запиту",),
    "question": ("Питання",),
    "answer": ("Відповідь",),
    "status": ("Статус (якщо баг)", "Статус"),
    "task": ("Задача",),
}

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
    text = re.sub(r"(?<!\d)\d{5,}(?!\d)", "[id]", text)
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


def field(row: Dict[str, str], key: str, fieldnames: Tuple[str, ...]) -> str:
    """Read a logical column whatever this sheet happens to call it."""
    for name in COLUMNS[key]:
        value = (row.get(name) or "").strip()
        if value:
            return value
    # a few sheets ship the date in an unnamed leading column
    if key == "date" and fieldnames and fieldnames[0] == "":
        return (row.get("") or "").strip()
    return ""


def parse_date(raw: str) -> Optional[Tuple[int, int, int]]:
    """`10/8/26` → (2026, 8, 10). Day first, as the exports are written."""
    m = re.match(r"^\s*(\d{1,2})[/.](\d{1,2})[/.](\d{2,4})\s*$", raw)
    if not m:
        return None
    day, month, year = (int(g) for g in m.groups())
    if year < 100:
        year += 2000
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    return (year, month, day)


def read_rows(paths: Iterable[str]) -> List[Dict[str, str]]:
    """Load every sheet into one list of logical rows, de-duplicated.

    The quarterly "All" sheets repeat the monthly ones, so the same request
    shows up more than once; keep the first occurrence of each question.
    """
    seen: Dict[str, str] = {}
    collected: List[Dict[str, str]] = []
    for path in paths:
        try:
            with open(path, encoding="utf-8-sig", newline="") as fh:
                reader = csv.DictReader(fh)
                fieldnames = tuple(reader.fieldnames or ())
                rows = list(reader)
        except OSError as exc:
            print(f"skip {path}: {exc}", file=sys.stderr)
            continue

        source = os.path.basename(path)
        for row in rows:
            question = field(row, "question", fieldnames)
            if not question:
                continue
            key = hashlib.md5(re.sub(r"\s+", " ", question.lower()).encode()).hexdigest()
            if key in seen:
                continue
            seen[key] = source
            collected.append({
                "question": question,
                "answer": field(row, "answer", fieldnames),
                "category": field(row, "category", fieldnames),
                "kind": field(row, "kind", fieldnames),
                "status": field(row, "status", fieldnames),
                "task": field(row, "task", fieldnames),
                "date": field(row, "date", fieldnames),
                "source": source,
                "key": key,
            })
    return collected


def convert(paths: List[str], out_dir: str) -> int:
    rows = read_rows(paths)
    if not rows:
        print("no rows with a question found", file=sys.stderr)
        return 1

    os.makedirs(out_dir, exist_ok=True)
    for name in os.listdir(out_dir):
        if name.endswith(".md"):
            os.remove(os.path.join(out_dir, name))

    handles = collect_handles([{"Питання": r["question"], "Відповідь": r["answer"]}
                               for r in rows])

    # newest first — recent cases describe the platform as it is now
    rows.sort(key=lambda r: parse_date(r["date"]) or (0, 0, 0), reverse=True)

    written: List[Dict[str, str]] = []
    for i, row in enumerate(rows, start=1):
        question = clean_dialogue(row["question"], handles)
        answer = clean_dialogue(row["answer"], handles)
        if not question.strip():
            continue

        category = row["category"] or "Інше"
        parsed = parse_date(row["date"])
        stamp = "%04d-%02d" % parsed[:2] if parsed else "undated"
        slug = f"case-{stamp}-{row['key'][:6]}"

        title = make_title(question, category, i)
        extra = [row["kind"], row["date"]]
        if row["status"]:
            extra.append(f"статус: {row['status']}")
        if row["task"]:
            extra.append(f"задача: {row['task']}")
        summary = make_summary(question, extra)

        body = [
            "> ВНУТРІШНІЙ КЕЙС. Робоче листування команд з платформою AMP.",
            "> Використовувати як контекст; не цитувати клієнту й не переказувати",
            "> як офіційну інструкцію — офіційне джерело це статті довідкового центру.",
            "",
            "## Запит",
            question,
            "",
            "## Відповідь платформи",
            answer if answer.strip() else "(у вивантаженні відповіді немає)",
        ]
        head = [
            f"# {title}",
            "Category: team-cases",
            f"Section: {category}",
            f"Summary: {summary}",
        ]
        with open(os.path.join(out_dir, slug + ".md"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(head) + "\n\n" + "\n".join(body).strip() + "\n")
        written.append({"slug": slug, "section": category, "date": row["date"]})

    # Compact index: with thousands of cases the per-case list would blow up the
    # model's system prompt, so the catalog carries counts and search finds the rest.
    sections: Dict[str, int] = {}
    for case in written:
        sections[case["section"]] = sections.get(case["section"], 0) + 1
    index = [
        "# 🗂 Кейси з робочих чатів (внутрішнє)",
        "Summary: Реальні звернення команд до платформи AMP і відповіді платформи. "
        "Внутрішній контекст: не цитувати клієнту. Шукати через kb_search — "
        "перелік кейсів у каталог не виводиться.",
        "",
        f"{len(written)} кейсів за темами:",
        "",
    ]
    for section, count in sorted(sections.items(), key=lambda kv: -kv[1]):
        index.append(f"- {section} — {count}")
    with open(os.path.join(out_dir, "_index.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(index).strip() + "\n")

    print(f"wrote {len(written)} cases to {out_dir}/ "
          f"(from {len(paths)} files, duplicates dropped)", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="+", help="CSM dashboard CSV exports")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output directory")
    args = ap.parse_args()
    return convert([os.path.expanduser(p) for p in args.csv], args.out)


if __name__ == "__main__":
    sys.exit(main())
