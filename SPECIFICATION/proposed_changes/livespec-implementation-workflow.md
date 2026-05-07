---
topic: livespec-implementation-workflow
author: Codex GPT-5
created_at: 2026-05-07T08:49:51Z
---

## Proposal: Add repo-local implementation workflow layer

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md
- SPECIFICATION/scenarios.md

### Summary

Add a repo-local `livespec-implementation` Claude Code plugin, beads-backed
implementation gap tracking, and `implementation:*` justfile namespace for
the `livespec` repository's own development workflow.

This proposal does NOT make implementation gap discovery a first-class
LiveSpec product feature. The shipped `.claude-plugin/` continues to govern
the `SPECIFICATION` lifecycle only. The new layer is project-local tooling
for this repository, kept under `.claude/plugins/livespec-implementation/`
and invoked as `/livespec-implementation:*`.

### Motivation

The current `SPECIFICATION` already defines strong repository discipline:
Red/Green TDD, `just check`, lefthook, CI, coverage, branch protection, and
the protected-branch PR workflow. What is missing is an explicit
implementation workflow for turning revised `SPECIFICATION` content into
tracked implementation work without moving that responsibility into the
LiveSpec product itself.

Prior research supports the boundary:

- OpenSpec exposes specification artifacts together with implementation
  tasks and apply/archive workflows; its public overview describes generated
  proposals, implementation tasks, design decisions, and spec deltas:
  https://openspec.dev/
- GitHub Spec Kit explicitly includes `/speckit.plan`, `/speckit.tasks`,
  `/speckit.taskstoissues`, and `/speckit.implement`, showing a combined
  specification-to-implementation workflow:
  https://github.com/github/spec-kit/blob/main/README.md
- BMAD treats implementation as story execution plus code review after
  planning/story creation:
  https://docs.bmad-method.org/explanation/faq/implementation-faq/
- GitHub documents the branch/PR model separately from spec tooling through
  GitHub Flow, pull-request merging, and protected branches:
  https://docs.github.com/en/get-started/using-github/github-flow and
  https://docs.github.com/articles/merging-a-pull-request and
  https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- Beads is a distributed graph issue tracker for AI agents, powered by
  Dolt, and is appropriate as the repo-local task tracking substrate:
  https://github.com/gastownhall/beads
- The peer Open Brain repo demonstrates the desired local pattern in
  concrete, reusable form. The `openbrain` project-local plugin describes
  itself as skills for keeping its `SPECIFICATION` and implementation
  converged:
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/.claude-plugin/plugin.json#L1-L8
  Its `update-specification-drift`, `plan`, and `implement` skills provide
  the nearest examples for `refresh-gaps`, `plan`, and `implement` here:
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/skills/update-specification-drift/SKILL.md#L1-L35
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/skills/plan/SKILL.md#L1-L20
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/skills/implement/SKILL.md#L1-L19

The Open Brain beads migration and problem-history documents are especially
important because they record decisions and upstream Beads workarounds that
should be copied or consciously adapted:

- Migration plan and original adoption rationale:
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/research/migrate-to-beads.md#L1-L27
- Migration constraints around JSONL as derived view, hooks, and agent
  commands:
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/research/migrate-to-beads.md#L45-L54
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/research/migrate-to-beads.md#L79-L90
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/research/migrate-to-beads.md#L123-L154
- Living index of Beads upstream problems and local workarounds:
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/research/beads-problems.md#L1-L20
- Upstream Beads bugs and workaround requirements already encountered:
  `bd init` does not synthesize the Dolt remote
  (https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/research/beads-problems.md#L24-L56);
  `bd doctor` is unavailable in embedded mode
  (https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/research/beads-problems.md#L60-L87);
  JSONL-vs-Dolt source-of-truth confusion caused real failure modes
  (https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/research/beads-problems.md#L91-L125);
  `bd bootstrap` does not reliably wire the remote on fresh embedded init
  (https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/research/beads-problems.md#L129-L157);
  Beads-generated docs omit key command explanations
  (https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/research/beads-problems.md#L161-L188);
  `.beads/` permissions warnings require a temporary self-heal until a
  post-v1.0.3 Beads release includes upstream PR #3483
  (https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/research/beads-problems.md#L192-L229);
  workspace identity mismatch requires explicit detection and reversible
  local-Dolt rebuild
  (https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/research/beads-problems.md#L233-L321);
  and lefthook's npm postinstall can race Beads hook ownership, requiring
  a mise-pinned lefthook binary plus explicit hook-path checks
  (https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/research/beads-problems.md#L325-L363).

The synthesis is that LiveSpec-the-product should remain a SPECIFICATION
governance tool, while LiveSpec-the-repository should have a local
implementation layer that is allowed to know this repository's code,
tests, justfile, branch protection, and release discipline.

### Open Brain Reference Map for `revise`

When revising this proposal, use the following Open Brain permalinks as
implementation examples. They are commit-pinned to
`b3dc01b961e064db1ad02d1e61c32d52364075aa` so the referenced line numbers
remain stable.

- Project-local plugin manifest:
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/.claude-plugin/plugin.json#L1-L8
- `update-specification-drift` skill: source-of-truth framing,
  read-only gap refresh, schema, commit discipline, and inspection procedure:
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/skills/update-specification-drift/SKILL.md#L13-L35
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/skills/update-specification-drift/SKILL.md#L37-L94
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/skills/update-specification-drift/SKILL.md#L96-L178
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/skills/update-specification-drift/SKILL.md#L180-L215
- Gap schema example:
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/PLAN/current-specification-drift.schema.json#L1-L225
- `plan` skill: beads operations, clean-tree discipline, gap coverage
  triage, non-fix closures, and explicit non-goals:
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/skills/plan/SKILL.md#L22-L46
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/skills/plan/SKILL.md#L54-L83
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/skills/plan/SKILL.md#L105-L157
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/skills/plan/SKILL.md#L179-L246
- `implement` skill: beads issue execution, ranking, destructive-action
  gates, checkpoint commits, verified gap closure, and refusal to close
  unverified fixes:
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/skills/implement/SKILL.md#L21-L70
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/skills/implement/SKILL.md#L72-L154
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/skills/implement/SKILL.md#L179-L235
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/skills/implement/SKILL.md#L264-L376
- Shared commit discipline for clean-tree entry, atomic commits, explicit
  staging, message shapes, push behavior, destructive-action two-commit
  pattern, and audit trail:
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/skills/_shared/commit-discipline.md#L13-L80
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/skills/_shared/commit-discipline.md#L82-L128
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/skills/_shared/commit-discipline.md#L130-L187
- Beads architecture docs in agent instructions:
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/AGENTS.md#L284-L414
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/AGENTS.md#L416-L461
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/AGENTS.md#L463-L518
- Beads setup and hook rewrite example:
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/setup-beads.sh#L1-L30
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/setup-beads.sh#L37-L48
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/setup-beads.sh#L56-L86
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/setup-beads.sh#L94-L123
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/setup-beads.sh#L125-L192
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/setup-beads.sh#L194-L209
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/setup-beads.sh#L211-L334
- Embedded-mode beads doctor replacement:
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/bd-doctor.sh#L1-L49
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/bd-doctor.sh#L102-L136
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/bd-doctor.sh#L142-L199
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/bd-doctor.sh#L205-L289
- Package/setup examples for `setup:beads`, `bd:doctor`, `prepare`,
  `bd prime`, and pinned `bd` / `lefthook`:
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/package.json#L39-L41
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/settings.json#L1-L25
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.mise.toml#L1-L7
- Beads per-clone config and gitignore shape:
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/setup-beads.sh#L118-L123
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/setup-beads.sh#L158-L192
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.beads/.gitignore#L1-L73
- Current-gap to beads-label invariant:
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/smoke.ts#L402-L449
- Beads adoption and upstream-problem research files that `revise` should
  treat as required implementation context:
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/research/migrate-to-beads.md#L1-L154
  https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/research/beads-problems.md#L1-L387
- LiveSpec lifecycle archive context for keeping implementation downstream
  from `SPECIFICATION` revision:
  https://github.com/thewoolleyman/livespec/blob/3cae7764a2aac70e07a5458f876e115f23441a50/archive/brainstorming/approach-2-nlspec-based/2026-04-19-nlspec-lifecycle-diagram.md#L1-L41
  https://github.com/thewoolleyman/livespec/blob/3cae7764a2aac70e07a5458f876e115f23441a50/archive/brainstorming/approach-2-nlspec-based/2026-04-19-nlspec-lifecycle-diagram-detailed.md#L1-L79
- LiveSpec's current repo-layout and justfile conventions that follow-up
  implementation MUST preserve:
  https://github.com/thewoolleyman/livespec/blob/3cae7764a2aac70e07a5458f876e115f23441a50/AGENTS.md#L1-L113
  https://github.com/thewoolleyman/livespec/blob/3cae7764a2aac70e07a5458f876e115f23441a50/justfile#L1-L22

### Implementation Landing Map for `revise`

This proposed change should revise only the live `SPECIFICATION` root
documents listed above. Follow-up implementation work should land in these
repository locations:

- Project-local plugin:
  `.claude/plugins/livespec-implementation/.claude-plugin/plugin.json` and
  `.claude/plugins/livespec-implementation/skills/{refresh-gaps,plan,implement}/SKILL.md`
- Shared skill guidance:
  `.claude/plugins/livespec-implementation/skills/_shared/commit-discipline.md`
- Gap artifacts:
  `implementation-gaps/current.schema.json` and
  `implementation-gaps/current.json`
- Beads state/config:
  `.beads/.gitignore`, per-clone `.beads/config.yaml`, and the embedded
  Dolt state managed by `just implementation:setup-beads`
- Agent docs:
  `AGENTS.md` Beads architecture, command, anti-pattern, and session
  completion guidance
- Claude local hooks:
  `.claude/settings.json` for `bd prime` session-start and pre-compact
  context priming
- Tool pin:
  `.mise.toml` for the pinned `bd` and `lefthook` versions
- Just interface:
  `justfile` targets under the `implementation:*` namespace only
- Helper code:
  existing repo conventions only, such as `dev-tooling/` and mirrored
  `tests/`; do not add a top-level `scripts/` directory or parallel
  user-facing command surface

### Proposed Changes

#### Add repo-local implementation workflow to `spec.md`

Add a new subsection under the existing developer workflow material:

```markdown
## Repo-local implementation workflow

The `livespec` repository MAY maintain a project-local Claude Code plugin
named `livespec-implementation` under `.claude/plugins/livespec-implementation/`.
This plugin is part of this repository's development workflow only. It MUST
NOT be shipped under `.claude-plugin/`, MUST NOT expose `/livespec:*`
commands, and MUST NOT be described as a first-class LiveSpec product
feature.

The project-local plugin owns three implementation workflow skills:

- `refresh-gaps` compares the current `SPECIFICATION` against this
  repository's implementation, tests, tooling, and workflow state, then
  writes the current implementation-gap report.
- `plan` manages beads issues for implementation work, including creating
  or updating issues for untracked implementation gaps.
- `implement` drives issue-based implementation work, verifies completed
  gap-tied issues by rerunning `refresh-gaps`, and closes beads issues with
  audit notes.

The implementation workflow is downstream from the LiveSpec lifecycle.
`/livespec:propose-change` and `/livespec:revise` remain the only path for
changing `SPECIFICATION`. After a revision changes the expected behavior,
the repo-local implementation layer MAY discover implementation gaps and
map them to beads issues. That discovery requires repository-specific
implementation knowledge and is therefore intentionally outside LiveSpec
core.
```

`revise` placement guidance: this belongs near the current
`## Test-Driven Development discipline`, `## Developer-tooling layout`, and
`## Definition of Done` material in `SPECIFICATION/spec.md`, because it
defines this repository's own implementation workflow rather than shipped
LiveSpec user behavior. The subsection SHOULD mention that the model follows
the Open Brain project-local plugin pattern, but MUST state that the
implementation layer is local to this repository and downstream of
`SPECIFICATION` revision.

#### Add implementation workflow contracts to `contracts.md`

Add a new section describing the project-local command and artifact surface:

```markdown
## Project-local implementation plugin contracts

The project-local implementation plugin root is:

- `.claude/plugins/livespec-implementation/.claude-plugin/plugin.json`
- `.claude/plugins/livespec-implementation/skills/refresh-gaps/SKILL.md`
- `.claude/plugins/livespec-implementation/skills/plan/SKILL.md`
- `.claude/plugins/livespec-implementation/skills/implement/SKILL.md`
- `.claude/plugins/livespec-implementation/skills/_shared/commit-discipline.md`

The plugin manifest SHOULD mirror the Open Brain project-local manifest
shape, adapted to the `livespec-implementation` name and purpose. Reference:
https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/plugins/openbrain/.claude-plugin/plugin.json#L1-L8

The command namespace is:

- `/livespec-implementation:refresh-gaps`
- `/livespec-implementation:plan`
- `/livespec-implementation:implement`

The implementation gap report lives under `implementation-gaps/`:

- `implementation-gaps/current.json`
- `implementation-gaps/current.schema.json`

`implementation-gaps/current.json` MUST be machine-readable JSON and MUST
validate against `implementation-gaps/current.schema.json`. The report MUST
include, at minimum:

- `schema_version`
- `generated_at`
- `spec_sources` fingerprints for the root `SPECIFICATION` files read
- `inspection` metadata explaining what was and was not inspected
- `gaps[]`
- `summary`

Each `gaps[]` entry MUST include:

- `id` matching `gap-[0-9]{4,}`
- `area`
- `severity`
- optional operator-assigned `priority`
- `title`
- `spec_refs`
- `expected`
- `observed`
- `evidence`
- `evidence_kind`
- `destructive_to_fix`
- `destructive_reason`
- `fix_hint`
- `depends_on`

The report schema SHOULD be modeled on Open Brain's current drift schema,
with names adapted from `PLAN/current-specification-drift.*` to
`implementation-gaps/current.*` and with LiveSpec-specific `area` values.
Reference:
https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/PLAN/current-specification-drift.schema.json#L1-L225

All user-facing helper and verification entry points for this layer MUST be
exposed through the `implementation:*` justfile namespace. Initial required
targets:

- `just implementation:setup-beads`
- `just implementation:beads-doctor`
- `just implementation:refresh-gaps`
- `just implementation:check-gaps`
- `just implementation:check-gap-tracking`

`just implementation:setup-beads` MUST cover the role that
`pnpm run setup:beads` covers in Open Brain. `just
implementation:beads-doctor` MUST cover the role that
`pnpm run bd:doctor` covers there. Reference:
https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/package.json#L39-L41

The implementation layer MUST NOT introduce a top-level `scripts/` directory
or a parallel user-facing command surface. If helper code is needed, it
MUST live under the repository's existing development-tooling conventions
and be invoked through `just implementation:*`.
```

`revise` placement guidance: this belongs in `SPECIFICATION/contracts.md`
because it defines concrete command names, artifact paths, file names, and
schema obligations. Do not put the schema itself inline in full unless that
matches existing contract style; a concise field contract is sufficient, with
full schema emitted during implementation under
`implementation-gaps/current.schema.json`.

#### Add beads and gap-tracking constraints to `constraints.md`

Add a new section under developer-tooling constraints:

```markdown
## Project-local implementation tracking constraints

The `livespec` repository uses beads (`bd`) as the canonical task tracker
for repo-local implementation work.

`bd` and `lefthook` MUST be pinned through `.mise.toml`. The initial
implementation SHOULD use the same versions currently vetted by Open Brain
unless newer versions have been deliberately tested with the setup and
doctor guards below. `lefthook` MUST NOT be installed through npm or a
node package because its postinstall behavior can overwrite
`core.hooksPath` and bypass Beads hook wrappers. Open Brain pin reference:
https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.mise.toml#L1-L7

Beads issue ids for this repository's implementation workflow use the
prefix `li-`. Every current implementation gap id in
`implementation-gaps/current.json` MUST appear exactly once as a label on
one beads issue across all statuses. Closed beads issues MAY retain labels
for retired gaps; the invariant is one-way from current gaps to tracked
issues.

The beads Dolt database is the source of truth. `.beads/issues.jsonl` is a
git-tracked human-readable export view only. Developers and agents MUST NOT
hand-edit `.beads/issues.jsonl`, MUST NOT treat it as the sync protocol,
and MUST NOT run manual JSONL import/export as ordinary workflow. Beads'
own Dolt-backed sync and hook behavior is authoritative.

Agent-facing repository instructions MUST explain the Beads architecture:
the Dolt database as source of truth, `refs/dolt/data` as the git-pushed
sync ref, `.beads/issues.jsonl` as derived export, the purpose of `bd prime`
and `bd remember`, upstream documentation entry points, and common
anti-patterns. Open Brain reference:
https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/AGENTS.md#L284-L414

The implementation workflow MUST use noninteractive `bd` commands only.
`bd edit` is forbidden because it opens `$EDITOR`. Agents MUST use
`bd create`, `bd update`, `bd close`, `bd dep`, `bd ready`, `bd show`, and
other noninteractive forms with `--json` when command output informs a
follow-up action.

The implementation workflow MUST preserve the existing repository hook
discipline. Beads hooks and lefthook MUST be chained so that existing
`just check` / pre-commit / pre-push gates continue to run. Hook failures
MUST be surfaced and fixed, not bypassed. `--no-verify`, force-push, and
bulk staging (`git add -A`, `git add .`, `git commit -a`) remain forbidden
for implementation workflow skills.

`just implementation:setup-beads` MUST adapt Open Brain's setup guardrails
to this repository. It MUST install or resolve the pinned `bd` and
`lefthook` through `mise`; skip unsafe setup in git worktrees; initialize
or bootstrap an embedded Dolt database with the `li-` prefix; prefer
`refs/dolt/data` as the bootstrap source; clean stale lock files only when
no live lock holder exists; detect symlink corruption; detect workspace
identity mismatch with a real database-opening probe; move a mismatched
local `.beads/embeddeddolt/` aside to a timestamped backup before
rebuilding; assert the `origin` Dolt remote; assert `dolt.auto-commit=on`
and `export.auto=true`; set `.beads/` permissions to `0700` until the
upstream permissions fix is available in the pinned Beads release; assert
`core.hooksPath = .beads/hooks`; and rewrite hook files only through the
canonical setup target. The generated hook wrappers MUST dispatch lefthook
through `mise exec -- lefthook` and MUST warn or fail if a `node_modules`
lefthook installation returns. Open Brain
references:
https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/setup-beads.sh#L1-L30
https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/setup-beads.sh#L37-L86
https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/setup-beads.sh#L94-L156
https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/setup-beads.sh#L158-L209

Hook templates managed by `just implementation:setup-beads` MUST run the
existing lefthook-managed repository gates first, then Beads hook behavior,
while preserving and returning the lefthook exit status. Open Brain
reference:
https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/setup-beads.sh#L211-L334

`just implementation:beads-doctor` MUST exist because upstream `bd doctor`
does not cover the embedded-mode checks this repository needs. It MUST
check the resolved `bd` version and path, `.beads/embeddeddolt` presence,
git hook path, Dolt remote wiring, pushed `refs/dolt/data`, local Dolt
status, `dolt.auto-commit`, `export.auto`, `core.hooksPath`, and
lefthook resolution through `mise`. Open Brain references:
https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/bd-doctor.sh#L1-L49
https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/bd-doctor.sh#L102-L199
https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/scripts/bd-doctor.sh#L205-L289

The local Claude settings SHOULD wire `bd prime` on session start and
pre-compaction so agents begin with recent beads context. Open Brain
reference:
https://github.com/thewoolleyman/openbrain/blob/b3dc01b961e064db1ad02d1e61c32d52364075aa/.claude/settings.json#L1-L25

Every mutating `livespec-implementation` skill invocation MUST begin with a
clean-tree precondition. If the tree is dirty, the skill MUST surface the
dirty paths and ask whether to commit existing work first, stash and
continue, or abort. The skill MUST NOT silently begin on unrelated dirt.

Implementation workflow commits MUST be atomic and reviewable. Each
logical change, gap refresh, beads issue mutation, source edit,
verification record, and closure fact MUST be committed as its own
reviewable unit unless the user explicitly chooses a different split after
being shown the proposed boundaries. Staging MUST name explicit paths.

Gap-tied issue closure with `resolution:fix` MUST rerun
`livespec-implementation:refresh-gaps` or `just implementation:refresh-gaps`
and confirm that the gap no longer appears in
`implementation-gaps/current.json`. If the gap remains, the issue MUST NOT
be closed as fixed.

Closure notes for gap-tied fixes MUST record:

- resolution method
- verification method
- verification timestamp
- commits
- files changed
- destructive actions taken
- user approval reference for destructive actions, when applicable
- migrations, deployments, secret changes, or external changes, when
  applicable

Non-fix gap closures use `resolution:wontfix`, `resolution:spec-revised`,
`resolution:duplicate`, `resolution:no-longer-applicable`, or
`resolution:resolved-out-of-band`. These are planning decisions and MUST NOT
fabricate fix-verification metadata.
```

`revise` placement guidance: these constraints belong in
`SPECIFICATION/constraints.md` near developer-tooling, testing, hook, and
branch-protection constraints. They define the repository's implementation
discipline and Beads safety model; they MUST NOT be added to shipped
LiveSpec command contracts as product behavior.

#### Add implementation workflow scenarios to `scenarios.md`

Add scenarios for the project-local workflow:

```markdown
## Project-local implementation workflow scenarios

Scenario: refreshed implementation gaps after a SPECIFICATION revision

Given a `SPECIFICATION` revision has landed through `/livespec:revise`
And the implementation may no longer satisfy the revised `SPECIFICATION`
When the maintainer invokes `/livespec-implementation:refresh-gaps`
Then `implementation-gaps/current.json` is regenerated
And the report identifies implementation gaps using `gap-NNNN` ids
And the command does not edit `SPECIFICATION`
And the command does not create or close beads issues

Scenario: planning creates beads issues for untracked current gaps

Given `implementation-gaps/current.json` contains a current gap `gap-0007`
And no beads issue across any status carries the `gap-0007` label
When the maintainer invokes `/livespec-implementation:plan`
Then the skill surfaces `gap-0007` as untracked
And, after user confirmation, creates one beads issue labeled `gap-0007`
And commits the beads export view as a reviewable planning commit

Scenario: implementation closes a verified gap-tied issue

Given a beads issue labeled `gap-0007` is selected for implementation
And the issue has been claimed with `bd update <id> --claim`
When the implementation work lands
And `/livespec-implementation:refresh-gaps` regenerates
`implementation-gaps/current.json`
And `gap-0007` no longer appears in the current gaps array
Then the implementation skill appends closure audit notes
And applies `resolution:fix`
And closes the beads issue
And commits the closure fact separately from the source edit

Scenario: implementation refuses to close an unverified gap-tied issue

Given a beads issue labeled `gap-0007` is selected for implementation
When the implementation work lands
And `implementation-gaps/current.json` still contains `gap-0007` after
refresh
Then the implementation skill refuses to close the issue as fixed
And surfaces the remaining observed gap
And asks whether to retry, split follow-up work, or hand off to planning for
a non-fix closure decision

Scenario: beads setup preserves existing repository gates

Given the repository already uses lefthook and `just check` as enforcement
gates
When the maintainer invokes `just implementation:setup-beads`
Then the command resolves the pinned `bd`
And resolves lefthook through `mise`
And initializes or repairs embedded Beads state without replacing the
existing enforcement model
And sets `core.hooksPath` to `.beads/hooks`
And writes hook wrappers that run existing lefthook behavior first
And then run Beads hook behavior
And a failing lefthook gate still fails the overall hook

Scenario: beads doctor reports implementation-tracking drift

Given the repository uses embedded Beads state
When the maintainer invokes `just implementation:beads-doctor`
Then the command checks the pinned `bd` path and version
And checks embedded Dolt presence and status
And checks Dolt remote wiring and pushed `refs/dolt/data`
And checks `dolt.auto-commit` and `export.auto`
And checks `core.hooksPath` and lefthook resolution
And reports actionable repair instructions for any failed check

Scenario: current gaps must map to exactly one beads issue

Given `implementation-gaps/current.json` contains `gap-0007`
When `just implementation:check-gap-tracking` runs
Then exactly one beads issue across all statuses must carry label
`gap-0007`
And zero matching issues fails the check
And two or more matching issues fail the check
And closed issues may retain labels for retired gap ids that no longer
appear in `implementation-gaps/current.json`

Scenario: implementation workflow remains outside LiveSpec core

Given the project-local implementation plugin exists under
`.claude/plugins/livespec-implementation/`
When the shipped LiveSpec plugin is packaged from `.claude-plugin/`
Then no `livespec-implementation` skill is included in the shipped plugin
And no `/livespec:*` command performs implementation gap discovery
And LiveSpec core remains limited to `SPECIFICATION` lifecycle governance
```

### Non-goals and Boundaries

- This proposal does NOT add implementation gap discovery to the shipped
  LiveSpec plugin.
- This proposal does NOT require other projects using LiveSpec to use beads.
- This proposal does NOT define a universal implementation-gap schema for
  arbitrary repositories.
- This proposal does NOT replace the existing Red/Green, `just check`,
  lefthook, branch protection, or semantic-release discipline.
- This proposal does NOT create or initialize `.beads/` or
  `implementation-gaps/`; those are follow-up implementation tasks after
  this proposal is revised into the live `SPECIFICATION`.
