from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryTests(unittest.TestCase):
    def test_required_release_files_exist(self) -> None:
        required = (
            ".gitignore",
            ".github/workflows/ci.yml",
            "CONTRIBUTING.md",
            "LICENSE",
            "README.md",
            "SKILL.md",
            "agents/openai.yaml",
            "references/project-config.example.yaml",
            "references/quality-checklist.md",
            "references/summary-template.md",
            "references/video-type-guides.md",
            "scripts/doctor.py",
            "scripts/init_config.py",
            "scripts/setup_macos.sh",
            "scripts/run_pipeline.py",
            "scripts/validate_note.py",
        )
        missing = [name for name in required if not (ROOT / name).is_file()]
        self.assertEqual(missing, [])

    def test_license_is_mit(self) -> None:
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertTrue(license_text.startswith("MIT License\n"))
        self.assertIn("Copyright (c) 2026 Chen Zhang", license_text)

    def test_readme_puts_disclaimer_first(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        first_level_two_heading = next(
            line for line in readme.splitlines() if line.startswith("## ")
        )
        self.assertEqual(first_level_two_heading, "## 免责声明与版权说明")
        self.assertLess(readme.splitlines().index("## 免责声明与版权说明"), 20)

    def test_skill_frontmatter_is_minimal(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill.startswith("---\n"))
        _, frontmatter, _ = skill.split("---", 2)
        keys = {
            line.split(":", 1)[0].strip()
            for line in frontmatter.splitlines()
            if ":" in line
        }
        self.assertEqual(keys, {"name", "description"})
        self.assertIn("name: summarize-learning-videos", frontmatter)

    def test_public_files_do_not_contain_personal_paths(self) -> None:
        forbidden = ("/Users/" + "zhangchen", "iCloud~md~" + "obsidian")
        suffixes = {".md", ".py", ".yaml", ".yml", ".sh"}
        offenders: list[str] = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or path.suffix not in suffixes:
                continue
            if "tests" in path.relative_to(ROOT).parts:
                continue
            text = path.read_text(encoding="utf-8")
            if any(value in text for value in forbidden):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
