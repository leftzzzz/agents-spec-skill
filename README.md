# agents-spec

[English](README.md) | [简体中文](README.zh-CN.md)

`agents-spec` is a portable [Agent Skill](https://agentskills.io/) for auditing and organizing shared agent instructions, engineering Specs, requirements, and technical decisions.

Source: [github.com/leftzzzz/agents-spec-skill](https://github.com/leftzzzz/agents-spec-skill)

The repository maintains one canonical Skill: `skills/agents-spec/SKILL.md`. Codex, Claude Code, Cursor, GitHub Copilot, OpenCode, and other compatible agents load the same Skill. Platform manifests only provide discovery and installation; they do not duplicate the Skill body.

## Language support

The Skill works with Chinese prompts and Chinese-language repositories. Its internal instructions remain in English for consistent cross-agent behavior, but you can describe tasks in Chinese or English.

## One-command installation

The commands below require Node.js 22.20 or newer, which is the runtime requirement of the current [`skills` CLI](https://github.com/vercel-labs/skills).

Each command installs the Skill globally so it is available in all projects for that agent. Choose your agent and run the corresponding command.

### Cursor

```bash
npx --yes skills add leftzzzz/agents-spec-skill --skill agents-spec --agent cursor --global --yes
```

### Claude Code

```bash
npx --yes skills add leftzzzz/agents-spec-skill --skill agents-spec --agent claude-code --global --yes
```

### Codex

```bash
npx --yes skills add leftzzzz/agents-spec-skill --skill agents-spec --agent codex --global --yes
```

### GitHub Copilot

```bash
npx --yes skills add leftzzzz/agents-spec-skill --skill agents-spec --agent github-copilot --global --yes
```

### OpenCode

```bash
npx --yes skills add leftzzzz/agents-spec-skill --skill agents-spec --agent opencode --global --yes
```

### Choose another agent interactively

If you omit `--agent`, the installer detects supported agents and prompts you to choose the target agent and installation scope:

```bash
npx --yes skills add leftzzzz/agents-spec-skill --skill agents-spec
```

In the commands above, `--global` means user-level installation and `--yes` skips confirmation prompts. For a project-only installation, enter the project root and remove `--global`.

You can also try a local checkout before the GitHub repository is published:

```bash
npx --yes skills add ./agents-spec-skill --skill agents-spec
```

For manual installation, copy the complete `skills/agents-spec/` directory to the corresponding location:

| Agent | Project directory | Global directory |
| --- | --- | --- |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex | `.agents/skills/` | `~/.codex/skills/` |
| Cursor | `.agents/skills/` | `~/.cursor/skills/` |
| GitHub Copilot | `.agents/skills/` | `~/.copilot/skills/` |
| OpenCode | `.agents/skills/` | `~/.config/opencode/skills/` |

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
