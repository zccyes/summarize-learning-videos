#!/usr/bin/env python3
"""Validate structural release criteria for a detailed Obsidian video note."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED_PROPERTIES = (
    "type", "title", "platform", "creator", "source", "video_id",
    "duration", "transcript_source", "source_quality", "status", "created", "tags",
)
REQUIRED_SECTIONS = (
    "## 一句话主题",
    "## 内容总览",
    "## 时间轴与内容地图",
    "## 分章节详细提炼",
    "## 核心概念与术语",
    "## 作者的假设、限制与可能争议",
    "## 复习问题",
    "## 提炼质量说明",
)
PLACEHOLDER = re.compile(r"TODO|待补充|待填写|<[^>\n]{1,80}>", re.IGNORECASE)


def minimum_chars(duration_seconds: int | None) -> int:
    if duration_seconds is None:
        return 1500
    if duration_seconds <= 15 * 60:
        return 1500
    if duration_seconds <= 45 * 60:
        return 3000
    if duration_seconds <= 90 * 60:
        return 5000
    return 6000


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("note", type=Path)
    parser.add_argument("--duration-seconds", type=int)
    parser.add_argument("--expected-chapters", type=int)
    args = parser.parse_args()

    text = args.note.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        errors.append("Missing or malformed YAML frontmatter")
        frontmatter = ""
        body = text
    else:
        _, frontmatter, body = text.split("---", 2)

    for key in REQUIRED_PROPERTIES:
        if not re.search(rf"(?m)^{re.escape(key)}:\s*", frontmatter):
            errors.append(f"Missing YAML property: {key}")

    for section in REQUIRED_SECTIONS:
        if section not in body:
            errors.append(f"Missing required section: {section}")

    placeholders = sorted(set(PLACEHOLDER.findall(text)))
    if placeholders:
        errors.append("Template placeholders remain: " + ", ".join(placeholders[:5]))

    timeline_rows = len(re.findall(r"(?m)^\|\s*\[\d{2}:\d{2}", body))
    detailed_chapters = len(re.findall(r"(?m)^###\s+\d{2}:\d{2}", body))
    if args.expected_chapters:
        if timeline_rows < args.expected_chapters:
            errors.append(
                f"Timeline covers {timeline_rows} rows; expected at least {args.expected_chapters} chapters"
            )
        if detailed_chapters < args.expected_chapters:
            errors.append(
                f"Detailed section covers {detailed_chapters} chapters; expected at least {args.expected_chapters}"
            )
    elif timeline_rows < 3:
        warnings.append("Fewer than three timestamped timeline rows")

    body_chars = len(re.sub(r"\s+", "", body))
    required_chars = minimum_chars(args.duration_seconds)
    if body_chars < required_chars:
        errors.append(f"Body has {body_chars} non-space characters; quality floor is {required_chars}")

    review_questions = len(re.findall(r"(?m)^\d+\.\s+", body.split("## 复习问题", 1)[-1]))
    if review_questions < 5:
        errors.append(f"Only {review_questions} review questions; expected at least 5")

    result = {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "body_characters": body_chars,
            "timeline_rows": timeline_rows,
            "detailed_chapters": detailed_chapters,
            "review_questions": review_questions,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
