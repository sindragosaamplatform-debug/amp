#!/usr/bin/env python3
"""Knowledge base over the scraped help.aff.ltd articles.

Loads the plain-text articles produced by scrape_help.py, builds a compact
catalog (the router that goes into the model's system prompt) and answers
lookups: keyword search and full-article retrieval.

Shared by the MCP server (kb_mcp.py) and the chat bot (bot.py) so both see
exactly the same corpus. Standard library only.
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Dict, Iterable, List, Optional

KB_ROOT = os.environ.get(
    "KB_ROOT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "kb-uk")
)

LANGUAGES = ("uk", "ru", "en")

# A single packed file loads far faster than thousands of small ones, which
# matters on serverless cold starts. Built by `python3 kb.py pack`; the corpus
# directories stay the source of truth.
PACK_NAME = "_pack.json"

# Categories that are internal working material, not publishable help-center
# content. Everything loaded from them is flagged so the model cannot mistake
# it for something it may quote at a partner.
INTERNAL_CATEGORIES = {"team-cases"}

INTERNAL_BANNER = (
    "!! ВНУТРІШНЄ ДЖЕРЕЛО — робоче листування команд, не довідковий центр. "
    "Використовуй як контекст (як проблема виглядає насправді, що вже відомо), "
    "але не цитуй клієнту, не давай як інструкцію і не згадуй ідентифікатори."
)

# Words too common in this corpus to be worth scoring.
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "you", "your",
    "як", "що", "для", "при", "або", "які", "цей", "той", "від", "над",
    "как", "что", "для", "при", "или", "этот", "тот", "все", "его",
}


class Article:
    __slots__ = ("category", "slug", "title", "summary", "section", "url", "body", "_index")

    def __init__(self, category, slug, title, summary, section, url, body):
        self.category = category
        self.slug = slug
        self.title = title
        self.summary = summary
        self.section = section
        self.url = url
        self.body = body
        self._index = _tokenize(" ".join([title, summary, section, body]))

    @property
    def id(self) -> str:
        """Stable identifier used by the tools, e.g. 'aff-area/balance'."""
        return f"{self.category}/{self.slug}"

    @property
    def internal(self) -> bool:
        return self.category in INTERNAL_CATEGORIES

    def render(self, lang: str = "uk") -> str:
        if self.internal:
            head = [INTERNAL_BANNER, "", f"# {self.title}", f"id: {self.id}"]
            if self.section:
                head.append(f"Section: {self.section}")
            if self.summary:
                head.append(f"Summary: {self.summary}")
            return "\n".join(head) + "\n\n" + self.body.strip() + "\n"
        head = [
            f"# {self.title}",
            f"id: {self.id}",
            f"URL: {localize(self.url, lang)}",
        ]
        if self.section:
            head.append(f"Section: {self.section}")
        if self.summary:
            head.append(f"Summary: {self.summary}")
        return "\n".join(head) + "\n\n" + self.body.strip() + "\n"


def _tokenize(text: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for word in re.findall(r"[0-9a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ_]+", text.lower()):
        if len(word) < 3 or word in STOPWORDS:
            continue
        counts[word] = counts.get(word, 0) + 1
    return counts


def _stem(word: str) -> str:
    """Crude stem: enough to match Ukrainian/Russian case endings.

    Five characters, not six: `списувати` and `списання` share only `списа`-
    worth of root, and a longer stem silently loses that match.
    """
    return word[:5] if len(word) > 5 else word


def localize(url: str, lang: str) -> str:
    """Swap the locale segment of a help.aff.ltd URL (paths are identical)."""
    if lang not in LANGUAGES:
        return url
    return re.sub(r"(https://help\.aff\.ltd)/(uk|ru|en)/", r"\1/%s/" % lang, url)


class KnowledgeBase:
    def __init__(self, root: str = KB_ROOT):
        self.root = root
        self.articles: Dict[str, Article] = {}
        self.categories: Dict[str, dict] = {}
        self.source = "directories"
        self._load()

    # -- loading ------------------------------------------------------------ #
    def _load(self) -> None:
        if not os.path.isdir(self.root):
            raise RuntimeError(
                f"knowledge base not found at {self.root} — run scrape_help.py first"
            )
        if self._load_pack():
            return
        for category in sorted(os.listdir(self.root)):
            cat_dir = os.path.join(self.root, category)
            if not os.path.isdir(cat_dir):
                continue
            index_path = os.path.join(cat_dir, "_index.md")
            self.categories[category] = _parse_index(index_path, category)
            for name in sorted(os.listdir(cat_dir)):
                if not name.endswith(".md") or name.startswith("_"):
                    continue
                article = _parse_article(os.path.join(cat_dir, name), category)
                self.articles[article.id] = article
        if not self.articles:
            raise RuntimeError(f"no articles found under {self.root}")

    def _load_pack(self) -> bool:
        """Load the packed corpus if one was built. Returns False to fall back."""
        path = os.path.join(self.root, PACK_NAME)
        if not os.path.isfile(path):
            return False
        with open(path, encoding="utf-8") as fh:
            pack = json.load(fh)
        self.categories = pack["categories"]
        self.packed_at = pack.get("generated_at", "")
        for row in pack["articles"]:
            article = Article(row["category"], row["slug"], row["title"],
                              row["summary"], row["section"], row["url"], row["body"])
            self.articles[article.id] = article
        self.source = PACK_NAME
        return bool(self.articles)

    def pack(self) -> str:
        """Write the corpus into one file for fast start-up."""
        path = os.path.join(self.root, PACK_NAME)
        payload = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "categories": self.categories,
            "articles": [
                {"category": a.category, "slug": a.slug, "title": a.title,
                 "summary": a.summary, "section": a.section, "url": a.url,
                 "body": a.body}
                for a in self.articles.values()
            ],
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False)
        return path

    # -- lookups ------------------------------------------------------------ #
    def get(self, article_id: str) -> Optional[Article]:
        article = self.articles.get(article_id)
        if article is not None:
            return article
        # tolerate a bare slug when it is unambiguous
        matches = [a for a in self.articles.values() if a.slug == article_id.strip("/")]
        return matches[0] if len(matches) == 1 else None

    def search(self, query: str, limit: int = 5, category: Optional[str] = None,
               exclude_internal: bool = False) -> List[dict]:
        terms = [_stem(w) for w in _tokenize(query)]
        if not terms:
            return []
        scored = []
        for article in self.articles.values():
            if category and article.category != category:
                continue
            if exclude_internal and article.internal:
                continue
            score = 0.0
            hits = 0
            for term in terms:
                title_hit = term in _stem_join(article.title)
                summary_hit = term in _stem_join(article.summary + " " + article.section)
                body_hits = sum(c for w, c in article._index.items() if w.startswith(term))
                if title_hit:
                    score += 12
                if summary_hit:
                    score += 6
                if body_hits:
                    score += min(body_hits, 12)
                if title_hit or summary_hit or body_hits:
                    hits += 1
            if not hits:
                continue
            # reward articles that match several distinct query terms
            score *= 1 + 0.5 * (hits - 1)
            scored.append((score, article))
        scored.sort(key=lambda pair: (-pair[0], pair[1].id))
        return [
            {
                "id": a.id,
                "title": a.title,
                "summary": a.summary,
                "section": a.section,
                "category": a.category,
                "url": a.url,
                "score": round(s, 1),
                "excerpt": _excerpt(a, terms),
            }
            for s, a in scored[:limit]
        ]

    def catalog(self, lang: str = "uk") -> str:
        """Compact routing index — goes into the system prompt, cached."""
        lines: List[str] = []
        for category, meta in self.categories.items():
            mark = " — ВНУТРІШНЄ, не для цитування клієнту" if category in INTERNAL_CATEGORIES else ""
            lines.append(f"## {meta['title']} [{category}]{mark}")
            if meta.get("summary"):
                lines.append(meta["summary"])

            # Internal categories hold thousands of chat cases — listing each one
            # would bury the help-center articles and blow up the system prompt.
            # The catalog carries counts by topic; kb_search reaches the rest.
            if category in INTERNAL_CATEGORIES:
                counts: Dict[str, int] = {}
                for article in self.articles.values():
                    if article.category == category:
                        counts[article.section or "Інше"] = counts.get(
                            article.section or "Інше", 0) + 1
                total = sum(counts.values())
                lines.append(f"{total} кейсів; шукати через kb_search "
                             f"(category=\"{category}\"). Теми:")
                for section, count in sorted(counts.items(), key=lambda kv: -kv[1]):
                    lines.append(f"- {section} — {count}")
                lines.append("")
                continue

            current = None
            for article in self.articles.values():
                if article.category != category:
                    continue
                if article.section != current:
                    current = article.section
                    lines.append(f"### {current or 'Інше'}")
                summary = article.summary.replace("\n", " ")
                lines.append(f"- {article.id} — {article.title}: {summary}")
            lines.append("")
        return "\n".join(lines).strip()

    def stats(self) -> dict:
        return {
            "root": self.root,
            "source": getattr(self, "source", "directories"),
            "packed_at": getattr(self, "packed_at", ""),
            "articles": len(self.articles),
            "categories": {c: sum(1 for a in self.articles.values() if a.category == c)
                           for c in self.categories},
        }


def _stem_join(text: str) -> str:
    return " ".join(_stem(w) for w in _tokenize(text))


def _excerpt(article: Article, terms: Iterable[str], width: int = 240) -> str:
    lowered = article.body.lower()
    for term in terms:
        pos = lowered.find(term)
        if pos != -1:
            start = max(0, pos - width // 3)
            snippet = article.body[start:start + width].replace("\n", " ")
            return ("…" if start else "") + snippet.strip() + "…"
    return article.body[:width].replace("\n", " ").strip() + "…"


HEAD_RE = re.compile(r"^(# |URL: |Category: |Section: |Summary: |Updated: )")


def _parse_article(path: str, category: str) -> Article:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    head, _, body = text.partition("\n\n")
    fields = {"title": "", "url": "", "section": "", "summary": ""}
    for line in head.splitlines():
        if line.startswith("# "):
            fields["title"] = line[2:].strip()
        elif line.startswith("URL: "):
            fields["url"] = line[5:].strip()
        elif line.startswith("Section: "):
            fields["section"] = line[9:].strip()
        elif line.startswith("Summary: "):
            fields["summary"] = line[9:].strip()
    slug = os.path.basename(path)[:-3]
    return Article(category, slug, fields["title"] or slug, fields["summary"],
                   fields["section"], fields["url"], body.strip())


def _parse_index(path: str, category: str) -> dict:
    meta = {"title": category, "summary": "", "url": ""}
    if not os.path.exists(path):
        return meta
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("# "):
                meta["title"] = line[2:].strip()
            elif line.startswith("URL: "):
                meta["url"] = line[5:].strip()
            elif line.startswith("Summary: "):
                meta["summary"] = line[9:].strip()
            elif line.startswith("## "):
                break
    return meta


_KB: Optional[KnowledgeBase] = None


def get_kb(root: str = KB_ROOT) -> KnowledgeBase:
    """Process-wide singleton so the catalog is built once."""
    global _KB
    if _KB is None or _KB.root != root:
        _KB = KnowledgeBase(root)
    return _KB


if __name__ == "__main__":
    import sys

    kb = get_kb()
    if len(sys.argv) > 1 and sys.argv[1] == "search":
        print(json.dumps(kb.search(" ".join(sys.argv[2:])), ensure_ascii=False, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "get":
        article = kb.get(sys.argv[2])
        print(article.render() if article else "not found")
    elif len(sys.argv) > 1 and sys.argv[1] == "catalog":
        print(kb.catalog())
    elif len(sys.argv) > 1 and sys.argv[1] == "pack":
        # rebuild from the directories, never from a stale pack
        pack_path = os.path.join(KB_ROOT, PACK_NAME)
        if os.path.exists(pack_path):
            os.remove(pack_path)
        fresh = KnowledgeBase(KB_ROOT)
        print(f"packed {len(fresh.articles)} entries -> {fresh.pack()}")
    else:
        print(json.dumps(kb.stats(), ensure_ascii=False, indent=2))
