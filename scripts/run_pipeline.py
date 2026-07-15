#!/usr/bin/env python3
"""Run acquisition, subtitle fallback, ASR, normalization, and chapterization once."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def one_match(folder: Path, patterns: list[str]) -> Path | None:
    for pattern in patterns:
        matches = sorted(folder.glob(pattern))
        if matches:
            return matches[0]
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--languages", default=r"zh-Hans,zh-Hant,zh.*,en.*")
    parser.add_argument("--language")
    parser.add_argument("--model", default="mlx-community/whisper-large-v3-turbo")
    parser.add_argument("--cookies-from-browser")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    python = sys.executable
    args.output.mkdir(parents=True, exist_ok=True)
    total_started = time.perf_counter()

    prepare = [
        python, str(script_dir / "prepare_video.py"), args.url,
        "--output", str(args.output), "--languages", args.languages,
        "--audio-if-no-subs",
    ]
    if args.cookies_from_browser:
        prepare += ["--cookies-from-browser", args.cookies_from_browser]
    run(prepare)

    manifest_path = args.output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = one_match(args.output, ["source*.vtt", "source*.srt"])
    asr_seconds = 0.0
    if source is None:
        audio = one_match(args.output, ["audio.mp3", "audio.m4a", "audio.*"])
        mlx = shutil.which("mlx_whisper")
        if mlx is None:
            local_mlx = Path.home() / ".local" / "bin" / "mlx_whisper"
            mlx = str(local_mlx) if local_mlx.exists() else None
        if audio is None or mlx is None:
            raise RuntimeError("Audio fallback or mlx_whisper executable is unavailable")
        asr_started = time.perf_counter()
        command = [
            mlx, str(audio), "--model", args.model,
            "--output-dir", str(args.output), "--output-name", "whisper",
            "--output-format", "json", "--verbose", "False",
            "--word-timestamps", "True",
        ]
        if args.language:
            command += ["--language", args.language]
        run(command)
        asr_seconds = time.perf_counter() - asr_started
        source = args.output / "whisper.json"

    normalize_started = time.perf_counter()
    transcript = args.output / "transcript.md"
    run([python, str(script_dir / "normalize_transcript.py"), str(source), str(transcript)])
    chapterized = args.output / "chapterized.md"
    run([
        python, str(script_dir / "chapterize_transcript.py"),
        str(manifest_path), str(transcript), str(chapterized),
    ])
    normalize_seconds = time.perf_counter() - normalize_started

    timings = {
        "prepare_seconds": manifest.get("timings", {}).get("total_prepare_seconds"),
        "asr_seconds": round(asr_seconds, 3),
        "normalize_and_chapterize_seconds": round(normalize_seconds, 3),
        "pipeline_total_seconds": round(time.perf_counter() - total_started, 3),
        "transcript_source": manifest.get("selected_subtitle_kind") or "local-asr",
        "model": args.model if asr_seconds else None,
    }
    timings_path = args.output / "timings.json"
    timings_path.write_text(json.dumps(timings, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "manifest": str(manifest_path),
        "chapterized": str(chapterized),
        "timings": timings,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
