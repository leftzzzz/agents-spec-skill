#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit


WARN_BYTES_DEFAULT = 24576
MAX_BYTES_DEFAULT = 32768
DOMAIN_INDEXES = {
    "specs": Path("docs/specs/AGENTS.md"),
    "requirements": Path("docs/requirements/AGENTS.md"),
    "technical": Path("docs/technical/AGENTS.md"),
}
LEGACY_SPEC_DIRS = (Path(".agents/projects"), Path(".agents/references"))
IGNORED_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    "vendor",
    "runtime",
    "__pycache__",
}
MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]*\]\(\s*(<[^>]+>|[^)\s]+)")
INLINE_CODE_PATTERN = re.compile(r"`([^`\n]+)`")
CLAUDE_IMPORT_PATTERN = re.compile(r"(?m)^\s*@AGENTS\.md\s*$")
SEARCH_ACTION_PATTERN = re.compile(
    r"read|search|check|inspect|consult|look\s+up|读取|阅读|查阅|检索|搜索|查找|核对|先查|查看",
    re.IGNORECASE,
)
DOMAIN_PURPOSE_PATTERNS = {
    "specs": re.compile(r"current|active|behavior|constraint|rule|boundary|contract|当前|现行|行为|约束|规则|边界"),
    "requirements": re.compile(
        r"product|user|acceptance|intent|产品|用户|验收|意图|为什么",
        re.IGNORECASE,
    ),
    "technical": re.compile(
        r"architecture|implementation|design|rationale|tradeoff|架构|实现|方案|设计|原因|权衡",
        re.IGNORECASE,
    ),
}
KNOWN_FAILURE_PATTERN = re.compile(r"此前调到|曾经|不要再|不能再|复发|覆盖生产|绕过|事故|误判")
VALIDATION_PATTERN = re.compile(
    r"python|node|pnpm|npm|yarn|scripts/|\.test\.|test|lint|smoke|e2e|deploy|验收|测试|证据|门禁|检查|docs/|\.md",
    re.IGNORECASE,
)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args()

    if args.add_claude and not args.fix:
        parser.error("--add-claude is valid only with --fix")
    if args.warn_bytes < 0 or args.max_bytes < 0:
        parser.error("byte thresholds must be non-negative")
    if args.warn_bytes > args.max_bytes:
        parser.error("--warn-bytes cannot exceed --max-bytes")

    try:
        root = Path(args.root).resolve()
        if not root.is_dir():
            raise ValueError(f"repository root is not a directory: {root}")

        fix_errors: list[dict[str, str]] = []
        fix_warnings: list[dict[str, str]] = []
        actions: list[str] = []
        if args.fix:
            fix_errors, fix_warnings, actions = apply_fixes(root, add_claude=args.add_claude)

        report = build_report(root, args.max_bytes, args.warn_bytes)
        report["mode"] = "fix" if args.fix else "check"
        report["errors"] = fix_errors + report["errors"]
        report["warnings"] = fix_warnings + report["warnings"]
        report["actions"] = actions

        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print_text_report(report)
        return 1 if report["errors"] else 0
    except (OSError, UnicodeError, ValueError) as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "mode": "fix" if args.fix else "check",
                        "errors": [issue("internal.failure", str(exc))],
                        "warnings": [],
                        "actions": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(f"agent documentation guard failed: {exc}", file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate cross-agent AGENTS.md routing and SDD documentation structure."
    )
    parser.add_argument("root", nargs="?", default=".", help="Repository root to scan.")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="Validate without modifying files (default).")
    modes.add_argument("--fix", action="store_true", help="Apply explicitly selected deterministic fixes, then validate.")
    parser.add_argument(
        "--add-claude",
        action="store_true",
        help="With --fix, add missing CLAUDE.md after an explicit user request.",
    )
    parser.add_argument("--max-bytes", type=int, default=MAX_BYTES_DEFAULT, help="Maximum entrypoint warning threshold.")
    parser.add_argument("--warn-bytes", type=int, default=WARN_BYTES_DEFAULT, help="Practical entrypoint byte budget.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser


def apply_fixes(
    root: Path,
    *,
    add_claude: bool,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[str]]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    actions: list[str] = []

    if not add_claude:
        return errors, warnings, actions

    root_agents = root / "AGENTS.md"
    claude = root / "CLAUDE.md"
    if path_lexists(claude):
        return errors, warnings, actions
    if not root_agents.is_file():
        errors.append(
            issue(
                "claude.add_requires_agents",
                "cannot add CLAUDE.md because root AGENTS.md does not exist",
                "CLAUDE.md",
            )
        )
        return errors, warnings, actions

    try:
        claude.symlink_to("AGENTS.md")
        actions.append("created relative symlink CLAUDE.md -> AGENTS.md")
    except (NotImplementedError, OSError) as symlink_error:
        try:
            with claude.open("x", encoding="utf-8") as fallback_file:
                fallback_file.write("@AGENTS.md\n")
            actions.append("created CLAUDE.md importing @AGENTS.md")
            warnings.append(
                issue(
                    "claude.symlink_fallback",
                    f"symlink creation failed; used @AGENTS.md import fallback: {symlink_error}",
                    "CLAUDE.md",
                )
            )
        except OSError as fallback_error:
            errors.append(
                issue(
                    "claude.add_failed",
                    f"could not create symlink or import fallback: {fallback_error}",
                    "CLAUDE.md",
                )
            )

    return errors, warnings, actions


def build_report(root: Path, max_bytes: int, warn_bytes: int) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    validate_root_entrypoint(root, errors, warnings)
    validate_domain_entrypoints(root, errors, warnings)
    spec_files = validate_spec_index(root, errors, warnings)
    validate_legacy_sources(root, errors)
    validate_claude_entrypoint(root, errors)

    for entrypoint in governed_entrypoints(root):
        validate_entrypoint_hygiene(root, entrypoint, max_bytes, warn_bytes, warnings)

    return {
        "root": str(root),
        "errors": deduplicate_issues(errors),
        "warnings": deduplicate_issues(warnings),
        "actions": [],
        "stats": {
            "specFiles": len(spec_files),
            "domainEntrypoints": sum((root / path).is_file() for path in DOMAIN_INDEXES.values()),
            "claudePresent": path_lexists(root / "CLAUDE.md"),
        },
    }


def validate_root_entrypoint(
    root: Path,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    root_agents = root / "AGENTS.md"
    if not root_agents.is_file():
        errors.append(issue("root.missing", "root AGENTS.md is required", "AGENTS.md"))
        return

    text = strip_fenced_code_blocks(read_text(root_agents)).replace("\\", "/")
    for domain, relative_path in DOMAIN_INDEXES.items():
        reference = relative_path.as_posix()
        if reference not in text:
            errors.append(
                issue(
                    "root.domain_index_missing",
                    f"root AGENTS.md must reference {reference}",
                    "AGENTS.md",
                )
            )
            continue
        if not has_actionable_navigation(text, reference, domain):
            warnings.append(
                issue(
                    "root.navigation_trigger_missing",
                    f"reference to {reference} may not explain when to read or search that domain; review manually",
                    "AGENTS.md",
                )
            )

    validate_local_links(root, root_agents, text, errors)


def validate_domain_entrypoints(
    root: Path,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    for domain, relative_path in DOMAIN_INDEXES.items():
        path = root / relative_path
        relative = relative_path.as_posix()
        if not path.is_file():
            errors.append(issue("domain.missing", f"documentation entrypoint is required: {relative}", relative))
            continue

        text = strip_fenced_code_blocks(read_text(path))
        if count_headings(text) == 0:
            errors.append(issue("domain.no_heading", "documentation entrypoint needs a Markdown heading", relative))
        if not SEARCH_ACTION_PATTERN.search(text) or not DOMAIN_PURPOSE_PATTERNS[domain].search(text):
            warnings.append(
                issue(
                    "domain.link_only_stub",
                    "entrypoint may not explain this domain's purpose and how to read or search it; review manually",
                    relative,
                )
            )
        validate_local_links(root, path, text, errors)


def validate_spec_index(
    root: Path,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> list[Path]:
    specs_root = root / "docs/specs"
    index_path = root / DOMAIN_INDEXES["specs"]
    if not specs_root.is_dir():
        return []

    spec_files = sorted(
        (
            path
            for path in specs_root.rglob("*.md")
            if path.name not in {"AGENTS.md", "AGENTS.override.md", "CLAUDE.md"}
            and not any(part in IGNORED_DIRS for part in path.relative_to(root).parts)
        ),
        key=lambda path: path.relative_to(root).as_posix().lower(),
    )
    if not index_path.is_file():
        return spec_files

    index_text = strip_fenced_code_blocks(read_text(index_path))
    linked_paths = extract_local_link_paths(root, index_path, index_text)
    link_counts: dict[str, int] = {}
    for linked_path in linked_paths:
        key = linked_path.as_posix()
        link_counts[key] = link_counts.get(key, 0) + 1

    for spec_file in spec_files:
        relative = spec_file.relative_to(root).as_posix()
        count = link_counts.get(relative, 0)
        if count == 0:
            errors.append(
                issue(
                    "spec.unindexed",
                    "every engineering Spec Markdown file must be linked at least once from docs/specs/AGENTS.md",
                    relative,
                )
            )

    validate_duplicate_spec_index_rows(root, index_path, index_text, warnings)
    validate_spec_duplicates(root, spec_files, errors, warnings)
    return spec_files


def validate_duplicate_spec_index_rows(
    root: Path,
    index_path: Path,
    index_text: str,
    warnings: list[dict[str, str]],
) -> None:
    seen_rows: dict[str, int] = {}
    relative_index = index_path.relative_to(root).as_posix()

    for line_number, line in enumerate(index_text.splitlines(), start=1):
        row = line.strip()
        if not row or not extract_link_targets(row):
            continue

        links_to_spec = False
        for raw_target in extract_link_targets(row):
            resolved, outside = resolve_local_link(root, index_path, raw_target)
            if outside or resolved is None:
                continue
            if len(resolved.parts) >= 3 and resolved.parts[:2] == ("docs", "specs"):
                if resolved.name not in {"AGENTS.md", "AGENTS.override.md", "CLAUDE.md"}:
                    links_to_spec = True
                    break
        if not links_to_spec:
            continue

        first_line = seen_rows.get(row)
        if first_line is None:
            seen_rows[row] = line_number
            continue
        warnings.append(
            issue(
                "spec.duplicate_index_row",
                f"line {line_number} duplicates the exact Spec index row on line {first_line}",
                relative_index,
            )
        )


def validate_spec_duplicates(
    root: Path,
    spec_files: list[Path],
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    digest_groups: dict[str, list[Path]] = {}
    digest_by_path: dict[Path, str] = {}
    normalized: dict[Path, str] = {}

    for path in spec_files:
        content = path.read_bytes()
        relative = path.relative_to(root).as_posix()
        if not content.strip():
            errors.append(issue("spec.empty", "Spec file must not be empty", relative))
            continue
        digest = hashlib.sha256(content).hexdigest()
        digest_groups.setdefault(digest, []).append(path)
        digest_by_path[path] = digest
        normalized[path] = normalize_similarity_text(content.decode("utf-8-sig", errors="replace"))

    for group in digest_groups.values():
        if len(group) < 2:
            continue
        paths = [path.relative_to(root).as_posix() for path in group]
        message = f"byte-identical Specs violate single-source governance: {', '.join(paths)}"
        for relative in paths:
            errors.append(issue("spec.exact_duplicate", message, relative))

    candidates = list(normalized)
    if len(candidates) > 200:
        warnings.append(
            issue(
                "spec.similarity_skipped",
                "near-duplicate heuristic skipped because more than 200 Specs were found",
                "docs/specs/AGENTS.md",
            )
        )
        return

    trigram_sets = {path: make_trigrams(text) for path, text in normalized.items()}
    for index, left in enumerate(candidates):
        for right in candidates[index + 1 :]:
            if digest_by_path[left] == digest_by_path[right]:
                continue
            score = trigram_similarity(trigram_sets[left], trigram_sets[right])
            if score < 0.90:
                continue
            left_relative = left.relative_to(root).as_posix()
            right_relative = right.relative_to(root).as_posix()
            warnings.append(
                issue(
                    "spec.possible_duplicate",
                    f"heuristic similarity {score:.0%} with {right_relative}; review manually",
                    left_relative,
                )
            )


def validate_legacy_sources(root: Path, errors: list[dict[str, str]]) -> None:
    for relative_dir in LEGACY_SPEC_DIRS:
        directory = root / relative_dir
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*.md")):
            relative = path.relative_to(root).as_posix()
            errors.append(
                issue(
                    "legacy.managed_markdown",
                    "classify and migrate this legacy managed document into docs/specs, docs/requirements, or docs/technical",
                    relative,
                )
            )


def validate_claude_entrypoint(root: Path, errors: list[dict[str, str]]) -> None:
    claude = root / "CLAUDE.md"
    if not path_lexists(claude):
        return

    root_agents = root / "AGENTS.md"
    if claude.is_symlink():
        try:
            raw_target = os.readlink(claude)
            if Path(raw_target).is_absolute():
                errors.append(
                    issue(
                        "claude.absolute_symlink",
                        "CLAUDE.md must use a relative symlink to root AGENTS.md",
                        "CLAUDE.md",
                    )
                )
                return
            resolved_target = (claude.parent / raw_target).resolve(strict=False)
            expected_target = root_agents.resolve(strict=False)
        except (OSError, RuntimeError) as exc:
            errors.append(issue("claude.broken_symlink", f"cannot resolve CLAUDE.md symlink: {exc}", "CLAUDE.md"))
            return
        if resolved_target != expected_target or not root_agents.is_file():
            errors.append(
                issue(
                    "claude.wrong_symlink",
                    "CLAUDE.md symlink must resolve to root AGENTS.md",
                    "CLAUDE.md",
                )
            )
        return

    if not claude.is_file():
        errors.append(issue("claude.invalid_type", "CLAUDE.md must be a file or symlink", "CLAUDE.md"))
        return

    text = read_text(claude)
    if not CLAUDE_IMPORT_PATTERN.search(text):
        errors.append(
            issue(
                "claude.missing_import",
                "existing regular CLAUDE.md must contain a standalone @AGENTS.md import",
                "CLAUDE.md",
            )
        )


def validate_entrypoint_hygiene(
    root: Path,
    path: Path,
    max_bytes: int,
    warn_bytes: int,
    warnings: list[dict[str, str]],
) -> None:
    relative = path.relative_to(root).as_posix()
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig", errors="replace")

    if len(raw) > max_bytes:
        warnings.append(issue("entrypoint.over_budget", f"entrypoint exceeds {max_bytes} bytes", relative))
    elif len(raw) > warn_bytes:
        warnings.append(issue("entrypoint.near_budget", f"entrypoint exceeds {warn_bytes} bytes", relative))

    for line_number, line in enumerate(text.splitlines(), start=1):
        if re.match(r"^\s+#{1,6}\s+", line):
            warnings.append(
                issue(
                    "markdown.indented_heading",
                    f"line {line_number}: Markdown headings should not be indented",
                    relative,
                )
            )

    warnings.extend(validate_inline_repository_references(root, relative, text))
    warnings.extend(validate_known_failure_guards(relative, text))


def validate_local_links(
    root: Path,
    source: Path,
    text: str,
    errors: list[dict[str, str]],
) -> None:
    source_relative = source.relative_to(root).as_posix()
    for raw_target in extract_link_targets(text):
        resolved, outside = resolve_local_link(root, source, raw_target)
        if outside:
            errors.append(
                issue(
                    "link.outside_repository",
                    f"local Markdown link escapes the repository: {raw_target}",
                    source_relative,
                )
            )
            continue
        if resolved is None:
            continue
        target = root / resolved
        if not target.exists():
            errors.append(
                issue(
                    "link.missing_target",
                    f"Markdown link target does not exist: {raw_target}",
                    source_relative,
                )
            )


def extract_local_link_paths(root: Path, source: Path, text: str) -> list[Path]:
    paths: list[Path] = []
    for raw_target in extract_link_targets(text):
        resolved, outside = resolve_local_link(root, source, raw_target)
        if resolved is not None and not outside:
            paths.append(resolved)
    return paths


def extract_link_targets(text: str) -> list[str]:
    targets: list[str] = []
    for match in MARKDOWN_LINK_PATTERN.finditer(text):
        target = match.group(1).strip()
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        targets.append(target)
    return targets


def resolve_local_link(root: Path, source: Path, raw_target: str) -> tuple[Path | None, bool]:
    target = unquote(raw_target.strip())
    if not target or target.startswith("#"):
        return None, False

    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None, False
    link_path = parsed.path
    if not link_path:
        return None, False

    candidate = root / link_path.lstrip("/") if link_path.startswith("/") else source.parent / link_path
    try:
        resolved = candidate.resolve(strict=False)
        relative = resolved.relative_to(root.resolve())
    except ValueError:
        return None, True
    return relative, False


def has_actionable_navigation(text: str, reference: str, domain: str) -> bool:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if reference not in line:
            continue
        start = max(0, index - 2)
        end = min(len(lines), index + 2)
        context = " ".join(lines[start:end])
        if SEARCH_ACTION_PATTERN.search(context) and DOMAIN_PURPOSE_PATTERNS[domain].search(context):
            return True
    return False


def governed_entrypoints(root: Path) -> list[Path]:
    paths = [root / "AGENTS.md", *(root / path for path in DOMAIN_INDEXES.values())]
    return [path for path in paths if path.is_file()]


def validate_inline_repository_references(root: Path, source: str, text: str) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    for match in INLINE_CODE_PATTERN.finditer(text):
        reference = match.group(1).strip().replace("\\", "/")
        normalized = normalize_repository_reference(reference)
        if normalized is None or repository_reference_exists(root, normalized):
            continue
        warnings.append(
            issue(
                "reference.possibly_stale",
                f"inline repository path may not exist: {reference}",
                source,
            )
        )
    return warnings


def normalize_repository_reference(reference: str) -> str | None:
    if (
        "://" in reference
        or "{" in reference
        or "$" in reference
        or "<" in reference
        or ">" in reference
        or reference.startswith("@")
        or reference.startswith("--")
        or " " in reference
    ):
        return None

    prefixes = (".agents/", ".github/", "docs/", "packages/", "scripts/", "test/", "tests/")
    files = {"AGENTS.md", "CLAUDE.md", "package.json", "pnpm-lock.yaml", "wrangler.toml"}
    if reference in files or reference.startswith(prefixes):
        return reference.lstrip("/").rstrip("/")
    return None


def repository_reference_exists(root: Path, reference: str) -> bool:
    glob_match = re.search(r"[*?[]", reference)
    path_to_check = reference[: glob_match.start()] if glob_match else reference
    trimmed = path_to_check.rstrip("/")
    return not trimmed or (root / trimmed).exists()


def validate_known_failure_guards(source: str, text: str) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not KNOWN_FAILURE_PATTERN.search(line):
            continue
        section = extract_containing_section(lines, index)
        if VALIDATION_PATTERN.search(section):
            continue
        warnings.append(
            issue(
                "failure.missing_validation",
                f"line {index + 1}: failure-mode rule lacks a validation command, test, evidence, or related document",
                source,
            )
        )
    return warnings


def extract_containing_section(lines: list[str], index: int) -> str:
    start = 0
    end = len(lines)
    for current in range(index, -1, -1):
        if re.match(r"^#{1,6}\s+", lines[current]):
            start = current
            break
    for current in range(index + 1, len(lines)):
        if re.match(r"^#{1,6}\s+", lines[current]):
            end = current
            break
    return "\n".join(lines[start:end])


def strip_fenced_code_blocks(text: str) -> str:
    visible_lines: list[str] = []
    fence_character: str | None = None
    fence_length = 0

    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            marker = match.group(1)
            if fence_character is None:
                fence_character = marker[0]
                fence_length = len(marker)
                visible_lines.append("")
                continue
            if marker[0] == fence_character and len(marker) >= fence_length:
                fence_character = None
                fence_length = 0
                visible_lines.append("")
                continue
        visible_lines.append(line if fence_character is None else "")

    return "\n".join(visible_lines)


def normalize_similarity_text(text: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", text.casefold())


def make_trigrams(text: str) -> set[str]:
    if len(text) < 120:
        return set()
    return {text[index : index + 3] for index in range(len(text) - 2)}


def trigram_similarity(left_grams: set[str], right_grams: set[str]) -> float:
    if not left_grams or not right_grams:
        return 0.0
    union = left_grams | right_grams
    return len(left_grams & right_grams) / len(union) if union else 0.0


def count_headings(text: str) -> int:
    return len(re.findall(r"(?m)^#{1,6}\s+", text))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def path_lexists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def issue(code: str, message: str, path: str | None = None) -> dict[str, str]:
    result = {"code": code, "message": message}
    if path is not None:
        result["path"] = path
    return result


def deduplicate_issues(issues: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    result: list[dict[str, str]] = []
    for item in issues:
        key = (item["code"], item.get("path", ""), item["message"])
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def print_text_report(report: dict[str, Any]) -> None:
    print(f"Agent documentation guard: {report['root']}")
    print(f"Mode: {report['mode']}")
    if report["actions"]:
        print("Actions:")
        for action in report["actions"]:
            print(f"- {action}")
    print_issue_section("Errors", report["errors"])
    print_issue_section("Warnings", report["warnings"])
    print(
        "Summary: "
        f"{len(report['errors'])} error(s), {len(report['warnings'])} warning(s), "
        f"{report['stats']['specFiles']} Spec file(s)"
    )


def print_issue_section(title: str, items: list[dict[str, str]]) -> None:
    print(f"{title}:")
    if not items:
        print("- none")
        return
    for item in items:
        location = f" {item['path']}:" if item.get("path") else ""
        print(f"- [{item['code']}]{location} {item['message']}")


if __name__ == "__main__":
    raise SystemExit(main())
