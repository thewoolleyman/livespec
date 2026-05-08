---
topic: implementation-workflow-on-non-functional-requirements
author: claude-opus-4-7
created_at: 2026-05-08T03:44:52Z
---

## Proposal: Add repo-local implementation workflow under non-functional-requirements.md

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add a repo-local implementation workflow layer to the livespec repository: a project-local Claude Code plugin under `.claude/plugins/livespec-implementation/` with three skills (`refresh-gaps`, `plan`, `implement`), a beads-backed implementation-gap tracker, and an `implementation:*` justfile namespace. The layer MUST remain downstream of `/livespec:revise` and MUST NOT be shipped as part of the livespec plugin itself. All proposal content lands in `SPECIFICATION/non-functional-requirements.md` under the 5-section mirror structure: Spec sub-section codifies process intent; Contracts sub-sections codify the slash-command surface, justfile namespace, gap-report wire shape, and beads tooling pin; Constraints sub-sections codify plugin layout, beads invariants, gap-tied closure verification, and hook chaining; Scenarios sub-sections codify the 8 contributor-facing Gherkin scenarios. Refile of the rejected `livespec-implementation-workflow` proposal (predecessor moved to history paired with rejection-revision in v054).

### Motivation

The livespec repository currently lacks an explicit mechanism for tracking implementation gaps that arise after a SPECIFICATION revision lands. The shipped livespec plugin governs SPECIFICATION lifecycle only — it does NOT track which gaps need closing in this repository's own implementation. Open Brain demonstrates the desired pattern: a project-local plugin handles gap discovery (`refresh-gaps`), planning (`plan`), and execution (`implement`), backed by beads as a distributed task tracker. The boundary discipline is critical: implementation gap discovery is repository-specific work that requires intimate knowledge of THIS repo's code, tests, tooling, and workflow, and therefore MUST stay project-local rather than being shipped as a first-class livespec feature. Three concerns from the rejected predecessor are addressed in this refile: (1) mechanism-level setup-beads details (0700 permissions, refs/dolt/data preference, lock-file cleanup semantics, etc.) MUST move out of spec content and into the setup-beads.sh implementation; the spec defines architectural invariants only. (2) Open Brain inline commit-pinned URLs serve as evidence in the propose-change file's audit trail but MUST NOT bleed into final spec content; references to upstream patterns are sufficient. (3) Restatements of existing constraints (no force-push, no --no-verify, no bulk staging, atomic commits) MUST be omitted; those are already covered in `non-functional-requirements.md` Constraints/CLAUDE.md coverage and elsewhere.

### Proposed Changes

All changes target `SPECIFICATION/non-functional-requirements.md`. The proposal MUST add the following sub-sections under the existing 5-section mirror structure.

### Under `## Spec`

Add `### Repo-local implementation workflow` codifying the process intent:

- The livespec repository MAY maintain a project-local Claude Code plugin named `livespec-implementation` under `.claude/plugins/livespec-implementation/`. This plugin is part of this repository's contributor-facing development workflow only.
- The plugin MUST NOT ship under `.claude-plugin/`, MUST NOT expose `/livespec:*` commands, and MUST NOT be described as a first-class livespec product feature.
- The plugin owns three implementation workflow skills: `refresh-gaps` (compares the current SPECIFICATION against this repository's implementation, tests, tooling, and workflow state, then writes the current implementation-gap report); `plan` (manages beads issues for implementation work, including creating or updating issues for untracked implementation gaps); `implement` (drives issue-based implementation work, verifies completed gap-tied issues by rerunning `refresh-gaps`, and closes beads issues with audit notes).
- The implementation workflow MUST remain downstream from the livespec lifecycle. `/livespec:propose-change` and `/livespec:revise` remain the only path for changing SPECIFICATION; after a revision changes expected behavior, the repo-local implementation layer MAY discover implementation gaps and map them to beads issues.

### Under `## Contracts`

Add four sub-sections:

`### Project-local implementation plugin command surface` MUST enumerate the slash-command namespace: `/livespec-implementation:refresh-gaps`, `/livespec-implementation:plan`, `/livespec-implementation:implement`. The plugin manifest MUST live at `.claude/plugins/livespec-implementation/.claude-plugin/plugin.json` and MUST mirror the Open Brain project-local manifest shape adapted to the `livespec-implementation` name and purpose.

`### Implementation justfile namespace` MUST enumerate the initial required `implementation:*` justfile targets: `just implementation:setup-beads`, `just implementation:beads-doctor`, `just implementation:refresh-gaps`, `just implementation:check-gaps`, `just implementation:check-gap-tracking`. All user-facing helper and verification entry points for this layer MUST be exposed through the `implementation:*` namespace; the layer MUST NOT introduce a top-level `scripts/` directory or a parallel user-facing command surface.

`### Implementation-gap report shape` MUST codify the wire shape for `implementation-gaps/current.json`. The report MUST be machine-readable JSON validated against `implementation-gaps/current.schema.json` and MUST include at minimum: `schema_version`, `generated_at`, `spec_sources` fingerprints for the root SPECIFICATION files read, `inspection` metadata explaining what was and was not inspected, `gaps[]`, and `summary`. Each `gaps[]` entry MUST include: `id` matching `gap-[0-9]{4,}`, `area`, `severity`, optional operator-assigned `priority`, `title`, `spec_refs`, `expected`, `observed`, `evidence`, `evidence_kind`, `destructive_to_fix`, `destructive_reason`, `fix_hint`, `depends_on`. The schema MAY be modeled on Open Brain's drift schema, with names adapted from `PLAN/current-specification-drift.*` to `implementation-gaps/current.*` and with livespec-specific `area` values.

`### Toolchain pins addition for beads` MUST extend the existing Toolchain pins sub-section to add the `bd` (beads) CLI. `bd` and `lefthook` MUST be pinned through `.mise.toml`; `lefthook` MUST NOT be installed through npm or any node package because its postinstall behavior can overwrite `core.hooksPath` and bypass beads hook wrappers. The beads role: distributed graph issue tracker (Dolt-backed) for repo-local implementation work.

### Under `## Constraints`

Add four sub-sections:

`### Project-local plugin layout` MUST codify the plugin tree shape: `.claude/plugins/livespec-implementation/.claude-plugin/plugin.json` plus `.claude/plugins/livespec-implementation/skills/{refresh-gaps,plan,implement}/SKILL.md`, with optional `_shared/commit-discipline.md` for shared skill guidance. Gap artifacts live at `implementation-gaps/current.json` and `implementation-gaps/current.schema.json` at the repo root.

`### Beads invariants` MUST codify the architectural invariants on beads usage: (1) beads issue ids for this repository's implementation workflow use the prefix `li-`; (2) every current implementation gap id in `implementation-gaps/current.json` MUST appear exactly once as a label on one beads issue across all statuses (closed beads issues MAY retain labels for retired gaps; the invariant is one-way from current gaps to tracked issues); (3) the beads Dolt database is the source of truth — `.beads/issues.jsonl` is a git-tracked human-readable export view only and MUST NOT be hand-edited; (4) the implementation workflow MUST use noninteractive `bd` commands only — `bd edit` is forbidden because it opens `$EDITOR`; agents MUST use `bd create`, `bd update`, `bd close`, `bd dep`, `bd ready`, `bd show`, and other noninteractive forms with `--json` when command output informs a follow-up action. (5) Setup invariants: `just implementation:setup-beads` MUST detect and reversibly recover from corrupted or workspace-mismatched embedded state, MUST assert the `origin` Dolt remote, MUST chain lefthook + beads hooks so existing `just check` / pre-commit / pre-push gates continue to run, and MUST surface and fix hook failures rather than bypassing them. The exact recovery mechanics (permission modes, source preference for bootstrap, lock-file detection semantics, mismatch detection, backup-before-rebuild) live in the `setup-beads.sh` implementation, NOT in this spec — the spec defines architectural invariants only. Open Brain's `research/beads-problems.md` MAY be referenced as the upstream-issue tracking source for known beads workarounds.

`### Gap-tied issue closure verification` MUST codify: gap-tied issue closure with `resolution:fix` MUST rerun `livespec-implementation:refresh-gaps` (or `just implementation:refresh-gaps`) and confirm that the gap no longer appears in `implementation-gaps/current.json`. If the gap remains, the issue MUST NOT be closed as fixed. Closure notes for gap-tied fixes MUST record: resolution method, verification method, verification timestamp, commits, files changed, destructive actions taken, user approval reference for destructive actions when applicable, and migrations/deployments/secret-changes/external-changes when applicable. Non-fix gap closures use `resolution:wontfix`, `resolution:spec-revised`, `resolution:duplicate`, `resolution:no-longer-applicable`, or `resolution:resolved-out-of-band`. These are planning decisions and MUST NOT fabricate fix-verification metadata.

`### Hook chaining` MUST codify: beads hooks and lefthook MUST be chained so existing `just check` / pre-commit / pre-push gates continue to run. Hook templates managed by `just implementation:setup-beads` MUST run the existing lefthook-managed repository gates first, then beads hook behavior, while preserving and returning the lefthook exit status. The local Claude settings SHOULD wire `bd prime` on session start and pre-compaction so agents begin with recent beads context.

### Under `## Scenarios`

Add 8 sub-sections, each formatted as `### Scenario: <name>` with Given/When/Then steps using the gherkin-blank-line convention (one step per paragraph, no fenced code blocks). The scenarios:

1. `### Scenario: Refreshed implementation gaps after a SPECIFICATION revision` — verifies refresh-gaps regenerates `implementation-gaps/current.json` after a revision, identifies gaps using `gap-NNNN` ids, and does not edit SPECIFICATION or create/close beads issues.

2. `### Scenario: Planning creates beads issues for untracked current gaps` — verifies plan surfaces an untracked gap, creates one beads issue labeled with the gap id after user confirmation, and commits the beads export view as a reviewable planning commit.

3. `### Scenario: Implementation closes a verified gap-tied issue` — verifies implementation appends closure audit notes, applies `resolution:fix`, and closes the beads issue separately from the source edit, only after refresh-gaps confirms the gap no longer appears.

4. `### Scenario: Implementation refuses to close an unverified gap-tied issue` — verifies implementation refuses to close as fixed when refresh-gaps still shows the gap, surfaces the remaining observed gap, and asks whether to retry, split follow-up work, or hand off to planning for non-fix closure.

5. `### Scenario: Beads setup preserves existing repository gates` — verifies setup-beads resolves pinned `bd` and `lefthook` through mise, initializes or repairs embedded beads state without replacing existing enforcement, sets `core.hooksPath` to `.beads/hooks`, writes hook wrappers running existing lefthook behavior first then beads behavior, and ensures a failing lefthook gate still fails the overall hook.

6. `### Scenario: Beads doctor reports implementation-tracking drift` — verifies beads-doctor checks pinned `bd` path/version, embedded Dolt presence and status, Dolt remote wiring and pushed `refs/dolt/data`, `dolt.auto-commit`, `export.auto`, `core.hooksPath`, lefthook resolution, and reports actionable repair instructions for any failed check.

7. `### Scenario: Current gaps must map to exactly one beads issue` — verifies `just implementation:check-gap-tracking` enforces the gap-id→beads-label exactly-once invariant: zero matching issues fails, two-or-more matching issues fail, closed issues MAY retain labels for retired gap ids no longer in `implementation-gaps/current.json`.

8. `### Scenario: Implementation workflow remains outside livespec core` — verifies the project-local implementation plugin exists under `.claude/plugins/livespec-implementation/` AND when the shipped livespec plugin is packaged from `.claude-plugin/`, no `livespec-implementation` skill is included in the shipped plugin AND no `/livespec:*` command performs implementation gap discovery AND livespec core remains limited to SPECIFICATION lifecycle governance.

### Out of scope (post-revise follow-up implementation work)

This propose-change MUST add only the spec content above. Follow-up implementation work — actually creating `.claude/plugins/livespec-implementation/`, the three SKILL.md files, `implementation-gaps/current.schema.json`, the `setup-beads.sh` script, the per-clone `.beads/config.yaml`, the agent-facing AGENTS.md beads architecture documentation, the `.claude/settings.json` for `bd prime`, the `.mise.toml` `bd`/`lefthook` pins, and the `implementation:*` justfile targets — MUST land in subsequent commits/PRs after this propose-change is revised into the live SPECIFICATION. The Open Brain repository at `https://github.com/thewoolleyman/openbrain` SHOULD be referenced as the canonical pattern source for follow-up implementation; specific commit-pinned URLs from that repo serve as evidence in this propose-change file's audit trail and MUST NOT bleed into final spec content.
