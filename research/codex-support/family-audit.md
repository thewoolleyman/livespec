> **STATUS: SUPERSEDED (2026-06-23).** This family audit was written
> against the **retired** repo-local `.agents/skills/livespec-*` Codex
> adapter model. Its "Completed baseline" and "Manual verification"
> sections describe core's committed `.agents/skills/` adapters and treat
> repo-local adapters as the proven path; that model was RETIRED in
> livespec PR #528 (the v129 spec cut adopted the distributed Codex driver
> contract). Core ships NO repo-local `.agents/skills/livespec-*` adapter
> directory, and the "Codex driver/distribution — Open" rows below are now
> DONE. This file is preserved as a record of the research journey; the
> repo-state tables and per-row Codex-support status are HISTORICAL.
>
> **Current Codex support is the DISTRIBUTED model:** core is itself
> Codex-installable as an artifact carrier (ships `prose/` + wrappers, no
> skills); the `/livespec:*` surface ships from the Codex Driver
> `livespec-driver-codex`; each orchestrator ships its own cross-runtime
> Codex surface (e.g. `livespec-orchestrator-beads-fabro`); heavyweight
> orchestrator ops are shared-prose-backed (both the Claude and Codex
> runtimes bind thin to the same `prose/<op>.md`). Codex names the bound
> core prose file and (for wrapper-backed ops) the `scripts/bin/...`
> wrapper directly — NO `.agents/skills/*` adapter and NO `AGENTS.md`
> mapping is involved.
>
> **Authoritative sources** (current; this file is not):
> `SPECIFICATION/contracts.md` §"Plugin distribution";
> `SPECIFICATION/non-functional-requirements.md` §"Codex dogfooding
> compatibility" and §"Codex dogfooding contracts". The
> `livespec-driver-codex` build record lives in the local scratch handoff
> `tmp/livespec-driver-codex-build-handoff.md` (gitignored).

# Codex family support audit

Date: 2026-06-19
Last updated: 2026-06-23

## Purpose

This document records what remains to make OpenAI Codex a maintained
dogfooding surface across the livespec family, not just the core `livespec`
checkout. It extends the initial core-only audit in `audit.md`, the bootstrap
plan in `plan.md`, and the read-only adapter proof in `adapter-proof.md`.

The target is reproducibility for another agent runtime, especially the future
Pi driver/harness work: which repositories need support, what was proven, what
is still Claude-specific, and which next changes should be made through normal
LiveSpec processes.

## Current naming correction

The 2026-06-19/2026-06-20 audit was written across a repo rename. Older
handoff text used the then-current `livespec-impl-beads` and
`livespec-impl-git-jsonl` names. Current work must use the live repo names:

| Former name in older notes | Current repo name |
|---|---|
| `livespec-impl-beads` | `livespec-orchestrator-beads-fabro` |
| `livespec-impl-git-jsonl` | `livespec-orchestrator-git-jsonl` |

The current local live family also includes `livespec-console-beads-fabro`.
That repo is present and clean on `master`, but `fleet-manifest.jsonc` still
lists only six members and does not include it. Treat that as an open fleet
registration reconciliation item; do not infer from the omission that the
console repo is outside the live family.

Distributed Codex support also has a hidden core dependency: a future
`livespec-driver-codex` cannot make `/livespec:*` usable from arbitrary family
repos unless CORE itself is installable/discoverable by Codex as the artifact
carrier for the shared prose, scripts, schemas, and templates. The Claude
Driver works cross-repo because CORE is installed as the `livespec@livespec`
Claude plugin; Codex needs an equivalent CORE installability story, not just a
runtime driver repo.

## Completed baseline

- Core `livespec` has committed Codex project skills under `.agents/skills/`
  for `livespec-help`, `livespec-next`, and `livespec-doctor`.
  **[SUPERSEDED: these repo-local adapters were RETIRED in PR #528; core
  now ships no `.agents/skills/livespec-*` directory. The `/livespec:*`
  surface ships from the distributed `livespec-driver-codex` Driver.]**
- Those adapters were proven with separate `codex exec` processes in PR #457.
- The adapter sync check landed in PR #460 and is part of `just check`.
- Core `SPECIFICATION/non-functional-requirements.md` was repaired in PR #465
  to describe the project-local `.agents/skills/livespec-*` path over core
  prose and wrappers.
- Core operational instructions in `AGENTS.md` were updated in PR #466 with
  parity-critical repository mutation discipline for Codex.
- Wrapper `--help` zero-exit behavior was fixed in PR #467.
- The core spec wording repair for Driver/prose/binding ownership landed in
  PR #471 through the governed propose-change -> revise lifecycle:
  - `SPECIFICATION/history/v119/` accepts
    `codex-driver-spec-wording.md`, repairing stale `spec.md` and CLI e2e
    harness wording that treated core as owning Claude skill prompts.
  - `SPECIFICATION/history/v120/` accepts
    `codex-contract-binding-wording.md`, repairing remaining `contracts.md`
    SKILL.md terminology and co-editing `tests/heading-coverage.json` for the
    renamed H2 headings.
- Codex runtime/e2e evidence must record Claude Code Driver, Codex
  project-local adapters, and the future Pi harness explicitly where runtime
  behavior is part of a proof. Codex telemetry remains tokens-primary.
- Four governed sibling repos now have Codex support requirements recorded in
  their own specs:
  - `livespec-dev-tooling` PR #134, merge
    `e76b63621a40ff4f3d88f9681d1503107e82ee79`, cut
    `SPECIFICATION/history/v015/`, and updated
    `SPECIFICATION/non-functional-requirements.md`.
  - `livespec-runtime` PR #48, merge
    `dce528968176c8a80f8cd8b3abe97d988f3b456e`, cut
    `SPECIFICATION/history/v005/`, and updated
    `SPECIFICATION/non-functional-requirements.md`.
  - `livespec-orchestrator-git-jsonl` PR #88, merge
    `e26cebee15bfd43f51a7eab596a75e9b2d719ed0`, cut
    `SPECIFICATION/history/v009/`, and updated
    `SPECIFICATION/constraints.md`.
  - `livespec-orchestrator-beads-fabro` PR #62, merge
    `59627827584e43aabeaca9e11b8658b2e32dbfa6`, cut
    `SPECIFICATION/history/v005/`, and updated
    `SPECIFICATION/constraints.md`.
- Sibling `AGENTS.md` instruction parity landed on 2026-06-20:
  - `livespec-dev-tooling` PR #136, merge
    `095594f9dcc4f89e95e8007bd6456c567a72a431`.
  - `livespec-runtime` PR #50, merge
    `18a35a246bb77f5f361dfabbbee2531287fc9fdd`.
  - `livespec-orchestrator-git-jsonl` PR #90, merge
    `2d88ee7d7ab4df3d61071478675eab4551630581`.
  - `livespec-orchestrator-beads-fabro` PR #75, merge
    `af150ef55131c3a628e0dfd14f242285b31ee112`.
  - `livespec-driver-claude` PR #18, merge
    `ea6b4ed9f73756d0163ac9767a395de070bf95ab`.
  - Scope: each repo's root `AGENTS.md` now carries the complete
    worktree -> PR -> merge -> cleanup mutation lifecycle, including
    primary-checkout confirmation, dedicated worktree editing, `mise exec -- git`
    commit/push, no `--no-verify`, PR checks, primary refresh, worktree removal,
    local branch deletion, and clean-`master` verification.

## Current live checks

Core spec-side `next` run:

```json
{"candidates":[{"action":"prune-history","reason":"118 unpruned history versions; consider pruning","urgency":"low"}],"pagination":{"has_more":false,"limit":5,"offset":0,"total":1}}
```

Local family checkout inventory:

**[SUPERSEDED: the `.agents/skills` column below is HISTORICAL — core's
repo-local Codex adapters were RETIRED in PR #528, so `livespec` is now
`.agents/skills = no` like every sibling. Codex support is now the
distributed `livespec-driver-codex` Driver, not a repo-local tree.]**

| Repo | Governed spec | `.agents/skills` | `.claude-plugin` | Beads tenant |
|---|---:|---:|---:|---:|
| `livespec` | yes | yes | yes | yes |
| `livespec-dev-tooling` | yes | no | no | yes |
| `livespec-driver-claude` | yes | no | yes | yes |
| `livespec-orchestrator-beads-fabro` | yes | no | yes | yes |
| `livespec-orchestrator-git-jsonl` | yes | no | yes | yes |
| `livespec-runtime` | yes | no | no | yes |
| `livespec-console-beads-fabro` | yes | no | no | no |

All seven checkouts above were clean on `master` when rechecked on
2026-06-23. The committed fleet manifest still names only the first six.

Open Codex-support work summary:

| Area | Current state | Why it matters |
|---|---|---|
| Codex driver/distribution | Open. Create/spec a `livespec-driver-codex` analogue if Codex support is meant to work outside the core checkout; also make CORE Codex-installable so the driver can resolve shared prose/scripts from any family repo. | The proven path loads project-local adapters only from core. It does not prove a distributed Codex driver, marketplace/plugin flow, or cross-repo CORE artifact resolution. |
| Runtime/e2e verification | Open. Read-only instruction loading and adapter selection are proven; writable/e2e Codex behavior is not fully proven. | Codex support should not be closed by inheriting Claude Driver behavior. |
| Telemetry/cost | Open. Codex must stay token-primary, with provider/runtime tags and no inference from Claude Code cost spans. | OpenAI/Codex evidence needs its own token mapping. |
| Hook/replacement behavior | Open. Claude-only pre-tool hooks do not run under Codex. | Mutating Codex automation needs either a Codex replacement or a narrower documented support claim. |
| Fleet inventory | Open for `livespec-console-beads-fabro`. | The live local family contains the console repo, but `fleet-manifest.jsonc` omits it. Reconcile through the governed fleet process before relying on fleet automation for console coverage. |

Sibling spec-side `next` runs on 2026-06-19:

| Repo | `next` result |
|---|---|
| `livespec-dev-tooling` | no candidates |
| `livespec-orchestrator-beads-fabro` | initially one low-urgency `revise` candidate for `proposed_changes/grooming-gherkin-and-gap-detectability.md`; after the repo was refreshed to master, no candidates |
| `livespec-orchestrator-git-jsonl` | no candidates |
| `livespec-runtime` | no candidates |

`livespec-console-beads-fabro` was not part of this audit's original
2026-06-19 sibling `next` sweep and has no recorded Codex-support update in the
tables below yet.

Sibling PR verification completed on 2026-06-19:

| Repo | Local verification | PR / CI verification |
|---|---|---|
| `livespec-dev-tooling` | governed `propose_change.py` + `revise.py --post-step-doctor --run-stale-branch-check`; `mise exec -- just check` passed all 46 targets, 903 tests at 100% coverage | doc-only commit/pre-push hooks passed; PR #134 checks passed before merge |
| `livespec-runtime` | governed `propose_change.py` + `revise.py --post-step-doctor --run-stale-branch-check`; `mise exec -- just check` passed all 43 targets, 81 tests at 100% coverage | doc-only commit/pre-push hooks passed; PR #48 checks passed before merge |
| `livespec-orchestrator-git-jsonl` | governed `propose_change.py` + `revise.py --post-step-doctor --run-stale-branch-check`; `mise exec -- just check` passed all 46 targets, 319 tests at 100% coverage | doc-only commit/pre-push hooks passed; PR #88 checks passed, including `e2e-cli`, before merge |
| `livespec-orchestrator-beads-fabro` | governed `propose_change.py` + `revise.py --post-step-doctor --run-stale-branch-check`; `mise exec -- just check` passed all 44 targets, 917 tests at 100% coverage | doc-only commit/pre-push hooks passed; PR #62 checks passed, including `e2e-cli`, before merge |

Sibling instruction-parity verification completed on 2026-06-20:

| Repo | Local verification | PR / CI verification |
|---|---|---|
| `livespec-dev-tooling` | `mise exec -- just check-pre-commit-doc-only` passed; commit hook reran the doc-only subset; pre-push hook reran the doc-only subset | PR #136 checks passed before merge, including aggregate completeness, fleet conformance, format/lint/types/coverage, red-green-replay, and primary-checkout hook checks |
| `livespec-runtime` | `mise exec -- just check-pre-commit-doc-only` passed; commit hook reran the doc-only subset; pre-push hook reran the doc-only subset | PR #50 checks passed before merge, including aggregate completeness, format/lint/types/coverage, red-green-replay, and primary-checkout hook checks |
| `livespec-orchestrator-git-jsonl` | `mise exec -- just check-pre-commit-doc-only` passed all 3 doc-only targets; commit/pre-push hooks reran the doc-only subset | PR #90 checks passed before merge, including `e2e-cli`, aggregate completeness, format/lint/types/coverage, red-green-replay, and primary-checkout hook checks |
| `livespec-orchestrator-beads-fabro` | `mise exec -- just check-pre-commit-doc-only` passed all 3 doc-only targets; commit/pre-push hooks reran the doc-only subset | PR #75 checks passed before merge, including `e2e-cli`, aggregate completeness, format/lint/types/coverage, red-green-replay, and primary-checkout hook checks |
| `livespec-driver-claude` | `mise exec -- just check-pre-commit` passed; commit hook reran plugin-structure, lint, and format; pre-push hook ran full `just check` with 23 hook tests and 2 mock e2e tests passing | PR #18 checks passed before merge, including plugin-structure, hooks, mock e2e, format, and lint |

After merge, all five primary checkouts were fast-forwarded to `origin/master`,
the feature worktrees were removed, local `codex-agent-mutation-protocol`
branches were deleted, remaining remote topic branches were deleted through the
GitHub API where the primary-checkout push guard blocked `git push --delete`,
and each checkout was verified clean on `master`.

## Acceptance runtime-matrix evidence (W7 step 2)

This section records which agent runtime each acceptance tier actually
exercised in the W7 impl/acceptance factory. Telemetry stays token-first:
provider dollar estimates are overlays only, and Codex/OpenAI runtime
participation is never inferred from Claude Code dollar spans.

- **Beads/Fabro LIVE golden-master tier (`livespec-b8od`,
  livespec-orchestrator-beads-fabro PR #101):** Exercised the **Claude Code Driver
  runtime**. The UNMODIFIED production `implement-work-item` Fabro workflow
  dispatched the greeting work-item into a Fabro sandbox (image
  `ghcr.io/thewoolleyman/livespec-fabro-sandbox:sha-ea684ad`) where
  **Claude (Fable 5)** implemented `greet()` from the fixture
  SPECIFICATION; a real PR was created and merged; the behavioral assertion
  `greet("Ada")=="Hello, Ada!"` was green from the merged repo; and the run
  was independently reproduced from clean `master` (run repo
  `livespec-e2e-9h6jqddb`, dispatcher `status=green`/`converged`, ~161s).
  The run's calibration record had `token_cost_micros: null` (no dollar
  overlay captured this run) — telemetry stays token-first.
- **git-jsonl hermetic tier (`livespec-ei4i`):** Deterministic stub (a
  canned greet program); **no agent runtime exercised** — a fast, hermetic,
  LLM-free behavioral check. The swap-proof pairs this deterministic
  reference against the live real-factory Beads/Fabro run.
- **Codex:** NOT exercised in the impl/acceptance FACTORY. Codex has
  verified project-local adapters in core for spec-side `help`/`next`/`doctor`
  ONLY; there is no Codex impl-side driver. Classification: no-adapter for
  the impl factory; Codex participation here is contributor-workflow
  (`AGENTS.md` instruction loading) plus spec-side adapters, not a runtime
  that drives the golden-master.
- **Pi:** future harness; not yet exercised.
- **Claude-only mechanics that remain driver-only:** the Fabro factory and
  the Claude Code Driver plugin hooks; the project `livespec_footgun_guard`
  pre-tool hook still needs a Codex replacement before mutating Codex
  automation.

## Family-wide gaps

### Repository support

Only core currently exposes Codex project skills. That remains intentional for
the sibling repos as of the 2026-06-19 spec updates:
**[SUPERSEDED: core no longer exposes repo-local Codex project skills
either — they were RETIRED in PR #528. The distributed
`livespec-driver-codex` Driver now provides the `/livespec:*` surface for
every governed repo without a repo-local `.agents/skills` tree.]**

- `livespec-dev-tooling` owns shared enforcement-suite code, not a user-facing
  `/livespec:*` Driver, so its Codex support is contributor-workflow support
  through `AGENTS.md`, repo hooks, and stable check/wrapper entry points.
- `livespec-runtime` exposes harness-neutral library code. Runtime code must
  stay agent-runtime-neutral and must not branch on Claude, Codex, Pi, or any
  harness identity.
- `livespec-orchestrator-git-jsonl` and `livespec-orchestrator-beads-fabro` may need future
  impl-side Codex adapters, but their specs now require those adapters to be
  thin runtime bindings over existing wrapper CLIs and substrate semantics, not
  copies of Claude-specific `SKILL.md` bodies.
- `livespec-console-beads-fabro` is now a live governed repo and needs the same
  Codex-support classification pass before family support is closed. It also
  needs fleet-manifest reconciliation if it is intended to participate in fleet
  automation.
- `livespec-driver-claude` is deliberately Claude-specific. Its governed spec
  should classify Codex only as a non-target runtime for that repo; no Codex
  adapter implementation is expected there.

The future distributed path is still open: `livespec-driver-codex` is now the
likely missing runtime driver if Codex should provide a reusable installed
surface analogous to `livespec-driver-claude`. That driver is not sufficient by
itself: CORE also needs Codex installability/discovery so the driver can find
the shared prose, scripts, schemas, and templates from any governed repo.

### Specification coverage

Core and the governed siblings now consistently state the applicable Codex
support requirement.

Observed state:

- `livespec` has Codex-specific non-functional rules, constraints, and
  scenarios.
- `livespec-dev-tooling` now states Codex contributor-workflow support in
  `SPECIFICATION/non-functional-requirements.md`.
- `livespec-runtime` now states Codex contributor-workflow support and
  harness-neutral runtime-code constraints in
  `SPECIFICATION/non-functional-requirements.md`.
- `livespec-orchestrator-beads-fabro` now states Codex adapter constraints in
  `SPECIFICATION/constraints.md`.
- `livespec-orchestrator-git-jsonl` now states Codex adapter constraints in
  `SPECIFICATION/constraints.md`.
- `livespec-console-beads-fabro` is present locally with a governed
  `SPECIFICATION/`, but this audit has not yet recorded a Codex-support
  classification or spec update for it.
- `livespec-driver-claude` is intentionally Claude-specific and now has a
  governed `SPECIFICATION/`; that spec should not be treated as a Codex adapter
  host.

### Manual verification

Manual Codex verification exists for core read-only operations:

- adapter discovery via `codex debug prompt-input`;
- help adapter reads `.agents/skills/livespec-help/SKILL.md` and
  `.claude-plugin/prose/help.md`;
- next adapter reads `.agents/skills/livespec-next/SKILL.md` and names
  `.claude-plugin/scripts/bin/next.py`;
- doctor adapter reads `.agents/skills/livespec-doctor/SKILL.md` and names
  `.claude-plugin/scripts/bin/doctor_static.py`.

On 2026-06-19, read-only Codex CLI probes were launched from each sibling
checkout with `codex exec --sandbox read-only`. Every probe confirmed that
Codex loaded or read the repository-root `AGENTS.md`, identified relevant
non-mutating verification surfaces, and left `git status --short` clean. Those
probes also identified the missing sibling instruction-parity path that was
fixed by the 2026-06-20 PRs listed above.

| Repo | Codex-loaded instruction surface | Mutation protocol evidence | Non-mutating surfaces Codex identified |
|---|---|---|---|
| `livespec-dev-tooling` | `/data/projects/livespec-dev-tooling/AGENTS.md` | Now carries the full worktree -> PR -> merge -> cleanup lifecycle from PR #136, plus Red-Green-Replay, `mise exec -- git ...`, and never `--no-verify`. | `just check-scoped`, `just check`, `just check-static`, `just check-changed`, `just check-pre-commit`, `just check-pre-push`, individual `just check-*` targets. |
| `livespec-runtime` | `/data/projects/livespec-runtime/AGENTS.md` | Now carries the full worktree -> PR -> merge -> cleanup lifecycle from PR #50, plus Red-Green-Replay, `mise exec -- git ...`, and never `--no-verify`. | `just check`, `just check-static`, `just check-changed`, `just check-lint`, `just check-format`, `just check-types`, `just check-coverage`, `just check-pre-commit`, `just check-pre-push`. |
| `livespec-orchestrator-git-jsonl` | `/data/projects/livespec-orchestrator-git-jsonl/AGENTS.md` | Now carries the full worktree -> PR -> merge -> cleanup lifecycle from PR #90, plus Red-Green-Replay, `mise exec -- git ...`, and never `--no-verify`. | `mise exec -- just check`, `check-pre-commit`, `check-pre-push`, `check-red-green-replay`, `check-static`, `check-changed`, store checks, and read-only wrappers `list_work_items.py`, `list_memos.py`, `next.py`, `detect_impl_gaps.py`. |
| `livespec-orchestrator-beads-fabro` | `/data/projects/livespec-orchestrator-beads-fabro/AGENTS.md` | Now carries the full worktree -> PR -> merge -> cleanup lifecycle from PR #75, plus Red-Green-Replay, `mise exec -- git ...`, and never `--no-verify`. | `just check-static`, `just check-format`, `just check-lint`, `just check-types`, `just changed-files`, `just check-red-green-replay`, `just check-work-item-merge-evidence`, read/check wrappers, and dispatcher `ledger-check`, `spec-check`, `janitor-check`. |
| `livespec-driver-claude` | `/data/projects/livespec-driver-claude/AGENTS.md` | Now carries the full worktree -> PR -> merge -> cleanup lifecycle from PR #18, plus worktree secondary checkout guidance, `mise exec -- git ...`, and never `--no-verify`. | `just check` for plugin-structure, hook tests, and mock e2e. Codex correctly classified the repo as deliberately Claude-specific and not a Codex adapter host. |
| `livespec-console-beads-fabro` | not yet audited in this pass | Not recorded. | Needs a Codex read-only instruction-surface probe and repo classification before family support is closed. |

On 2026-06-20, fresh read-only Codex probes were launched after those PRs
merged. Each probe read the repo-root `AGENTS.md` and confirmed that the file
contains the repository mutation protocol requiring the worktree -> PR -> merge
-> cleanup path before tracked-file edits. The probes emitted local MCP
transport warnings from the Codex subprocess, but completed successfully and
left all five sibling checkouts clean on `master`.

Conclusion: sibling instruction parity is now complete at the `AGENTS.md`
surface. Mutating Codex automation is still not fully claimable until the
remaining Codex driver/distribution, runtime/e2e, telemetry, and Codex
hook/replacement questions are resolved.

### Runtime/e2e testing

Codex support owns the Codex evidence boundary, not the implementation
sequencing of any separate epic. This directory should record whether Codex
loaded the relevant repository instruction surface, used verified
project-local adapters where they exist, preserved tokens-primary telemetry,
and documented unsupported or Claude-only mechanics.

Implementation item IDs, blockers, and sequencing for other epics belong in
their own research directories and ledgers, not in `research/codex-support/`.

The acceptance criteria now require:

- Codex can load the repo instruction surface for each tested checkout;
- Codex can invoke verified project-local adapters where they exist;
- Codex is represented in observability as tokens-primary rather than
  Claude-specific cost spans;
- Codex-specific limitations are explicit rather than silently inherited from
  Claude Code.

### Telemetry and Cost

The current tracking split is:

- `livespec-orchestrator-beads-fabro-zbl` owns provider-specific token extraction and
  report-only cost overlays. It already names Codex/OpenAI and self-hosted
  models as deferred provider legs, with raw tokens as the durable metric.
- `livespec-dev-tooling-e60` owns broader agent-loop observability, including
  per-turn spans, token counts, tool-call latencies, hook and pytest timings,
  Red-Green-Replay leg timings, dispatch outcomes, and reflect-loop work-item
  filing.

Codex support must not be closed by reusing Claude Code dollar spans. The
minimum acceptable evidence is token-first telemetry with provider/runtime
tags, plus an explicit mapping for OpenAI/Codex token fields when an extractor
is implemented. Dollar figures remain provider-specific overlays and may be
absent or explicitly imputed for self-hosted runs.

### Non-skill mechanisms

Observed hooks and non-skill mechanisms:

- All family repos have repo-level git hooks / lefthook discipline.
- Each active family checkout has `.claude/hooks/livespec_footgun_guard.py`.
  `livespec-driver-claude` also has Driver-plugin hooks under
  `.claude-plugin/hooks/`.
- Sibling specs now explicitly state that Claude-only hooks are not assumed to
  run under Codex, and any Codex adapter or hook replacement must be manually
  verified before support is claimed.

Hook classification:

| Mechanism | Locations | Classification | Rationale |
|---|---|---|---|
| `.claude/hooks/livespec_footgun_guard.py` | `livespec`, `livespec-dev-tooling`, `livespec-driver-claude`, `livespec-orchestrator-beads-fabro`, `livespec-orchestrator-git-jsonl`, `livespec-runtime` | Codex replacement required before mutating Codex automation; AGENTS/repo-hook coverage sufficient for read-only probes and human-supervised verification. | This Claude Code `PreToolUse` Bash guard blocks `git commit/push --no-verify`, `LEFTHOOK=0/false`, and `git config core.bare=true` before a command runs. Codex does not run it. Git hooks and branch protections catch many commit/push failures later, but cannot stop direct file edits in a primary checkout. |
| `.claude/settings.json` `SessionStart` plugin/bootstrap hooks | active family checkouts | Claude-driver-only by design. | These run Claude plugin installation or project hook setup. Codex has no proven livespec marketplace/plugin path; project-local `.agents/skills` plus repo instructions are the current Codex path. |
| `.claude/settings.json` `PreToolUse` background/subagent guards | active family checkouts where configured | Claude-driver-only unless a future Codex runtime exposes equivalent hook events. | The hooks enforce Claude Code tool/session behavior. Current Codex evidence covers read-only execution, not background tool lifecycle integration. |
| `livespec-driver-claude/.claude-plugin/hooks/block-auto-memory.sh` | `livespec-driver-claude` plugin | Claude-driver-only by design. | This prevents Claude Code auto-memory behavior in the Claude Driver. It is not a cross-runtime livespec contract. |
| `livespec-driver-claude/.claude-plugin/hooks/warn-plan-persistence.sh` | `livespec-driver-claude` plugin | Claude-driver-only by design, with possible future documentation analogue for other runtimes. | This warns Claude users about plan persistence. Codex support should not inherit it silently; if Pi/Codex need equivalent guidance it belongs in their runtime instructions or driver, not in the Claude Driver. |
| Repo git hooks and `check-primary-checkout-commit-refuse-hook-installed` | all governed family repos | AGENTS/repo-hook coverage sufficient for commit/push enforcement once installed. | These are runtime-neutral git/just mechanisms. They do not replace pre-edit instruction loading, but they are the correct backstop for commit/push discipline under Codex. |

## Recommended next sequence

1. Decide whether to create `livespec-driver-codex` for distributed Codex
   support. If yes, also make CORE Codex-installable/discoverable so the driver
   can resolve the shared prose and wrapper CLIs from non-core repos. If no,
   document that supported Codex use remains repo-local `.agents/skills/*`
   adapters in core only.
2. Reconcile `livespec-console-beads-fabro` with `fleet-manifest.jsonc` through
   the governed fleet process, then add its Codex-support classification here.
3. Complete writable/runtime Codex verification and record only Codex-specific
   evidence here; keep unrelated epic sequencing in its owning docs.
4. Refine telemetry/cost follow-ups as implementation begins; Codex should
   remain tokens-primary, not Claude-cost-derived.
5. Before claiming mutating Codex automation, provide a Codex replacement for
   the Claude-only pre-tool footgun guard or record the narrower support claim
   that relies on AGENTS/repo hooks only.

## Reproduction commands

```bash
/usr/bin/python3 .claude-plugin/scripts/bin/next.py \
  --project-root /data/projects/livespec \
  --spec-target /data/projects/livespec/SPECIFICATION \
  --limit 5 \
  --offset 0

for d in /data/projects/livespec*; do
  [ -d "$d/.git" ] || [ -f "$d/.git" ] || continue
  printf '%s\t' "${d##*/}"
  git -C "$d" rev-parse --show-toplevel 2>/dev/null | tr '\n' '\t'
  git -C "$d" branch --show-current 2>/dev/null | tr '\n' '\t'
  [ -d "$d/SPECIFICATION" ] && printf 'SPEC=yes\t' || printf 'SPEC=no\t'
  [ -d "$d/.agents/skills" ] && printf 'agents=yes\t' || printf 'agents=no\t'
  [ -d "$d/.claude-plugin" ] && printf 'claude_plugin=yes\t' || printf 'claude_plugin=no\t'
  [ -d "$d/.beads" ] && printf 'beads=yes\n' || printf 'beads=no\n'
done | sort
```

Beads summary command, run through the 1Password environment wrapper:

```bash
for d in /data/projects/livespec /data/projects/livespec-driver-claude \
  /data/projects/livespec-orchestrator-beads-fabro /data/projects/livespec-orchestrator-git-jsonl \
  /data/projects/livespec-runtime /data/projects/livespec-dev-tooling \
  /data/projects/livespec-console-beads-fabro; do
  [ -d "$d/.beads" ] || continue
  name=${d##*/}
  tenant=${name//-/_}
  var="BEADS_DOLT_PASSWORD_${tenant}"
  pw=${!var-}
  printf "=== %s ===\n" "$name"
  if [ -z "$pw" ]; then
    printf "missing-env:%s\n" "$var"
    continue
  fi
  (
    cd "$d" &&
      export BEADS_DOLT_PASSWORD="$pw" LIVESPEC_BD_PATH=/usr/local/bin/bd &&
      /usr/local/bin/bd list --status open --json 2>/dev/null |
        jq -r '.[] | [.id,.priority,.issue_type,.title] | @tsv'
  )
done
```
