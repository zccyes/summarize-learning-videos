#!/usr/bin/env python3
"""Normalize VTT or Whisper JSON into timestamped Markdown."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


TIMESTAMP = re.compile(r"(?P<start>\d{2}:\d{2}:\d{2}[.,]\d{3}|\d{2}:\d{2}[.,]\d{3})\s+-->\s+")
TAG = re.compile(r"<[^>]+>")


def clean_text(value: str) -> str:
    value = TAG.sub("", html.unescape(value))
    return re.sub(r"\s+", " ", value).strip()


def display_time(value: str | float | int) -> str:
    if isinstance(value, (float, int)):
        total = int(value)
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    parts = value.replace(",", ".").split(":")
    if len(parts) == 2:
        parts.insert(0, "00")
    return ":".join(parts)[:8]


def dedupe(rows: list[tuple[str, str]]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for timestamp, text in rows:
        text = clean_text(text)
        if not text:
            continue
        if result and text == result[-1][1]:
            continue
        if result and text.startswith(result[-1][1]) and len(text) > len(result[-1][1]):
            result[-1] = (result[-1][0], text)
            continue
        result.append((timestamp, text))
    return result


def parse_vtt(path: Path) -> list[tuple[str, str]]:
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    rows: list[tuple[str, str]] = []
    index = 0
    while index < len(lines):
        match = TIMESTAMP.search(lines[index])
        if not match:
            index += 1
            continue
        timestamp = display_time(match.group("start"))
        index += 1
        text_lines: list[str] = []
        while index < len(lines) and lines[index].strip():
            text_lines.append(lines[index])
            index += 1
        rows.append((timestamp, " ".join(text_lines)))
    return dedupe(rows)


def parse_json(path: Path) -> list[tuple[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    segments = data.get("segments") or []
    return dedupe([(display_time(item.get("start", 0)), item.get("text", "")) for item in segments])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = parse_json(args.input) if args.input.suffix.lower() == ".json" else parse_vtt(args.input)
    body = "\n\n".join(f"[{timestamp}] {text}" for timestamp, text in rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(f"# 视频转写稿\n\n{body}\n", encoding="utf-8")
    print(f"Wrote {len(rows)} timestamped segments to {args.output}")


if __name__ == "__main__":
    main()
