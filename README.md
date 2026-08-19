# agents-spec

[English](README.md) | [简体中文](README.zh-CN.md)

`agents-spec` is a portable [Agent Skill](https://agentskills.io/) for auditing and organizing shared agent instructions, engineering Specs, requirements, and technical decisions.

Source: [github.com/leftzzzz/agents-spec-skill](https://github.com/leftzzzz/agents-spec-skill)

The repository maintains one canonical Skill: `skills/agents-spec/SKILL.md`. Every compatible agent loads the same Skill. Platform manifests only provide discovery and installation; they do not duplicate the Skill body.

## Language support

The Skill works with Chinese prompts and Chinese-language repositories. Its internal instructions remain in English for consistent cross-agent behavior, but you can describe tasks in Chinese or English.

## Installing

The [`npx skills add`](https://github.com/vercel-labs/skills) CLI scans the `skills/` directory in this repository. Every agent supported by the CLI uses the same installation command, so this README does not maintain a platform-specific command list.

```bash
npx skills add https://github.com/leftzzzz/agents-spec-skill
```

This repository currently contains one Skill. You can also select it explicitly by its **install name** (the `name:` field in the `SKILL.md` frontmatter, not the directory name):

```bash
npx skills add https://github.com/leftzzzz/agents-spec-skill --skill "agents-spec"
```

The installer handles agent selection and installation scope, while its own supported-agent registry stays current as new agents are added.

To install from a local checkout instead:

```bash
npx skills add ./agents-spec-skill
```

For manual installation, copy the complete `skills/agents-spec/` directory to the Skill directory documented by your agent.

## Usage

After installation, describe the task in natural language:

```text
Use agents-spec to audit this repository's agent instructions and Spec indexes.
Report the audit results and migration plan before editing any files.
```

Explicit Skill invocation syntax varies by agent. Natural-language invocation works across compatible platforms. In Codex, you can also use `$agents-spec`.

The target repository model is:

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
- `docs/requirements/` contains product intent, acceptance criteria, and product decisions.
- `docs/technical/` contains architecture, implementation plans, and technical decisions.
- The root `AGENTS.md` tells every agent when to read or search each documentation domain.
- Platform-specific instruction files remain thin adapters to the shared root entrypoint.

## Guard script

The bundled guard has no third-party runtime dependencies. Run a read-only structural check:

```bash
python skills/agents-spec/scripts/audit_agents_md.py /path/to/repository --check
```

Emit JSON for CI:

```bash
python skills/agents-spec/scripts/audit_agents_md.py /path/to/repository --check --json
```

Only after a user explicitly asks to add a missing Claude compatibility entry:

```bash
python skills/agents-spec/scripts/audit_agents_md.py \
  /path/to/repository \
  --fix \
  --add-claude
```

Exit codes are `0` for compliance, `1` for structural violations, and `2` for invalid invocation or internal failure.

## Portable packaging

The repository uses the open Agent Skills layout:

```text
skills/agents-spec/
  SKILL.md
  LICENSE.txt
  agents/openai.yaml
  scripts/audit_agents_md.py
```

Optional native metadata lives at the repository root:

- `.codex-plugin/plugin.json`
- `.claude-plugin/plugin.json`
- `.cursor-plugin/plugin.json`

These files point to the same `skills/` directory. Contributions must not add platform-specific copies of `SKILL.md`.

## Development

```bash
python -m unittest discover -s tests -v
ruff check skills tests
ruff format --check skills tests
skills-ref validate skills/agents-spec
python /path/to/plugin-creator/scripts/validate_plugin.py .
npx --yes @anthropic-ai/claude-code@2.1.229 plugin validate .
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing the Skill contract or guard behavior.

## License

MIT
