#!/usr/bin/env python3
"""Create a local project-config.yaml without publishing personal paths."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_CONFIG = SKILL_ROOT / "references" / "project-config.example.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", help="Absolute path to an Obsidian vault")
    parser.add_argument("--target-folder", default=".", help="Folder inside the vault; default: vault root")
    parser.add_argument("--output", default="project-config.yaml", help="Config file to create")
    parser.add_argument("--force", action="store_true", help="Replace an existing output file")
    args = parser.parse_args()

    vault_input = args.vault or input("Obsidian vault path: ").strip()
    if not vault_input:
        parser.error("an Obsidian vault path is required")

    vault = Path(vault_input).expanduser().resolve()
    if not vault.is_dir():
        parser.error(f"vault directory does not exist: {vault}")
    if not (vault / ".obsidian").is_dir():
        parser.error(f"this does not look like an Obsidian vault (.obsidian missing): {vault}")

    output = Path(args.output).expanduser()
    if output.exists() and not args.force:
        parser.error(f"output already exists: {output}; use --force to replace it")

    template = EXAMPLE_CONFIG.read_text(encoding="utf-8")
    template = template.replace(
        'vault_root: "/absolute/path/to/your/ObsidianVault"',
        f"vault_root: {json.dumps(str(vault), ensure_ascii=False)}",
    )
    template = template.replace(
        'target_folder: "."',
        f"target_folder: {json.dumps(args.target_folder, ensure_ascii=False)}",
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(template, encoding="utf-8")
    print(f"Created: {output.resolve()}")
    print("This file is ignored by Git because it may contain a personal path.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
