# Contributing

Thanks for improving `agents-spec`.

## Principles

- Keep `skills/agents-spec/SKILL.md` as the single canonical Skill body.
- Keep platform manifests thin; do not duplicate instructions for individual agents.
- Preserve the guard's zero-dependency Python runtime.
- Treat heuristic findings as warnings, never as proof of semantic intent.
- Add a regression test for every deterministic guard behavior change.

## Local checks

Use Python 3.10 or newer:

```bash
python -m unittest discover -s tests -v
ruff check skills tests
ruff format --check skills tests
skills-ref validate skills/agents-spec
```

Run the Codex plugin validator as an additional adapter check when it is available:

```bash
python /path/to/plugin-creator/scripts/validate_plugin.py .
npx --yes @anthropic-ai/claude-code@2.1.229 plugin validate .
```

## Pull requests

Keep each pull request focused. Describe the behavior or packaging contract that changes, include the validation you ran, and call out any platform-specific assumptions.
