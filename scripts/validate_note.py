#!/usr/bin/env python3
"""Validate structural release criteria for a detailed Obsidian video note."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import unquote


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
    "## 知识图谱关键词",
    "## 提炼质量说明",
    "## 笔记属性",
)
PLACEHOLDER = re.compile(
    r"TODO|待补充|待填写|<(?!/?(?:a|span|img)\b)[^>\n]{1,80}>",
    re.IGNORECASE,
)


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


def concept_name(heading: str) -> str:
    text = re.sub(r"^###\s+", "", heading).strip().replace("`", "")
    return " ".join(re.split(r"[（(]", text, maxsplit=1)[0].split())


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

    level_two_sections = re.findall(r"(?m)^##\s+.+$", body)
    if level_two_sections and level_two_sections[-1] != "## 笔记属性":
        errors.append("Note properties must be the final level-two section")

    property_section = body.split("## 笔记属性", 1)[-1] if "## 笔记属性" in body else ""
    if "| 属性 | 内容 |" not in property_section:
        errors.append("Final note-properties section must contain the generated property table")
    for label in ("标题", "平台", "作者", "原视频", "时长", "来源质量", "标签"):
        if not re.search(rf"(?m)^\|\s*{re.escape(label)}\s*\|", property_section):
            errors.append(f"Final note-properties table is missing: {label}")

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

    concept_section = body.split("## 核心概念与术语", 1)[-1].split("\n## ", 1)[0]
    concept_headings = re.findall(r"(?m)^###\s+.+$", concept_section)
    concept_count = len(concept_headings)
    if concept_count == 0:
        errors.append("Core concepts must use one plain-text level-three heading per concept")
    if any("[[" in heading or "]]" in heading for heading in concept_headings):
        errors.append("Core-concept headings must not use unresolved wikilinks")

    baidu_links = re.findall(
        r'href="https://www\.baidu\.com/s\?wd=([^"\s]+)"', concept_section
    )
    google_links = re.findall(
        r'href="https://www\.google\.com/search\?q=([^"\s]+)"', concept_section
    )
    baidu_icons = concept_section.count('src="https://www.baidu.com/favicon.ico"')
    google_icons = concept_section.count('src="https://www.google.com/favicon.ico"')
    if len(baidu_links) != concept_count or baidu_icons != concept_count:
        errors.append(
            f"Core concepts have {concept_count} headings but not exactly one Baidu logo button each"
        )
    if len(google_links) != concept_count or google_icons != concept_count:
        errors.append(
            f"Core concepts have {concept_count} headings but not exactly one Google logo button each"
        )

    expected_queries = [concept_name(heading) for heading in concept_headings]
    decoded_baidu = [unquote(html.unescape(query)) for query in baidu_links]
    decoded_google = [unquote(html.unescape(query)) for query in google_links]
    if len(decoded_baidu) == concept_count and decoded_baidu != expected_queries:
        errors.append(
            "Baidu queries must exactly equal their visible concept names; "
            "do not append explanatory keywords"
        )
    if len(decoded_google) == concept_count and decoded_google != expected_queries:
        errors.append(
            "Google queries must exactly equal their visible concept names; "
            "do not append explanatory or translated keywords"
        )
    if concept_section.count('title="百度搜索：') != concept_count:
        errors.append("Every Baidu button must include a hover title")
    if concept_section.count('title="Google搜索：') != concept_count:
        errors.append("Every Google button must include a hover title")
    if concept_section.count('aria-label="百度搜索：') != concept_count:
        errors.append("Every Baidu button must include an accessibility label")
    if concept_section.count('aria-label="Google搜索：') != concept_count:
        errors.append("Every Google button must include an accessibility label")

    button_contents = re.findall(
        r'(?s)<a\b[^>]*href="https://www\.(?:baidu|google)\.com/[^>]*>(.*?)</a>',
        concept_section,
    )
    for content in button_contents:
        visible_text = re.sub(r"<[^>]+>", "", content).strip()
        if visible_text:
            errors.append("Search buttons must be logo-only with no visible provider text")
            break

    keyword_section = body.split("## 知识图谱关键词", 1)[-1].split("\n## ", 1)[0]
    graph_tags = re.findall(r"(?<!#)#(?!#)([^\s#]+)", keyword_section)
    if len(set(graph_tags)) < 3:
        errors.append("Knowledge-graph section must contain at least three normalized tags")
    if "[[" in keyword_section or "]]" in keyword_section:
        errors.append("Knowledge-graph keywords must use tags, not unresolved wikilinks")

    result = {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "body_characters": body_chars,
            "timeline_rows": timeline_rows,
            "detailed_chapters": detailed_chapters,
            "review_questions": review_questions,
            "core_concepts": concept_count,
            "graph_keywords": len(set(graph_tags)),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
