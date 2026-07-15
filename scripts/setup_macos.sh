#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "This installer currently supports Apple Silicon Macs only."
  echo "Other systems can still use the skill with platform subtitles or a compatible transcription tool."
  exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install it from https://brew.sh and run this script again."
  exit 1
fi

brew install yt-dlp ffmpeg uv

if ! command -v mlx_whisper >/dev/null 2>&1 && ! command -v mlx-whisper >/dev/null 2>&1; then
  uv tool install mlx-whisper
fi

python3 "$SCRIPT_DIR/doctor.py" --skip-config --require-asr

echo
echo "Dependencies are ready. Next, create project-config.yaml with init_config.py."
