#!/usr/bin/env python3
"""Render portable, logo-only Baidu and Google search buttons for Obsidian."""

from __future__ import annotations

import argparse
import html
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


def render(term: str, baidu_query: str, google_query: str) -> str:
    baidu_url = "https://www.baidu.com/s?wd=" + quote(baidu_query, safe="")
    google_url = "https://www.google.com/search?q=" + quote(google_query, safe="")
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--term", required=True)
    parser.add_argument("--baidu-query")
    parser.add_argument("--google-query")
    args = parser.parse_args()

    print(
        render(
            args.term,
            args.baidu_query or args.term,
            args.google_query or args.term,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
