#!/usr/bin/env python3
"""Check whether the video-summary skill is ready to run on this machine."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Check:
    name: str
    status: str
    detail: str


def read_yaml_scalar(text: str, key: str) -> str | None:
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*:\s*(.*?)\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return None
    value = match.group(1).split(" #", 1)[0].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value or None


def discover_config(explicit: str | None) -> Path | None:
    candidates = [
        explicit,
        os.environ.get("VIDEO_NOTES_CONFIG"),
        str(Path.cwd() / "project-config.yaml"),
    ]
    for candidate in candidates:
        if candidate:
            path = Path(candidate).expanduser()
            if path.exists():
                return path.resolve()
    return None


def run_checks(config: str | None, skip_config: bool, require_asr: bool) -> list[Check]:
    checks: list[Check] = []

    python_ok = sys.version_info >= (3, 10)
    checks.append(Check("Python", "pass" if python_ok else "fail", platform.python_version()))

    required_files = [
        "SKILL.md",
        "README.md",
        "LICENSE",
        "agents/openai.yaml",
        "references/summary-template.md",
        "references/quality-checklist.md",
        "scripts/run_pipeline.py",
        "scripts/validate_note.py",
    ]
    missing = [item for item in required_files if not (SKILL_ROOT / item).is_file()]
    checks.append(
        Check(
            "Skill files",
            "fail" if missing else "pass",
            "missing: " + ", ".join(missing) if missing else str(SKILL_ROOT),
        )
    )

    for command in ("yt-dlp", "ffmpeg"):
        location = shutil.which(command)
        checks.append(Check(command, "pass" if location else "fail", location or "not found in PATH"))

    is_apple_silicon = platform.system() == "Darwin" and platform.machine() == "arm64"
    mlx_location = shutil.which("mlx_whisper") or shutil.which("mlx-whisper")
    if mlx_location:
        checks.append(Check("Local ASR", "pass", mlx_location))
    elif require_asr:
        checks.append(Check("Local ASR", "fail", "mlx-whisper not found"))
    elif is_apple_silicon:
        checks.append(Check("Local ASR", "warn", "mlx-whisper not found; install it for local transcription"))
    else:
        checks.append(
            Check(
                "Local ASR",
                "warn",
                "mlx-whisper targets Apple Silicon; use subtitles or configure another transcription path",
            )
        )

    if skip_config:
        checks.append(Check("Project config", "skip", "skipped by request"))
        return checks

    config_path = discover_config(config)
    if not config_path:
        checks.append(
            Check(
                "Project config",
                "warn",
                "not found; run init_config.py or set VIDEO_NOTES_CONFIG",
            )
        )
        return checks

    try:
        config_text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        checks.append(Check("Project config", "fail", f"cannot read {config_path}: {exc}"))
        return checks

    checks.append(Check("Project config", "pass", str(config_path)))
    vault_value = read_yaml_scalar(config_text, "vault_root")
    if not vault_value:
        checks.append(Check("Obsidian vault", "fail", "vault_root is missing from the config"))
        return checks

    vault = Path(vault_value).expanduser()
    if not vault.is_dir():
        checks.append(Check("Obsidian vault", "fail", f"directory does not exist: {vault}"))
        return checks
    if not (vault / ".obsidian").is_dir():
        checks.append(Check("Obsidian vault", "warn", f".obsidian directory not found in {vault}"))
    elif not os.access(vault, os.W_OK):
        checks.append(Check("Obsidian vault", "fail", f"directory is not writable: {vault}"))
    else:
        checks.append(Check("Obsidian vault", "pass", str(vault.resolve())))

    target_folder = read_yaml_scalar(config_text, "target_folder") or "."
    target = vault / target_folder
    if target.exists() and not target.is_dir():
        checks.append(Check("Output folder", "fail", f"not a directory: {target}"))
    elif target.is_dir() and not os.access(target, os.W_OK):
        checks.append(Check("Output folder", "fail", f"not writable: {target}"))
    elif target.is_dir():
        checks.append(Check("Output folder", "pass", str(target.resolve())))
    else:
        checks.append(Check("Output folder", "warn", f"will be created on first use: {target}"))

    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="Path to project-config.yaml")
    parser.add_argument("--skip-config", action="store_true", help="Skip Obsidian config checks")
    parser.add_argument("--require-asr", action="store_true", help="Treat missing local ASR as a failure")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    checks = run_checks(args.config, args.skip_config, args.require_asr)
    if args.json:
        print(json.dumps([asdict(item) for item in checks], ensure_ascii=False, indent=2))
    else:
        icons = {"pass": "✓", "warn": "!", "fail": "✗", "skip": "-"}
        for item in checks:
            print(f"{icons[item.status]} {item.name}: {item.detail}")
        failures = sum(item.status == "fail" for item in checks)
        warnings = sum(item.status == "warn" for item in checks)
        print(f"\nResult: {failures} failure(s), {warnings} warning(s)")

    return 1 if any(item.status == "fail" for item in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
