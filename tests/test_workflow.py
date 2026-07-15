from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run_script(name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        check=False,
        capture_output=True,
        text=True,
    )


class WorkflowTests(unittest.TestCase):
    def test_render_note_properties_appends_final_table_from_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            note = Path(directory) / "note.md"
            note.write_text(
                "---\n"
                "type: video-note\n"
                'title: "测试笔记"\n'
                "platform: Bilibili\n"
                "creator: 测试作者\n"
                "source: https://example.com/video\n"
                "duration: 00:10:00\n"
                "source_quality: C\n"
                "tags:\n"
                "  - 视频笔记\n"
                "  - 人工智能\n"
                "---\n\n"
                "# 测试笔记\n\n正文。\n",
                encoding="utf-8",
            )
            result = run_script("render_note_properties.py", "--write", str(note))
            self.assertEqual(result.returncode, 0, result.stderr)
            result = run_script("render_note_properties.py", "--write", str(note))
            self.assertEqual(result.returncode, 0, result.stderr)
            text = note.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"))
            self.assertTrue(text.rstrip().endswith("| 标签 | #视频笔记 #人工智能 |"))
            self.assertIn("| 原视频 | [打开原视频](https://example.com/video) |", text)
            self.assertEqual(text.count("## 笔记属性"), 1)

    def test_render_search_buttons_are_logo_only_and_url_encoded(self) -> None:
        result = run_script(
            "render_search_buttons.py",
            "--term",
            "HBM4",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        markup = result.stdout.strip()
        self.assertIn("https://www.baidu.com/favicon.ico", markup)
        self.assertIn("https://www.google.com/favicon.ico", markup)
        hrefs = re.findall(r'href="([^"]+)"', markup)
        self.assertEqual(parse_qs(urlparse(hrefs[0]).query)["wd"], ["HBM4"])
        self.assertEqual(parse_qs(urlparse(hrefs[1]).query)["q"], ["HBM4"])
        self.assertIn('title="百度搜索：HBM4"', markup)
        self.assertIn('aria-label="Google搜索：HBM4"', markup)
        self.assertNotIn(">百度搜索<", markup)
        self.assertNotIn(">Google搜索<", markup)

    def test_rewrite_search_buttons_uses_heading_concept_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            note = Path(directory) / "note.md"
            old_buttons = (
                '<span class="slv-search-buttons">'
                '<a href="https://www.baidu.com/s?wd=%E6%B2%89%E6%B2%A1%E6%88%90%E6%9C%AC%20%E5%86%B3%E7%AD%96">'
                '<img src="https://www.baidu.com/favicon.ico" alt=""></a>'
                '<a href="https://www.google.com/search?q=sunk%20cost%20decision%20making">'
                '<img src="https://www.google.com/favicon.ico" alt=""></a></span>'
            )
            note.write_text(
                "## 核心概念与术语\n\n"
                "### 沉没成本（Sunk Cost）\n\n"
                f"{old_buttons}\n\n概念说明。\n\n"
                "## 下一节\n",
                encoding="utf-8",
            )
            result = run_script("render_search_buttons.py", "--rewrite-note", str(note))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Rewrote 1", result.stdout)
            text = note.read_text(encoding="utf-8")
            hrefs = re.findall(r'href="([^"]+)"', text)
            self.assertEqual(parse_qs(urlparse(hrefs[0]).query)["wd"], ["沉没成本"])
            self.assertEqual(parse_qs(urlparse(hrefs[1]).query)["q"], ["沉没成本"])
            self.assertIn("## 下一节", text)

    def test_normalize_vtt_deduplicates_progressive_captions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "sample.vtt"
            output = root / "transcript.md"
            source.write_text(
                "WEBVTT\n\n"
                "00:00:01.000 --> 00:00:03.000\n第一句\n\n"
                "00:00:02.000 --> 00:00:04.000\n第一句话完整了\n\n"
                "00:00:05.000 --> 00:00:07.000\n第二句话\n",
                encoding="utf-8",
            )
            result = run_script("normalize_transcript.py", str(source), str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            text = output.read_text(encoding="utf-8")
            self.assertIn("[00:00:01] 第一句话完整了", text)
            self.assertIn("[00:00:05] 第二句话", text)
            self.assertNotIn("[00:00:01] 第一句\n", text)

    def test_chapterize_covers_all_manifest_chapters(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            transcript = root / "transcript.md"
            output = root / "chapterized.md"
            manifest.write_text(
                json.dumps(
                    {
                        "title": "示例视频",
                        "duration_seconds": 120,
                        "chapters": [
                            {"title": "开场", "start_time": 0, "end_time": 60},
                            {"title": "结论", "start_time": 60, "end_time": 120},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            transcript.write_text(
                "# 视频转写稿\n\n[00:00:10] 第一部分。\n\n[00:01:10] 第二部分。\n",
                encoding="utf-8",
            )
            result = run_script(
                "chapterize_transcript.py", str(manifest), str(transcript), str(output)
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            text = output.read_text(encoding="utf-8")
            self.assertIn("开场", text)
            self.assertIn("第一部分。", text)
            self.assertIn("结论", text)
            self.assertIn("第二部分。", text)

    def test_init_config_uses_real_vault_and_stays_local(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = root / "vault"
            (vault / ".obsidian").mkdir(parents=True)
            output = root / "project-config.yaml"
            result = run_script(
                "init_config.py",
                "--vault",
                str(vault),
                "--target-folder",
                "未分类",
                "--output",
                str(output),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            text = output.read_text(encoding="utf-8")
            self.assertIn(str(vault.resolve()), text)
            self.assertIn('target_folder: "未分类"', text)
            self.assertNotIn("/absolute/path/to/your", text)

    def test_quality_validator_accepts_complete_note(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            note = Path(directory) / "note.md"
            buttons = run_script(
                "render_search_buttons.py",
                "--term",
                "测试概念",
            )
            self.assertEqual(buttons.returncode, 0, buttons.stderr)
            properties = "\n".join(
                [
                    "type: video-note",
                    'title: "测试笔记"',
                    "platform: test",
                    "creator: test",
                    "source: https://example.com/video",
                    "video_id: test-1",
                    "duration: 00:10:00",
                    "transcript_source: manual-subtitles",
                    "source_quality: high",
                    "status: complete",
                    "created: 2026-01-01",
                    "tags: [video-note]",
                ]
            )
            detailed_body = "这是经过完整核对的章节内容，包含论点、解释、例子和边界条件。" * 100
            body = f"""---
{properties}
---

## 一句话主题

测试主题。

## 内容总览

完整覆盖视频内容。

## 时间轴与内容地图

| 时间 | 章节 | 内容 |
| --- | --- | --- |
| [00:00] | 开场 | 介绍主题 |

## 分章节详细提炼

### 00:00 开场

{detailed_body}

## 核心概念与术语

### 测试概念（Test concept）

{buttons.stdout.strip()}

核心概念的定义和适用范围。

## 作者的假设、限制与可能争议

- 本内容仅用于验证结构。

## 复习问题

1. 主题是什么？
2. 主要论点是什么？
3. 使用了什么例子？
4. 有哪些限制？
5. 如何实际应用？

## 知识图谱关键词

#测试概念 #视频笔记 #结构验证

## 提炼质量说明

已对照完整章节阅读稿复核，并通过结构校验。

## 笔记属性

| 属性 | 内容 |
|---|---|
| 类型 | video-note |
| 标题 | 测试笔记 |
| 平台 | test |
| 作者 | test |
| 原视频 | [打开原视频](https://example.com/video) |
| 视频 ID | test-1 |
| 时长 | 00:10:00 |
| 转写来源 | manual-subtitles |
| 来源质量 | high |
| 状态 | complete |
| 笔记创建日期 | 2026-01-01 |
| 标签 | #video-note |
"""
            note.write_text(body, encoding="utf-8")
            result = run_script(
                "validate_note.py",
                str(note),
                "--duration-seconds",
                "600",
                "--expected-chapters",
                "1",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            text = note.read_text(encoding="utf-8")
            note.write_text(
                text.replace(
                    "%E6%B5%8B%E8%AF%95%E6%A6%82%E5%BF%B5",
                    "%E6%B5%8B%E8%AF%95%E6%A6%82%E5%BF%B5%20%E4%B8%AD%E6%96%87",
                    1,
                ),
                encoding="utf-8",
            )
            result = run_script(
                "validate_note.py",
                str(note),
                "--duration-seconds",
                "600",
                "--expected-chapters",
                "1",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Baidu queries must exactly equal", result.stdout)


if __name__ == "__main__":
    unittest.main()
