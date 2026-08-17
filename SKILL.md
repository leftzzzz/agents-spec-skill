---
name: organize-agents-spec
description: Audit, reorganize, split, migrate, and maintain AGENTS.md and optional CLAUDE.md instructions with cross-agent document routing and SDD-aligned docs/specs, docs/requirements, and docs/technical directories. Use when cleaning up agent instructions, establishing a single live Spec source, migrating rules out of .agents, adding indexed documentation entrypoints, checking Codex and Claude Code compatibility, or installing deterministic structure guardrails.
---

# Organize Agent Specs

## Core Model

Use a cross-agent documentation model:

- Keep root `AGENTS.md` as the shared boot map and documentation router.
- Keep current enforceable rules in `docs/specs/` as the single live Spec source.
- Keep product intent, acceptance criteria, and product decisions in `docs/requirements/`.
- Keep architecture, implementation plans, and technical decisions in `docs/technical/`.
- Keep real `AGENTS.md` navigation entrypoints in all three documentation directories.
- Do not depend on nested `AGENTS.md` auto-discovery. Make root explicitly tell every agent when to read or search each directory.
- Do not use `.agents/projects/` or `.agents/references/` as the canonical Spec store.

Use this default layout:

```text
AGENTS.md
CLAUDE.md -> AGENTS.md       # Optional; create only on explicit user request
docs/
  specs/
    AGENTS.md
    projects/
    references/
  requirements/
    AGENTS.md
  technical/
    AGENTS.md
```

Preserve an existing useful subdivision under `docs/specs/`; `projects/` and `references/` are defaults, not mandatory empty directories.

## Document Responsibilities

Treat each document class as a separate authority:

- Spec: state only what must be true now. Keep one live version and use Git for history.
- Requirement document: record what to build, why it matters, acceptance criteria, and product decisions.
- Technical document: record architecture, implementation approach, tradeoffs, and technical decisions.

Never store decision history or rationale in a Spec. When an accepted requirement or technical decision changes current behavior, update the affected Spec in the same change. Do not copy a rule into root or an index; link to its single Spec source.

Do not require lifecycle metadata such as version, status, supersedes, stable ID, or owner solely for this model. Do not require `description`, `appliesTo`, or `alwaysApply` frontmatter. If another documentation tool needs frontmatter, allow it but do not treat it as the routing authority.

## Entrypoints And Routing

Keep root `AGENTS.md` compact but substantive. Include a documentation navigation table that links all three entrypoints and explains when to use them:

| Need | Read or search first |
| --- | --- |
| Current behavior, constraints, rules, or boundaries | `docs/specs/AGENTS.md` |
| Product intent, user needs, or acceptance criteria | `docs/requirements/AGENTS.md` |
| Architecture, implementation approach, or technical rationale | `docs/technical/AGENTS.md` |

Also state this workflow in root:

- For existing behavior, inspect applicable Specs before changing code.
- For a new feature, inspect relevant requirement and technical documents, then reconcile applicable Specs before implementation.
- After accepting a requirement or technical decision, update affected Specs in the same change.
- Search requirement or technical documents for rationale; do not infer rationale from Specs.

Make each documentation entrypoint a real navigator, not a link-only stub:

- `docs/specs/AGENTS.md`: explain the Spec authority and search workflow; link every Spec Markdown file exactly once.
- `docs/requirements/AGENTS.md`: explain what belongs here and how to search it. Do not semantically audit requirement decisions.
- `docs/technical/AGENTS.md`: explain what belongs here and how to search it. Do not semantically audit technical decisions.

Use Markdown links in the Spec index so the guard script can validate paths deterministically.

## Claude Code Compatibility

Treat root `CLAUDE.md` as optional:

- Never create `CLAUDE.md` unless it is missing and the user explicitly asks to add it.
- When both conditions are true, run the guard with `--fix --add-claude` to create the relative symlink `CLAUDE.md -> AGENTS.md`.
- If the platform cannot create symlinks, allow the script to fall back to a regular `CLAUDE.md` containing `@AGENTS.md`.
- Never overwrite an existing file or symlink.
- If `CLAUDE.md` exists, require it to resolve to root `AGENTS.md` or import `@AGENTS.md`; report an invalid existing entry as an error.
- Keep all shared rules in root `AGENTS.md`. Use `.claude/CLAUDE.md` only for genuinely Claude-specific additions.

A missing `CLAUDE.md` is compliant unless the user explicitly requested one.

## Workflow

1. Audit before proposing edits:
   - Locate root and nested `AGENTS.md`, optional `CLAUDE.md`, `.agents/**/*.md`, and all three documentation directories.
   - Run the bundled guard with `--check --json` when a filesystem is available.
   - Read root and only the relevant indexed documents.

2. Report the discovered authorities:
   - Identify current Spec sources and legacy `.agents/` candidates.
   - Identify missing or broken entrypoints and unindexed Specs.
   - Report exact duplicates separately from heuristic near-duplicate candidates.
   - Do not claim that a script can determine whether a business rule is semantically outdated.

3. Propose the exact migration and wait for confirmation unless the user asked for immediate execution:
   - Map current enforceable rules to `docs/specs/`.
   - Map product decisions to `docs/requirements/`.
   - Map technical decisions to `docs/technical/`.
   - Name every entrypoint and index row to create or update.
   - Preserve useful rules before removing a legacy source.

4. Apply the confirmed migration:
   - Resolve conflicting sources before selecting the live Spec.
   - Keep indexes descriptive and free of copied rules.
   - Preserve unrelated user changes.
   - Add `CLAUDE.md` only under the explicit-request rule above.

5. Validate:
   - Run the guard with `--check` and require exit code `0`.
   - Run relevant repository tests or documentation checks.
   - Summarize structural errors, semantic review candidates, and any CI gap.

## Deterministic Guard

Run the bundled script relative to this Skill directory:

```text
python <skill-dir>/scripts/audit_agents_md.py <repo-root> --check
python <skill-dir>/scripts/audit_agents_md.py <repo-root> --check --json
python <skill-dir>/scripts/audit_agents_md.py <repo-root> --fix --add-claude
```

Modes and exit codes:

- `--check`: read-only validation; this is the default mode.
- `--fix`: apply only explicitly selected deterministic repairs, then validate.
- `--add-claude`: valid only with `--fix`; records the user's explicit request to add the missing compatibility entry.
- Exit `0`: structurally compliant.
- Exit `1`: structural violations found.
- Exit `2`: invalid invocation or internal failure.

Treat these as hard errors:

- Missing root or documentation-domain `AGENTS.md` entrypoints.
- Missing root links or actionable search guidance for a documentation domain.
- Empty or link-only documentation entrypoints.
- Missing, duplicate, or broken Spec index links.
- Byte-identical duplicate Specs.
- Markdown remaining under legacy `.agents/projects/` or `.agents/references/`.
- Broken local links in governed entrypoints.
- An existing invalid `CLAUDE.md`.

Treat heuristic near-duplicate Specs, oversized entrypoints, indented headings, stale inline path candidates, and failure-mode prose without a validation reference as warnings. Warnings must not pretend to prove semantic duplication, conflict, or staleness.

The script is a hard checker only when it returns a nonzero status. It becomes a persistent repository gate only after the repository invokes `--check` from CI or another enforced validation entrypoint. Propose that integration explicitly; do not silently rewrite unrelated CI.

## Editing Guardrails

- Never discard current business constraints merely to shorten files.
- Never retain multiple live versions of one Spec; keep history in Git.
- Never move decision rationale into a Spec.
- Never duplicate detailed rules in root or directory indexes.
- Never infer that nested `AGENTS.md` files load identically across agent products.
- Never create or replace `CLAUDE.md` without the explicit-request condition.
- Never treat a heuristic warning as proof of a semantic conflict.
- Prefer structured Markdown link parsing and filesystem checks over ad hoc text replacement.
