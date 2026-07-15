#!/usr/bin/env python3
"""Collect video metadata, the best available subtitles, and optional audio."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


def run(command: list[str], capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def choose_language(available: dict, preferences: list[str]) -> str | None:
    keys = list(available)
    for preference in preferences:
        pattern = re.compile(preference, re.IGNORECASE)
        for key in keys:
            if pattern.fullmatch(key) or pattern.match(key):
                return key
    return keys[0] if keys else None


def duration_text(seconds: int | float | None) -> str | None:
    if seconds is None:
        return None
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--languages", default=r"zh-Hans,zh-Hant,zh.*,en.*")
    parser.add_argument("--audio", action="store_true")
    parser.add_argument("--audio-if-no-subs", action="store_true")
    parser.add_argument("--cookies-from-browser")
    args = parser.parse_args()

    for executable in ("yt-dlp", "ffmpeg"):
        if not shutil.which(executable):
            parser.error(f"Missing required executable: {executable}")

    args.output.mkdir(parents=True, exist_ok=True)
    common = ["--no-playlist"]
    if args.cookies_from_browser:
        common += ["--cookies-from-browser", args.cookies_from_browser]

    started = time.perf_counter()
    metadata_started = time.perf_counter()
    result = run(["yt-dlp", *common, "--dump-single-json", "--skip-download", args.url], capture=True)
    metadata_seconds = time.perf_counter() - metadata_started
    raw = json.loads(result.stdout)
    manual = raw.get("subtitles") or {}
    automatic = raw.get("automatic_captions") or {}
    preferences = [item.strip() for item in args.languages.split(",") if item.strip()]
    language = choose_language(manual, preferences)
    subtitle_kind = "manual" if language else None
    if not language:
        language = choose_language(automatic, preferences)
        subtitle_kind = "automatic" if language else None

    manifest = {
        "id": raw.get("id"),
        "title": raw.get("title"),
        "description": raw.get("description"),
        "webpage_url": raw.get("webpage_url") or args.url,
        "extractor": raw.get("extractor_key") or raw.get("extractor"),
        "uploader": raw.get("uploader") or raw.get("channel"),
        "uploader_id": raw.get("uploader_id") or raw.get("channel_id"),
        "upload_date": raw.get("upload_date"),
        "duration_seconds": raw.get("duration"),
        "duration": duration_text(raw.get("duration")),
        "chapters": raw.get("chapters") or [],
        "selected_subtitle_language": language,
        "selected_subtitle_kind": subtitle_kind,
        "available_manual_subtitles": sorted(manual),
        "available_automatic_captions": sorted(automatic),
        "prepared_audio": False,
        "timings": {"metadata_seconds": round(metadata_seconds, 3)},
    }

    if language:
        subtitle_started = time.perf_counter()
        subtitle_flag = "--write-subs" if subtitle_kind == "manual" else "--write-auto-subs"
        run([
            "yt-dlp", *common, "--skip-download", subtitle_flag,
            "--sub-langs", language, "--sub-format", "vtt",
            "-o", str(args.output / "source.%(ext)s"), args.url,
        ])
        manifest["timings"]["subtitle_seconds"] = round(time.perf_counter() - subtitle_started, 3)

    needs_audio = args.audio or (args.audio_if_no_subs and not language)
    if needs_audio:
        audio_started = time.perf_counter()
        run([
            "yt-dlp", *common, "-f", "bestaudio/best", "-x",
            "--audio-format", "mp3", "--audio-quality", "5",
            "-o", str(args.output / "audio.%(ext)s"), args.url,
        ])
        manifest["prepared_audio"] = True
        manifest["timings"]["audio_seconds"] = round(time.perf_counter() - audio_started, 3)

    manifest["timings"]["total_prepare_seconds"] = round(time.perf_counter() - started, 3)
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        if error.stderr:
            print(error.stderr, file=sys.stderr)
        raise
