# agents-spec

`agents-spec` is a Codex Skill and standalone repository guard for organizing agent instructions and non-business engineering Specs around explicit, cross-agent documentation routes.

It replaces tool-specific rule stores with an explicit, cross-agent documentation model:

```text
AGENTS.md
docs/
  specs/
    AGENTS.md
  requirements/
    AGENTS.md
  technical/
    AGENTS.md
```

- `docs/specs/` contains current engineering standards, contracts, policies, and invariants.
- `docs/requirements/` contains product or business intent, acceptance criteria, and product decisions.
- `docs/technical/` contains architecture, implementation plans, and technical decisions.
- Root `AGENTS.md` tells agents when to search each documentation domain.
- Optional `CLAUDE.md` compatibility is added only when explicitly requested.

The Skill routes business requirements and technical rationale without semantically policing their content. Its guard enforces structural facts such as missing indexes, broken links, duplicate engineering Spec sources, legacy rule locations, and invalid Claude compatibility entries; natural-language routing quality remains a review warning.

## Install

Clone the repository into the Codex skills directory:

```bash
git clone https://github.com/leftzzzz/agents-spec-skill.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/agents-spec"
```

Invoke it in Codex with:

```text
$agents-spec
```

The Skill produces shared `AGENTS.md` navigation that both Codex and Claude Code can follow. It does not assume that Claude Code directly loads Codex Skill packages.

## Guard Script

Run a read-only structural check:

```bash
python scripts/audit_agents_md.py /path/to/repository --check
```

Emit JSON for CI or other tooling:

```bash
python scripts/audit_agents_md.py /path/to/repository --check --json
```

Only after a user explicitly asks to add a missing `CLAUDE.md`, run:

```bash
python scripts/audit_agents_md.py /path/to/repository --fix --add-claude
```

Exit codes are `0` for compliance, `1` for structural violations, and `2` for invalid invocation or internal failure.

## Development

The guard has no third-party runtime dependencies. Run the test suite with:

```bash
python -m unittest discover -s tests -v
```

## License

MIT
