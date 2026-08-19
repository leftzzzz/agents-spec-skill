from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).parents[1]
    / "skills"
    / "agents-spec"
    / "scripts"
    / "audit_agents_md.py"
)


class AuditAgentsMdTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write(self, relative_path: str, text: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def create_valid_layout(self) -> None:
        self.write(
            "AGENTS.md",
            """# Agent instructions

## Documentation routing

| Need | Read or search first |
| --- | --- |
| Search current behavior, constraints, and rules | [Spec index](docs/specs/AGENTS.md) |
| Search product requirements, user intent, and acceptance criteria | [Requirement index](docs/requirements/AGENTS.md) |
| Search technical architecture, implementation, and rationale | [Technical index](docs/technical/AGENTS.md) |
""",
        )
        self.write(
            "docs/specs/AGENTS.md",
            """# Spec index

Search current behavior, constraints, and rules here before changing implementation.

## Documents

- [Orders](projects/orders.md)
""",
        )
        self.write(
            "docs/specs/projects/orders.md",
            """# Orders

An accepted order must retain its immutable order number.
""",
        )
        self.write(
            "docs/requirements/AGENTS.md",
            """# Requirement documents

Search requirement documents here for product intent, user needs, and acceptance criteria.
""",
        )
        self.write(
            "docs/technical/AGENTS.md",
            """# Technical documents

Search technical documents here for architecture, implementation design, and rationale.
""",
        )

    def run_guard(
        self, *arguments: str
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object] | None]:
        command = [sys.executable, str(SCRIPT), str(self.root), *arguments]
        if "--json" not in arguments:
            command.append("--json")
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        payload = (
            json.loads(completed.stdout)
            if completed.stdout.strip().startswith("{")
            else None
        )
        return completed, payload

    def error_codes(self, payload: dict[str, object]) -> set[str]:
        return {item["code"] for item in payload["errors"]}  # type: ignore[index]

    def warning_codes(self, payload: dict[str, object]) -> set[str]:
        return {item["code"] for item in payload["warnings"]}  # type: ignore[index]

    def test_valid_layout_does_not_require_claude_md(self) -> None:
        self.create_valid_layout()

        completed, payload = self.run_guard("--check")

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["errors"], [])
        self.assertFalse((self.root / "CLAUDE.md").exists())

    def test_fix_without_explicit_add_claude_does_not_create_file(self) -> None:
        self.create_valid_layout()

        completed, payload = self.run_guard("--fix")

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(payload["actions"], [])
        self.assertFalse((self.root / "CLAUDE.md").exists())

    def test_explicit_add_claude_creates_relative_symlink(self) -> None:
        self.create_valid_layout()

        completed, payload = self.run_guard("--fix", "--add-claude")

        claude = self.root / "CLAUDE.md"
        self.assertEqual(completed.returncode, 0, completed.stdout)
        if claude.is_symlink():
            self.assertEqual(os.readlink(claude), "AGENTS.md")
            self.assertIn(
                "created relative symlink CLAUDE.md -> AGENTS.md", payload["actions"]
            )
        else:
            self.assertEqual(claude.read_text(encoding="utf-8"), "@AGENTS.md\n")
            self.assertIn("created CLAUDE.md importing @AGENTS.md", payload["actions"])

    def test_add_claude_flag_requires_fix_mode(self) -> None:
        self.create_valid_layout()

        completed, _ = self.run_guard("--add-claude")

        self.assertEqual(completed.returncode, 2)
        self.assertFalse((self.root / "CLAUDE.md").exists())

    def test_existing_invalid_claude_file_is_not_overwritten(self) -> None:
        self.create_valid_layout()
        claude = self.write("CLAUDE.md", "# Claude-only instructions\n")

        completed, payload = self.run_guard("--fix", "--add-claude")

        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("claude.missing_import", self.error_codes(payload))
        self.assertEqual(
            claude.read_text(encoding="utf-8"), "# Claude-only instructions\n"
        )

    def test_existing_wrong_claude_symlink_is_not_replaced(self) -> None:
        self.create_valid_layout()
        self.write("OTHER.md", "# Other instructions\n")
        claude = self.root / "CLAUDE.md"
        claude.symlink_to("OTHER.md")

        completed, payload = self.run_guard("--fix", "--add-claude")

        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("claude.wrong_symlink", self.error_codes(payload))
        self.assertEqual(os.readlink(claude), "OTHER.md")

    def test_regular_claude_import_is_valid(self) -> None:
        self.create_valid_layout()
        self.write("CLAUDE.md", "@AGENTS.md\n\n# Claude-specific additions\n")

        completed, payload = self.run_guard("--check")

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertNotIn("claude.missing_import", self.error_codes(payload))

    def test_unindexed_spec_is_a_hard_error(self) -> None:
        self.create_valid_layout()
        self.write(
            "docs/specs/projects/unindexed.md",
            "# Unindexed\n\nThis is a current rule.\n",
        )

        completed, payload = self.run_guard("--check")

        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("spec.unindexed", self.error_codes(payload))

    def test_spec_can_have_multiple_distinct_trigger_links(self) -> None:
        self.create_valid_layout()
        index = self.root / "docs/specs/AGENTS.md"
        index.write_text(
            index.read_text(encoding="utf-8")
            + "- [When changing order identity](projects/orders.md)\n",
            encoding="utf-8",
        )

        completed, payload = self.run_guard("--check")

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertNotIn("spec.unindexed", self.error_codes(payload))
        self.assertNotIn("spec.duplicate_index_row", self.warning_codes(payload))

    def test_markdown_link_with_balanced_parentheses_is_resolved(self) -> None:
        self.create_valid_layout()
        original = self.root / "docs/specs/projects/orders.md"
        renamed = self.root / "docs/specs/projects/orders(v2).md"
        renamed.write_text(original.read_text(encoding="utf-8"), encoding="utf-8")
        original.unlink()
        index = self.root / "docs/specs/AGENTS.md"
        index.write_text(
            index.read_text(encoding="utf-8").replace(
                "projects/orders.md", "projects/orders(v2).md"
            ),
            encoding="utf-8",
        )

        completed, payload = self.run_guard("--check")

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(payload["errors"], [])

    def test_markdown_link_with_angle_destination_and_spaces_is_resolved(self) -> None:
        self.create_valid_layout()
        original = self.root / "docs/specs/projects/orders.md"
        renamed = self.root / "docs/specs/projects/order notes.md"
        renamed.write_text(original.read_text(encoding="utf-8"), encoding="utf-8")
        original.unlink()
        index = self.root / "docs/specs/AGENTS.md"
        index.write_text(
            index.read_text(encoding="utf-8").replace(
                "projects/orders.md", "<projects/order notes.md>"
            ),
            encoding="utf-8",
        )

        completed, payload = self.run_guard("--check")

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(payload["errors"], [])

    def test_uppercase_spec_purpose_is_accepted(self) -> None:
        self.create_valid_layout()
        root_agents = self.root / "AGENTS.md"
        root_agents.write_text(
            root_agents.read_text(encoding="utf-8").replace(
                "Search current behavior", "Search Current behavior"
            ),
            encoding="utf-8",
        )

        completed, payload = self.run_guard("--check")

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertNotIn("root.navigation_trigger_missing", self.warning_codes(payload))

    def test_english_failure_mode_without_validation_is_a_warning(self) -> None:
        self.create_valid_layout()
        agents = self.root / "AGENTS.md"
        agents.write_text(
            agents.read_text(encoding="utf-8")
            + "\n## Reliability\n\nPrevent this production incident from recurring.\n",
            encoding="utf-8",
        )

        completed, payload = self.run_guard("--check")

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("failure.missing_validation", self.warning_codes(payload))

    def test_exact_duplicate_spec_index_row_is_a_warning(self) -> None:
        self.create_valid_layout()
        index = self.root / "docs/specs/AGENTS.md"
        index.write_text(
            index.read_text(encoding="utf-8") + "- [Orders](projects/orders.md)\n",
            encoding="utf-8",
        )

        completed, payload = self.run_guard("--check")

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("spec.duplicate_index_row", self.warning_codes(payload))

    def test_byte_identical_specs_are_a_hard_error(self) -> None:
        self.create_valid_layout()
        original = (self.root / "docs/specs/projects/orders.md").read_text(
            encoding="utf-8"
        )
        self.write("docs/specs/projects/orders-copy.md", original)
        index = self.root / "docs/specs/AGENTS.md"
        index.write_text(
            index.read_text(encoding="utf-8")
            + "- [Orders copy](projects/orders-copy.md)\n",
            encoding="utf-8",
        )

        completed, payload = self.run_guard("--check")

        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("spec.exact_duplicate", self.error_codes(payload))

    def test_legacy_managed_markdown_is_a_hard_error(self) -> None:
        self.create_valid_layout()
        self.write(".agents/projects/legacy.md", "# Legacy rule\n")

        completed, payload = self.run_guard("--check")

        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("legacy.managed_markdown", self.error_codes(payload))

    def test_missing_domain_navigation_is_a_hard_error(self) -> None:
        self.create_valid_layout()
        root_agents = self.root / "AGENTS.md"
        root_agents.write_text(
            root_agents.read_text(encoding="utf-8").replace(
                "| Search technical architecture, implementation, and rationale | [Technical index](docs/technical/AGENTS.md) |\n",
                "",
            ),
            encoding="utf-8",
        )

        completed, payload = self.run_guard("--check")

        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("root.domain_index_missing", self.error_codes(payload))

    def test_domain_path_without_search_purpose_is_a_warning(self) -> None:
        self.create_valid_layout()
        root_agents = self.root / "AGENTS.md"
        root_agents.write_text(
            root_agents.read_text(encoding="utf-8").replace(
                "| Search product requirements, user intent, and acceptance criteria | [Requirement index](docs/requirements/AGENTS.md) |",
                "| Search these documents | [Requirement index](docs/requirements/AGENTS.md) |",
            ),
            encoding="utf-8",
        )

        completed, payload = self.run_guard("--check")

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("root.navigation_trigger_missing", self.warning_codes(payload))

    def test_link_only_domain_entrypoint_is_a_warning(self) -> None:
        self.create_valid_layout()
        self.write("docs/requirements/order.md", "# Order requirement\n")
        self.write(
            "docs/requirements/AGENTS.md",
            "# Requirement documents\n\n- [Order](order.md)\n",
        )

        completed, payload = self.run_guard("--check")

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("domain.link_only_stub", self.warning_codes(payload))

    def test_unindexed_business_requirement_is_outside_spec_audit(self) -> None:
        self.create_valid_layout()
        self.write(
            "docs/requirements/order-discount.md",
            "# Order discount\n\nCustomers should receive the agreed promotional discount.\n",
        )

        completed, payload = self.run_guard("--check")

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertNotIn("spec.unindexed", self.error_codes(payload))

    def test_routing_example_inside_code_fence_does_not_satisfy_root_index(
        self,
    ) -> None:
        self.create_valid_layout()
        self.write(
            "AGENTS.md",
            """# Agent instructions

```markdown
Search current rules in docs/specs/AGENTS.md.
Search product requirements in docs/requirements/AGENTS.md.
Search technical architecture in docs/technical/AGENTS.md.
```
""",
        )

        completed, payload = self.run_guard("--check")

        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("root.domain_index_missing", self.error_codes(payload))


if __name__ == "__main__":
    unittest.main()
