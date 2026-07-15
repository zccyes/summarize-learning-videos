#!/usr/bin/env python3
"""Organize a complete timestamped transcript under platform chapters."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROW = re.compile(r"^\[(?P<time>\d{2}:\d{2}:\d{2})\]\s+(?P<text>.+)$")


def seconds(value: str) -> int:
    hours, minutes, seconds_value = (int(part) for part in value.split(":"))
    return hours * 3600 + minutes * 60 + seconds_value


def display(value: int | float) -> str:
    total = int(value)
    hours, remainder = divmod(total, 3600)
    minutes, seconds_value = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds_value:02d}"


def read_rows(path: Path) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = ROW.match(line.strip())
        if match:
            rows.append((seconds(match.group("time")), match.group("text").strip()))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("transcript", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--fallback-minutes", type=int, default=10)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    rows = read_rows(args.transcript)
    chapters = manifest.get("chapters") or []
    duration = int(manifest.get("duration_seconds") or (rows[-1][0] if rows else 0))
    if not chapters:
        width = max(60, args.fallback_minutes * 60)
        chapters = [
            {
                "title": f"内容段落 {index + 1}",
                "start_time": start,
                "end_time": min(start + width, duration + 1),
            }
            for index, start in enumerate(range(0, duration + 1, width))
        ]

    blocks = [f"# {manifest.get('title') or '视频'}：完整章节阅读稿"]
    for chapter in chapters:
        start = int(chapter.get("start_time") or 0)
        end = int(chapter.get("end_time") or duration + 1)
        text = "".join(text_value for row_time, text_value in rows if start <= row_time < end)
        blocks.append(
            f"## {display(start)}–{display(end)} {chapter.get('title') or '未命名章节'}\n\n{text}"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n\n".join(blocks).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote {len(chapters)} complete chapters to {args.output}")


if __name__ == "__main__":
    main()
