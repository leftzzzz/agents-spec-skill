---
name: agents-spec
description: Audit, reorganize, split, migrate, and maintain AGENTS.md, optional platform instruction files, and current-only engineering Specs with cross-agent routing and SDD-aligned docs/specs, docs/requirements, and docs/technical directories. Use when cleaning up agent instructions, organizing engineering standards, contracts, policies, or invariants, removing history or summaries from Specs, separating business requirements and technical decisions from Specs, migrating rules out of .agents, checking multi-agent compatibility, or installing deterministic structure guardrails.
---

# AGENTS Spec

## Core Model

Use a cross-agent documentation model:

- Keep root `AGENTS.md` as the shared boot map and documentation router.
- Keep only current, implementation-facing engineering facts and rules in `docs/specs/` as the single live Spec source.
- Keep each fact or rule in one authoritative body. A Spec must not contain history, change summaries, progress snapshots, release records, background narrative, or unrelated description.
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

Classify a statement by what it governs:

- Agent instruction: state how an agent must act or where it must look.
- Engineering Spec: state what the code or system must satisfy now, such as a standard, contract, protocol, security policy, compatibility boundary, or operational invariant.
- Requirement document: record the product or business outcome, why it matters, acceptance criteria, and product decisions.
- Technical document: record architecture, implementation approach, tradeoffs, and technical decisions.

Do not use `docs/specs/` as a generic home for every document called a "spec." Split a mixed document by responsibility: move business intent and acceptance criteria to `docs/requirements/`, current verifiable engineering facts and rules to `docs/specs/`, and design rationale, migration plans, audits, postmortems, status reports, and historical records to `docs/technical/`.

Every Spec paragraph must directly define or locate a current, uniquely authoritative, implementation-relevant, and verifiable fact or rule. Remove narrative introductions, executive summaries, duplicated conclusions, prior-state descriptions, completed-work reports, dated observations, and future work unless they themselves define a current constraint. A Spec is not a summary of requirement documents, technical documents, code, registries, manifests, or run output.

Never store decision history or rationale in an engineering Spec. When an accepted requirement or technical decision changes current behavior, replace the affected Spec statement in the same change; keep the old state in Git or a technical record, not beside the new rule. Do not copy a rule into root or an index; link to its single authoritative source.

Do not require lifecycle metadata such as version, status, supersedes, stable ID, or owner solely for this model. Do not require `description`, `appliesTo`, or `alwaysApply` frontmatter. Remove unused frontmatter during migration; if a real tool consumes metadata, keep only the fields that tool requires and do not treat them as the routing authority.

## Persistent Rule Governance

Apply these checks to Agent instructions and to normative statements inside engineering Specs. Do not apply them to the content of business requirements or technical decision documents.

- Admit a persistent Agent instruction only when a non-obvious problem recurs or one occurrence would cause material harm.
- Admit an engineering Spec statement when it defines a current, stable, implementation-facing, and verifiable standard, contract, policy, or invariant. It does not need a history of failure.
- Retain a factual statement only when it is the current authority or tells the reader how to query the current machine authority. Delete or relocate facts that merely describe a past run, migration, release, incident, audit, or completed task.
- Keep each normative statement focused on one behavior. Review its trigger or scope, invariant, preferred path, and any necessary exception, but do not force a four-field template or invent an exception.
- Put personal cross-repository preferences in the user's global layer, shared repository behavior and routing in root `AGENTS.md`, engineering constraints in `docs/specs/`, business intent in `docs/requirements/`, technical rationale in `docs/technical/`, and transient context only in the current task.
- Keep one authoritative body for a principle. Other locations may contain trigger indexes that link to it, and multiple distinct indexes may point to the same source.
- Automate a requirement only when the judgment is deterministic, stable, sufficiently important or frequent, low in false positives, and invoked from a real enforcement point. Keep contextual or semantic judgment in prose and review.
- Validate a new enforced rule with a violating case, an intended safe exception or an explicit no-exception case, and an adjacent irrelevant case. Narrow or remove a rule that repeatedly produces false positives.

## Entrypoints And Routing

Keep root `AGENTS.md` compact but substantive. Include a documentation navigation table that links all three entrypoints and explains when to use them:

| Need | Read or search first |
| --- | --- |
| Current engineering behavior, standards, contracts, constraints, or boundaries | `docs/specs/AGENTS.md` |
| Product intent, user needs, or acceptance criteria | `docs/requirements/AGENTS.md` |
| Architecture, implementation approach, or technical rationale | `docs/technical/AGENTS.md` |

At the beginning of a task, read the root `AGENTS.md` as the only guaranteed cross-agent boot entrypoint. Then read the relevant documentation entrypoint and linked documents on demand. Do not preload every Spec or assume that nested `AGENTS.md` files are auto-discovered by every agent product.

Also state this workflow in root:

- For existing engineering behavior, inspect applicable Specs before changing code.
- For a new feature, inspect relevant requirement and technical documents, then reconcile applicable Specs before implementation.
- After accepting a requirement or technical decision, update affected Specs in the same change.
- Search requirement or technical documents for rationale; do not infer rationale from Specs.

Make each documentation entrypoint a real navigator, not a link-only stub:

- `docs/specs/AGENTS.md`: explain the engineering Spec authority and search workflow; link every Spec Markdown file at least once. Allow multiple distinct trigger entries to point to the same authoritative Spec.
- `docs/requirements/AGENTS.md`: explain what belongs here and how to search it. Do not semantically audit requirement decisions.
- `docs/technical/AGENTS.md`: explain what belongs here and how to search it. Do not semantically audit technical decisions.

Use Markdown links in the Spec index so the guard script can validate paths deterministically.

## Agent Compatibility

Treat platform-specific instruction files as optional adapters around the shared root `AGENTS.md`:

- Keep shared rules and routing in root `AGENTS.md`, which is the only guaranteed boot entrypoint across agents.
- Add a platform file only when the target agent requires or the user explicitly requests it.
- When a platform supports imports or symlinks, make the adapter resolve to `AGENTS.md`; otherwise keep it short and link to the canonical file.
- Never copy shared rules into multiple platform files. Put genuinely platform-specific additions in the adapter only.
- For Claude Code, `CLAUDE.md` may be a relative symlink to `AGENTS.md` or a regular file containing a standalone `@AGENTS.md` import. Use the guard's `--fix --add-claude` only after an explicit request.
- Do not add platform manifests or marketplace metadata unless the target platform requires them or the user explicitly requests native plugin distribution.

A missing platform file is compliant unless the target agent explicitly requires one.

## Workflow

1. Audit before proposing edits:
   - Locate root and nested `AGENTS.md`, optional platform instruction files, `.agents/**/*.md`, and all three documentation directories.
   - Run the bundled guard with `--check --json` when a filesystem is available.
   - Read root and only the relevant indexed documents.
   - Review existing Spec sections and metadata for history, summaries, duplicated machine values, task status, and material unrelated to a current fact or rule.

2. Report the discovered authorities:
   - Identify current engineering Spec sources and legacy `.agents/` candidates.
   - Identify missing or broken entrypoints and unindexed Specs.
   - Report exact duplicates separately from heuristic near-duplicate candidates.
   - Flag mixed business intent, engineering constraints, and decision rationale for manual classification. Do not claim that a script can classify them reliably or determine whether a business rule is semantically outdated.
   - Identify Spec content that must be deleted or moved because it reports a prior state, completed work, a dated result, or a future plan instead of governing current behavior.

3. Propose the exact migration and wait for confirmation unless the user asked for immediate execution:
   - Map current verifiable engineering standards, contracts, policies, and invariants to `docs/specs/`.
   - Map product or business outcomes, acceptance criteria, and decisions to `docs/requirements/`.
   - Map technical decisions, implementation plans, migrations, audits, postmortems, progress reports, and historical records to `docs/technical/`.
   - Name every entrypoint and index row to create or update.
   - Preserve useful rules before removing a legacy source.

4. Apply the confirmed migration:
   - Resolve conflicting sources before selecting the live engineering Spec.
   - Extract only current facts and rules from legacy documents; do not move a mixed document into `docs/specs/` unchanged.
   - Remove duplicated summaries, background, status, history, and unused metadata from the resulting Spec.
   - Keep indexes descriptive and free of copied rules.
   - Apply the persistent-rule admission and placement checks before adding new Agent instructions or engineering Spec statements.
   - Preserve unrelated user changes.
   - Add `CLAUDE.md` only under the explicit-request rule above.

5. Validate:
   - Run the guard with `--check` and require exit code `0`.
   - Run relevant repository tests or documentation checks, including violation, intended-exception or no-exception, and adjacent irrelevant cases for newly enforced rules.
   - Manually confirm that each changed Spec contains only current authoritative facts and rules; the deterministic guard cannot prove semantic currentness or relevance.
   - Report structural errors, semantic review candidates, and any CI gap outside the Specs rather than adding an audit summary to a Spec.

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
- Missing root links for a documentation domain.
- Missing documentation entrypoints or required Markdown headings.
- Missing or broken Spec index links.
- Byte-identical duplicate Specs.
- Markdown remaining under legacy `.agents/projects/` or `.agents/references/`.
- Broken local links in governed entrypoints.
- An existing invalid `CLAUDE.md`.

Treat possibly incomplete natural-language routing guidance, exact duplicate Spec index rows, heuristic near-duplicate Specs, oversized entrypoints, indented headings, stale inline path candidates, and failure-mode prose without a validation reference as warnings. Warnings must not pretend to prove semantic duplication, conflict, classification, or staleness.

The script is a hard checker only when it returns a nonzero status. It becomes a persistent repository gate only after the repository invokes `--check` from CI or another enforced validation entrypoint. Propose that integration explicitly; do not silently rewrite unrelated CI.

The guard validates routing and document structure; it is not a context loader or a formatter. Context loading comes from the root `AGENTS.md` routing workflow, and enforcement comes from an explicit CI or hook invocation.

## Editing Guardrails

- Never discard current business constraints merely to shorten files.
- Never use failure history as an admission requirement for an engineering Spec.
- Never retain multiple live versions of one Spec; keep history in Git.
- Never keep a historical section, migration log, release record, audit summary, current-task status, or future-work list inside a Spec.
- Never keep introductory or concluding prose that only restates rules defined elsewhere in the same Spec.
- Never preserve unused legacy frontmatter merely because the source document had it.
- Never move decision rationale into a Spec.
- Never duplicate detailed rules in root or directory indexes.
- Never confuse multiple trigger indexes with multiple authoritative sources.
- Never use keyword heuristics to auto-classify a document as a business requirement, engineering Spec, or technical decision.
- Never infer that nested `AGENTS.md` files load identically across agent products.
- Never create or replace a platform instruction file without the explicit-request condition.
- Never treat a heuristic warning as proof of a semantic conflict.
- Prefer a parser that respects Markdown link structure and filesystem checks over ad hoc text replacement.
