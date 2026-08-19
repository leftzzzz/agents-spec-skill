from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL_NAME = "agents-spec"
REPOSITORY_NAME = "agents-spec-skill"
SKILL_ROOT = ROOT / "skills" / SKILL_NAME


class SkillPackageTests(unittest.TestCase):
    def test_skill_frontmatter_has_expected_name_and_only_supported_keys(self) -> None:
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        _, frontmatter, _ = text.split("---", maxsplit=2)
        fields = {
            match.group(1): match.group(2).strip()
            for match in re.finditer(
                r"(?m)^([A-Za-z][A-Za-z0-9_-]*):\s*(.+)$", frontmatter
            )
        }

        self.assertEqual(set(fields), {"name", "description"})
        self.assertEqual(fields["name"], SKILL_NAME)
        self.assertTrue(fields["description"])

    def test_openai_metadata_invokes_current_skill_name(self) -> None:
        text = (SKILL_ROOT / "agents/openai.yaml").read_text(encoding="utf-8")

        self.assertIn(f"${SKILL_NAME}", text)
        self.assertIn('display_name: "AGENTS Spec"', text)

    def test_runtime_files_do_not_reference_previous_skill_names(self) -> None:
        runtime_files = [
            SKILL_ROOT / "SKILL.md",
            SKILL_ROOT / "agents/openai.yaml",
            SKILL_ROOT / "scripts/audit_agents_md.py",
        ]

        for path in runtime_files:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("organize-agents-md", text)
                self.assertNotIn("organize-agents-spec", text)

    def test_public_repository_metadata_matches_skill(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        readme_zh = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

        self.assertIn(f"github.com/leftzzzz/{REPOSITORY_NAME}", readme)
        self.assertIn(f"${SKILL_NAME}", readme)
        self.assertIn(
            f"npx skills add https://github.com/leftzzzz/{REPOSITORY_NAME}", readme
        )
        self.assertIn("[English](README.md) | [简体中文](README.zh-CN.md)", readme)
        self.assertIn("[English](README.md) | **简体中文**", readme_zh)
        self.assertIn("## Language support", readme)
        self.assertIn("## 中文支持", readme_zh)
        self.assertNotIn("## 中文支持", readme)
        self.assertTrue(license_text.startswith("MIT License\n"))
        self.assertIn("Copyright (c) 2026 leftzzzz", license_text)
        self.assertEqual(
            license_text, (SKILL_ROOT / "LICENSE.txt").read_text(encoding="utf-8")
        )

    def test_readmes_use_one_generic_install_command_for_supported_agents(
        self,
    ) -> None:
        readmes = {
            "English": (ROOT / "README.md").read_text(encoding="utf-8"),
            "Chinese": (ROOT / "README.zh-CN.md").read_text(encoding="utf-8"),
        }
        command = f"npx skills add https://github.com/leftzzzz/{REPOSITORY_NAME}"
        named_skill_command = f'{command} --skill "{SKILL_NAME}"'

        for language, readme in readmes.items():
            with self.subTest(language=language):
                self.assertIn(command, readme)
                self.assertIn(named_skill_command, readme)
                self.assertIn("`skills/`", readme)
                self.assertNotRegex(readme, r"npx skills add[^\n]*--agent(?:\s|=)")

    def test_native_manifests_are_thin_and_share_one_skill_directory(self) -> None:
        manifest_paths = [
            ROOT / ".codex-plugin/plugin.json",
            ROOT / ".claude-plugin/plugin.json",
            ROOT / ".cursor-plugin/plugin.json",
        ]
        manifests = []
        for path in manifest_paths:
            with self.subTest(path=path):
                payload = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(payload["name"], SKILL_NAME)
                self.assertEqual(payload["version"], "0.1.0")
                manifests.append(payload)

        self.assertEqual(manifests[0]["skills"], "./skills/")
        self.assertEqual(manifests[2]["skills"], "./skills/")
        self.assertEqual(list(ROOT.rglob("SKILL.md")), [SKILL_ROOT / "SKILL.md"])

    def test_native_marketplaces_reference_the_repository_plugin(self) -> None:
        for path in [
            ROOT / ".claude-plugin/marketplace.json",
            ROOT / ".cursor-plugin/marketplace.json",
        ]:
            with self.subTest(path=path):
                payload = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(payload["name"], SKILL_NAME)
                self.assertEqual(len(payload["plugins"]), 1)
                self.assertEqual(payload["plugins"][0]["name"], SKILL_NAME)
                self.assertEqual(payload["plugins"][0]["source"], "./")

    def test_skill_directory_has_open_format_license_and_runtime_files(self) -> None:
        self.assertTrue((SKILL_ROOT / "SKILL.md").is_file())
        self.assertTrue((SKILL_ROOT / "LICENSE.txt").is_file())
        self.assertTrue((SKILL_ROOT / "agents/openai.yaml").is_file())
        self.assertTrue((SKILL_ROOT / "scripts/audit_agents_md.py").is_file())


if __name__ == "__main__":
    unittest.main()
