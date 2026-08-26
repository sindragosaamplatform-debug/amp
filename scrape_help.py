#!/usr/bin/env python3
"""Scrape a HelpCrunch knowledge-base category (help.aff.ltd) into clean text files.

Each article becomes one plain-text file containing only what an AI guide agent
needs: title, URL, section, summary, and the article body reduced to headings,
paragraphs, lists, tables and code. Bold/italic markup, images, author blocks,
navigation, styling attributes and empty visual wrappers are dropped.

Usage:
    python3 scrape_help.py                          # default: /en/admin-panel -> ./kb
    python3 scrape_help.py --url https://help.aff.ltd/ru/admin-panel --out kb-ru
    python3 scrape_help.py --keep-images            # keep [image: url] markers
    python3 scrape_help.py --ext txt

Standard library only.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import html
import os
import re
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " \
     "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"

SKIP_TAGS = {"script", "style", "noscript", "svg", "iframe", "video", "audio",
             "source", "picture", "button", "form", "select", "option"}
BLOCK_TAGS = {"p", "div", "section", "article", "header", "footer", "blockquote",
              "figure", "figcaption", "h1", "h2", "h3", "h4", "h5", "h6",
              "ul", "ol", "li", "table", "tr", "pre", "hr", "br"}


# --------------------------------------------------------------------------- #
# fetching
# --------------------------------------------------------------------------- #
def fetch(url: str, retries: int = 3, timeout: int = 30) -> str:
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en",
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            return raw.decode(charset, errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {last}")


# --------------------------------------------------------------------------- #
# tiny HTML helpers (no third-party deps)
# --------------------------------------------------------------------------- #
TAG_RE = re.compile(r"<(/?)([a-zA-Z][\w:-]*)([^>]*?)(/?)>", re.S)


def extract_element(doc: str, opening_match: re.Match, tag: str) -> str:
    """Return the inner HTML of an element, given the match of its opening tag."""
    start = opening_match.end()
    depth = 1
    pos = start
    for m in TAG_RE.finditer(doc, start):
        if m.group(2).lower() != tag:
            continue
        if m.group(1):  # closing
            depth -= 1
            if depth == 0:
                return doc[start:m.start()]
        elif not m.group(4):  # opening, not self-closing
            depth += 1
        pos = m.end()
    return doc[start:pos]


def find_element(doc: str, tag: str, attr_pattern: str) -> str | None:
    """Inner HTML of the first `tag` whose attributes match `attr_pattern`."""
    pat = re.compile(rf"<{tag}\b[^>]*{attr_pattern}[^>]*>", re.I | re.S)
    m = pat.search(doc)
    if not m:
        return None
    return extract_element(doc, m, tag.lower())


def text_of(fragment: str | None) -> str:
    if not fragment:
        return ""
    txt = re.sub(r"<[^>]+>", " ", fragment)
    return clean_spaces(html.unescape(txt))


def int_attr(attrs: dict, name: str, default: int = 1) -> int:
    try:
        return max(1, int(attrs.get(name, "").strip()))
    except (TypeError, ValueError):
        return default


def clean_spaces(text: str) -> str:
    return re.sub(r"[ \t   ]+", " ", text).strip()


# --------------------------------------------------------------------------- #
# HTML -> clean text
# --------------------------------------------------------------------------- #
class ArticleTextExtractor(HTMLParser):
    """Flattens article HTML into plain text with structure but no styling."""

    def __init__(self, keep_images: bool = False, base_url: str = ""):
        super().__init__(convert_charrefs=True)
        self.keep_images = keep_images
        self.base_url = base_url
        self.lines: list[str] = []
        self.buf: list[str] = []
        self.skip_depth = 0
        self.pre_depth = 0
        self.list_stack: list[dict] = []   # {"type": "ul"|"ol", "n": int}
        self.href: str | None = None
        self.link_text: list[str] = []
        self.in_cell = False
        self.pending_prefix = ""
        # table state: carried-over cells from rowspan, per open table
        self.table_stack: list[dict] = []
        self.row: dict[int, str] = {}
        self.next_col = 0
        self.cur_span = (1, 1)

    # -- output plumbing ---------------------------------------------------- #
    def _flush(self) -> None:
        # inside a table cell everything stays in the buffer until </td>
        if self.in_cell:
            if self.buf and not self.buf[-1].endswith(" "):
                self.buf.append(" ")
            return
        line = "".join(self.buf)
        self.buf.clear()
        if self.pre_depth:
            self.lines.append(line.rstrip())
        else:
            line = clean_spaces(line)
            if line:
                self.lines.append(line)
            elif (self.lines and self.lines[-1] != ""
                    and not self.list_stack and not self.table_stack):
                # no blank lines between items of one list or rows of one table
                self.lines.append("")

    def _emit(self, text: str) -> None:
        self.buf.append(text)

    def _newblock(self) -> None:
        self._flush()
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    # -- parser callbacks --------------------------------------------------- #
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        a = dict((k.lower(), v or "") for k, v in attrs)

        if self.skip_depth or tag in SKIP_TAGS:
            if tag in SKIP_TAGS:
                self.skip_depth += 1
            return

        if tag == "img":
            if self.keep_images:
                src = a.get("src", "")
                alt = clean_spaces(a.get("alt", ""))
                if src:
                    self._newblock()
                    self.lines.append(f"[image: {alt + ' — ' if alt else ''}{src}]")
                    self.lines.append("")
            return

        if tag == "br":
            if self.in_cell:
                self.buf.append(" / ")
            else:
                self._flush()
            return

        if tag == "hr":
            self._newblock()
            self.lines.append("---")
            self.lines.append("")
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._newblock()
            self.pending_prefix = "#" * int(tag[1]) + " "
            return

        if tag == "pre":
            self._newblock()
            self.lines.append("```")
            self.pre_depth += 1
            return

        if tag in ("ul", "ol"):
            self._flush()
            self.list_stack.append({"type": tag, "n": 0})
            return

        if tag == "li":
            self._flush()
            if self.list_stack:
                lvl = self.list_stack[-1]
                indent = "  " * (len(self.list_stack) - 1)
                if lvl["type"] == "ol":
                    lvl["n"] += 1
                    self.pending_prefix = f"{indent}{lvl['n']}. "
                else:
                    self.pending_prefix = f"{indent}- "
            else:
                self.pending_prefix = "- "
            return

        if tag == "a":
            self.href = a.get("href", "")
            self.link_text = []
            return

        if tag == "table":
            self._newblock()
            self.table_stack.append({"carry": {}})
            return

        if tag == "tr":
            self._flush()
            carry = self.table_stack[-1]["carry"] if self.table_stack else {}
            # cells spanning into this row from earlier rows keep their column
            self.row = {col: txt for col, (left, txt) in carry.items() if left > 0}
            self.next_col = 0
            return

        if tag in ("td", "th"):
            self._flush()
            self.in_cell = True
            self.cur_span = (int_attr(a, "rowspan"), int_attr(a, "colspan"))
            return

        if tag in BLOCK_TAGS:
            self._flush()

    def handle_endtag(self, tag):
        tag = tag.lower()

        if self.skip_depth:
            if tag in SKIP_TAGS:
                self.skip_depth -= 1
            return

        if tag == "a":
            text = clean_spaces("".join(self.link_text))
            href = (self.href or "").strip()
            self.href, self.link_text = None, []
            if href.startswith(("http://", "https://", "mailto:")):
                if not text:
                    self._emit(href)
                elif text.rstrip("/") in href.rstrip("/"):
                    self._emit(text)
                else:
                    self._emit(f"{text} ({href})")
            else:
                self._emit(text)
            return

        if tag == "pre":
            self._flush()
            self.pre_depth = max(0, self.pre_depth - 1)
            self.lines.append("```")
            self.lines.append("")
            return

        if tag in ("td", "th"):
            text = clean_spaces("".join(self.buf)).strip(" /")
            self.buf.clear()
            self.in_cell = False
            rowspan, colspan = self.cur_span
            self.cur_span = (1, 1)
            carry = self.table_stack[-1]["carry"] if self.table_stack else {}
            while self.next_col in self.row:
                self.next_col += 1
            col = self.next_col
            for k in range(colspan):
                self.row[col + k] = text
                if rowspan > 1:
                    carry[col + k] = [rowspan, text]
            self.next_col = col + colspan
            return

        if tag == "tr":
            carry = self.table_stack[-1]["carry"] if self.table_stack else {}
            for col in list(carry):
                carry[col][0] -= 1
                if carry[col][0] <= 0:
                    del carry[col]
            row = [self.row[c] for c in sorted(self.row)]
            self.row = {}
            if any(row):
                self.lines.append(" | ".join(row))
            return

        if tag == "table":
            if self.table_stack:
                self.table_stack.pop()
            self._newblock()
            return

        if tag in ("ul", "ol"):
            self._flush()
            if self.list_stack:
                self.list_stack.pop()
            if not self.list_stack:
                self._newblock()
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._flush()
            self.lines.append("")
            return

        if tag in BLOCK_TAGS:
            self._flush()

    def handle_data(self, data):
        if self.skip_depth:
            return
        if self.href is not None:
            self.link_text.append(data)
            return
        if not self.pre_depth:
            if not data.strip():
                if self.buf and not self.buf[-1].endswith(" "):
                    self.buf.append(" ")
                return
        if self.pending_prefix and not self.buf:
            self.buf.append(self.pending_prefix)
            self.pending_prefix = ""
        self.buf.append(data)

    # -- result ------------------------------------------------------------- #
    def get_text(self) -> str:
        self._flush()
        out: list[str] = []
        for line in self.lines:
            line = line.replace(" ", " ").rstrip()
            if line == "" and (not out or out[-1] == ""):
                continue
            out.append(line)
        text = "\n".join(out).strip()
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"\n(---\n)(?:\s*---\n)+", r"\n\1", text)
        return normalize_headings(text)


HEADING_RE = re.compile(r"^(#{1,6}) ", re.M)


def normalize_headings(text: str) -> str:
    """Shift body headings so the shallowest one is level 2 (level 1 = article title)."""
    levels = [len(m.group(1)) for m in HEADING_RE.finditer(text)]
    if not levels:
        return text
    shift = 2 - min(levels)
    if shift == 0:
        return text
    return HEADING_RE.sub(
        lambda m: "#" * max(2, min(6, len(m.group(1)) + shift)) + " ", text)


def html_to_text(fragment: str, keep_images: bool = False) -> str:
    p = ArticleTextExtractor(keep_images=keep_images)
    p.feed(fragment)
    p.close()
    return p.get_text()


# --------------------------------------------------------------------------- #
# site-specific parsing
# --------------------------------------------------------------------------- #
def parse_category(index_html: str, base: str) -> tuple[str, str, list[dict]]:
    """Return (category title, category description, ordered article entries)."""
    title = text_of(find_element(index_html, "h1", "")) or "Category"
    desc = text_of(find_element(index_html, "span", 'class="page-header-description"'))

    entries: list[dict] = []
    section = ""
    pattern = re.compile(
        r'<div class="category-item section-header"[^>]*>\s*<h3>(?P<sec>.*?)</h3>'
        r'|<div class="category-item[^"]*"\s*data-href="(?P<href>[^"]+)"',
        re.S)
    for m in pattern.finditer(index_html):
        if m.group("sec") is not None:
            section = text_of(m.group("sec"))
            continue
        href = html.unescape(m.group("href"))
        if not href.startswith("http"):
            href = base.rstrip("/") + "/" + href.lstrip("/")
        entries.append({"url": href, "section": section})

    # fallback: any article link under the category path
    if not entries:
        for href in dict.fromkeys(re.findall(rf'{re.escape(base)}/[a-z0-9\-]+', index_html)):
            entries.append({"url": href, "section": ""})
    return title, desc, entries


def parse_article(page_html: str, url: str, keep_images: bool) -> dict:
    title = text_of(find_element(page_html, "h1", "")) or url.rsplit("/", 1)[-1]
    summary = text_of(find_element(page_html, "span", 'class="page-header-description"'))

    updated = ""
    m = re.search(r'class="article-update[^"]*"\s*title="([^"]*)"', page_html)
    if m:
        updated = html.unescape(m.group(1)).strip()

    body_html = find_element(page_html, "div", 'id="article-content"')
    body = html_to_text(body_html or "", keep_images=keep_images)
    return {"url": url, "title": title, "summary": summary,
            "updated": updated, "body": body}


def render_article(art: dict, category: str) -> str:
    head = [f"# {art['title']}", f"URL: {art['url']}", f"Category: {category}"]
    if art.get("section"):
        head.append(f"Section: {art['section']}")
    if art.get("summary"):
        head.append(f"Summary: {art['summary']}")
    if art.get("updated"):
        head.append(f"Updated: {art['updated']}")
    return "\n".join(head) + "\n\n" + art["body"].strip() + "\n"


def slug_of(url: str) -> str:
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    return re.sub(r"[^a-z0-9\-_]+", "-", slug.lower()) or "article"


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="https://help.aff.ltd/en/admin-panel",
                    help="category URL to scrape")
    ap.add_argument("--out", default="kb", help="output directory")
    ap.add_argument("--ext", default="md", choices=["md", "txt"],
                    help="output file extension")
    ap.add_argument("--keep-images", action="store_true",
                    help="keep [image: url] markers instead of dropping images")
    ap.add_argument("--extra", action="append", default=[], metavar="URL",
                    help="article URL to include even if the category page does not "
                         "list it (e.g. a page that exists but is untranslated); "
                         "may be repeated")
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--delay", type=float, default=0.2,
                    help="seconds to wait between request starts")
    args = ap.parse_args()

    base = args.url.rstrip("/")
    print(f"index  {base}", file=sys.stderr)
    index_html = fetch(base)
    category, cat_desc, entries = parse_category(index_html, base)
    if not entries:
        print("no articles found — the page layout may have changed", file=sys.stderr)
        return 1
    known = {e["url"] for e in entries}
    for url in args.extra:
        if url not in known:
            entries.append({"url": url, "section": "Not listed in the category"})
    print(f"found  {len(entries)} articles", file=sys.stderr)

    os.makedirs(args.out, exist_ok=True)

    lock_delay = args.delay

    def work(entry: dict) -> dict:
        time.sleep(lock_delay)
        page = fetch(entry["url"])
        art = parse_article(page, entry["url"], args.keep_images)
        art["section"] = entry["section"]
        return art

    results: dict[str, dict] = {}
    errors: list[tuple[str, str]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(work, e): e for e in entries}
        for fut in concurrent.futures.as_completed(futures):
            entry = futures[fut]
            try:
                art = fut.result()
            except Exception as exc:  # noqa: BLE001 - report and continue
                errors.append((entry["url"], str(exc)))
                print(f"FAIL   {entry['url']}: {exc}", file=sys.stderr)
                continue
            results[entry["url"]] = art
            print(f"ok     {art['title']}", file=sys.stderr)

    index_lines = [f"# {category}", f"URL: {base}"]
    if cat_desc:
        index_lines.append(f"Summary: {cat_desc}")
    index_lines += ["", f"{len(results)} articles.", ""]

    current_section = None
    written = 0
    for entry in entries:
        art = results.get(entry["url"])
        if not art:
            continue
        if art["section"] != current_section:
            current_section = art["section"]
            index_lines.append("")
            index_lines.append(f"## {current_section or 'Other'}")
        name = f"{slug_of(art['url'])}.{args.ext}"
        with open(os.path.join(args.out, name), "w", encoding="utf-8") as fh:
            fh.write(render_article(art, category))
        written += 1
        line = f"- {name} — {art['title']}"
        if art["summary"]:
            line += f": {art['summary']}"
        index_lines.append(line)

    with open(os.path.join(args.out, f"_index.{args.ext}"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(index_lines).strip() + "\n")

    print(f"\nwrote {written} files + _index.{args.ext} to {args.out}/", file=sys.stderr)
    if errors:
        print(f"{len(errors)} failed:", file=sys.stderr)
        for url, err in errors:
            print(f"  {url}: {err}", file=sys.stderr)
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
