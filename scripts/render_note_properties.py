#!/usr/bin/env python3
"""Render a final human-readable property table from Obsidian YAML frontmatter."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
from collections import OrderedDict
from pathlib import Path


LABELS = {
    "type": "类型",
    "title": "标题",
    "aliases": "别名",
    "platform": "平台",
    "creator": "作者",
    "participants": "参与者",
    "source": "原视频",
    "video_id": "视频 ID",
    "published": "发布日期",
    "duration": "时长",
    "language": "语言",
    "transcript_source": "转写来源",
    "source_quality": "来源质量",
    "status": "状态",
    "created": "笔记创建日期",
    "tags": "标签",
}


def scalar(value: str) -> str:
    value = value.strip()
    if not value or value == "null":
        return "—"
    if value.startswith('"') and value.endswith('"'):
        try:
            return str(json.loads(value))
        except json.JSONDecodeError:
            return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    return value


def inline_list(value: str) -> list[str]:
    inner = value.strip()[1:-1]
    if not inner.strip():
        return []
    reader = csv.reader(io.StringIO(inner), skipinitialspace=True)
    return [scalar(item) for item in next(reader)]


def parse_frontmatter(text: str) -> OrderedDict[str, str | list[str]]:
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError("Missing or malformed YAML frontmatter")
    _, frontmatter, _ = text.split("---", 2)
    properties: OrderedDict[str, str | list[str]] = OrderedDict()
    current: str | None = None

    for raw_line in frontmatter.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        item = re.match(r"^\s{2,}-\s+(.*)$", raw_line)
        if item and current:
            existing = properties.get(current)
            if not isinstance(existing, list):
                existing = []
                properties[current] = existing
            existing.append(scalar(item.group(1)))
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):(?:\s*(.*))?$", raw_line)
        if not match:
            continue
        current = match.group(1)
        value = (match.group(2) or "").strip()
        if value.startswith("[") and value.endswith("]"):
            properties[current] = inline_list(value)
        elif value:
            properties[current] = scalar(value)
        else:
            properties[current] = []

    return properties


def escape_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


def display_value(key: str, value: str | list[str]) -> str:
    values = value if isinstance(value, list) else [value]
    if key == "source" and values and values[0] != "—":
        url = values[0]
        return f"[打开原视频]({url})"
    if key == "tags":
        return " ".join(item if item.startswith("#") else f"#{item}" for item in values)
    if len(values) > 1:
        return "；".join(values)
    return values[0] if values else "—"


def render(properties: OrderedDict[str, str | list[str]]) -> str:
    rows = ["## 笔记属性", "", "| 属性 | 内容 |", "|---|---|"]
    for key, value in properties.items():
        label = LABELS.get(key, key)
        rows.append(f"| {escape_cell(label)} | {escape_cell(display_value(key, value))} |")
    return "\n".join(rows)


def replace_section(text: str, section: str) -> str:
    pattern = re.compile(r"(?ms)\n?^## 笔记属性\s*\n.*?(?=^##\s|\Z)")
    without_existing = pattern.sub("", text).rstrip()
    return f"{without_existing}\n\n{section}\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("note", type=Path)
    parser.add_argument("--write", action="store_true", help="Append or replace the final section")
    args = parser.parse_args()

    text = args.note.read_text(encoding="utf-8")
    section = render(parse_frontmatter(text))
    if args.write:
        args.note.write_text(replace_section(text, section), encoding="utf-8")
    else:
        print(section)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
