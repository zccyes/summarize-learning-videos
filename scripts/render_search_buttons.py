#!/usr/bin/env python3
"""Render portable, logo-only Baidu and Google search buttons for Obsidian."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path
from urllib.parse import quote


BUTTON_STYLE = (
    "display:inline-flex;align-items:center;justify-content:center;"
    "width:26px;height:26px;border:1px solid var(--background-modifier-border);"
    "border-radius:6px;background:var(--background-secondary);"
    "text-decoration:none;vertical-align:middle;margin-right:4px;"
)


def button(provider: str, href: str, icon: str, term: str) -> str:
    label = f"{provider}搜索：{term}"
    return (
        f'<a href="{html.escape(href, quote=True)}" '
        f'title="{html.escape(label, quote=True)}" '
        f'aria-label="{html.escape(label, quote=True)}" '
        f'target="_blank" rel="noopener noreferrer" style="{BUTTON_STYLE}">'
        f'<img src="{icon}" alt="" width="16" height="16"></a>'
    )


def normalize_term(term: str) -> str:
    normalized = " ".join(term.split()).strip()
    if not normalized:
        raise ValueError("Search term cannot be empty")
    return normalized


def render(term: str) -> str:
    term = normalize_term(term)
    baidu_url = "https://www.baidu.com/s?wd=" + quote(term, safe="")
    google_url = "https://www.google.com/search?q=" + quote(term, safe="")
    return (
        '<span class="slv-search-buttons">'
        + button(
            "百度",
            baidu_url,
            "https://www.baidu.com/favicon.ico",
            term,
        )
        + button(
            "Google",
            google_url,
            "https://www.google.com/favicon.ico",
            term,
        )
        + "</span>"
    )


def heading_term(heading: str) -> str:
    text = re.sub(r"^###\s+", "", heading).strip().replace("`", "")
    return normalize_term(re.split(r"[（(]", text, maxsplit=1)[0])


def rewrite_note(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"(?ms)^## 核心概念与术语\s*$.*?(?=^##\s|\Z)",
        text,
    )
    if not match:
        raise ValueError("Missing core-concepts section")

    section = match.group(0)
    pattern = re.compile(
        r"(?ms)^(###\s+.+?)\n\s*\n<span class=\"slv-search-buttons\">.*?</span>"
    )
    replacements = 0

    def replace(button_match: re.Match[str]) -> str:
        nonlocal replacements
        replacements += 1
        heading = button_match.group(1)
        return f"{heading}\n\n{render(heading_term(heading))}"

    rewritten = pattern.sub(replace, section)
    headings = len(re.findall(r"(?m)^###\s+.+$", section))
    if headings == 0 or replacements != headings:
        raise ValueError(
            f"Found {headings} concept headings but rewrote {replacements} button rows"
        )

    path.write_text(text[: match.start()] + rewritten + text[match.end() :], encoding="utf-8")
    return replacements


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--term")
    group.add_argument("--rewrite-note", type=Path)
    args = parser.parse_args()

    if args.rewrite_note:
        print(f"Rewrote {rewrite_note(args.rewrite_note)} core-concept button rows")
    else:
        print(render(args.term))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
