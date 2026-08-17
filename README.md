# organize-agents-spec

`organize-agents-spec` is a Codex Skill and standalone repository guard for organizing agent instructions around a single live Spec source.

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

- `docs/specs/` contains current enforceable behavior and constraints.
- `docs/requirements/` contains product intent, acceptance criteria, and product decisions.
- `docs/technical/` contains architecture, implementation plans, and technical decisions.
- Root `AGENTS.md` tells agents when to search each documentation domain.
- Optional `CLAUDE.md` compatibility is added only when explicitly requested.

The Skill does not pretend that a script can determine whether a business rule is semantically outdated. It enforces structural facts such as missing indexes, broken links, duplicate Spec sources, legacy rule locations, and invalid Claude compatibility entries.

## Install

Clone the repository into the Codex skills directory:

```bash
git clone https://github.com/leftzzzz/organize-agents-spec.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/organize-agents-spec"
```

Invoke it in Codex with:

```text
$organize-agents-spec
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
