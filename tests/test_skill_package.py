from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILL_NAME = "organize-agents-spec"


class SkillPackageTests(unittest.TestCase):
    def test_skill_frontmatter_has_expected_name_and_only_supported_keys(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        _, frontmatter, _ = text.split("---", maxsplit=2)
        fields = {
            match.group(1): match.group(2).strip()
            for match in re.finditer(r"(?m)^([A-Za-z][A-Za-z0-9_-]*):\s*(.+)$", frontmatter)
        }

        self.assertEqual(set(fields), {"name", "description"})
        self.assertEqual(fields["name"], SKILL_NAME)
        self.assertTrue(fields["description"])

    def test_openai_metadata_invokes_current_skill_name(self) -> None:
        text = (ROOT / "agents/openai.yaml").read_text(encoding="utf-8")

        self.assertIn(f"${SKILL_NAME}", text)
        self.assertIn('display_name: "Organize Agent Specs"', text)

    def test_runtime_files_do_not_reference_previous_skill_name(self) -> None:
        runtime_files = [
            ROOT / "SKILL.md",
            ROOT / "agents/openai.yaml",
            ROOT / "scripts/audit_agents_md.py",
        ]

        for path in runtime_files:
            with self.subTest(path=path):
                self.assertNotIn("organize-agents-md", path.read_text(encoding="utf-8"))

    def test_public_repository_metadata_matches_skill(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

        self.assertIn(f"github.com/leftzzzz/{SKILL_NAME}.git", readme)
        self.assertIn(f"${SKILL_NAME}", readme)
        self.assertTrue(license_text.startswith("MIT License\n"))
        self.assertIn("Copyright (c) 2026 leftzzzz", license_text)


if __name__ == "__main__":
    unittest.main()
