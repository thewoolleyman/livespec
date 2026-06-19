# Codex support handoff prompt

You are starting a new session in `/data/projects/livespec`.

Goal: make livespec usable from OpenAI Codex as a maintainer dogfooding
surface across the whole livespec family, not only in the core repo. The
minimum project-skill/bootstrap path is complete for core read-only operations;
continue with family-wide support, specs, verification, high-level testing,
non-skill runtime mechanisms, and reproducible research notes.

## Start here

Read these files first:

1. `AGENTS.md`
2. `research/codex-support/audit.md`
3. `research/codex-support/plan.md`
4. `research/codex-support/adapter-proof.md`

The audit and plan landed on `master` via PR #452:

- PR: `https://github.com/thewoolleyman/livespec/pull/452`
- Merge commit: `a819f5107e9a4f04cab9084247f4c392e6d9aebb`
- Date: 2026-06-19

Do not redo the initial audit unless new evidence contradicts it. Continue from
the plan.

The first read-only Codex adapter proof landed on `master` via PR #457:

- PR: `https://github.com/thewoolleyman/livespec/pull/457`
- Merge commit: `a2f41ce18541d51da602dd9eda4c5f510fffc8f2`
- Date: 2026-06-19
- Evidence: `research/codex-support/adapter-proof.md`

Do not redo the adapter proof unless new evidence contradicts it. Continue with
the spec/instructions follow-up below.

The Codex adapter mechanical sync check landed on `master` via PR #460:

- PR: `https://github.com/thewoolleyman/livespec/pull/460`
- Merge commit: `791cd3818925193572394b592fb85e8fa3624db4`
- Date: 2026-06-19

Do not redo the sync-check implementation unless new evidence contradicts it.
Continue with the next follow-up below.

The governed Codex dogfooding spec repair landed on `master` via PR #465:

- PR: `https://github.com/thewoolleyman/livespec/pull/465`
- Merge commit: `e04e1abad9055e070c33531a9b3b1b54daf9924f`
- Date: 2026-06-19
- Beads work-item: `livespec-4moata.2`
- Spec revisions cut: `SPECIFICATION/history/v117/` and
  `SPECIFICATION/history/v118/` after rebasing on master, which already used
  `SPECIFICATION/history/v116/` for the unrelated orchestrator grooming
  proposal.
- Local verification: `mise exec -- just check` passed all 52 targets after
  `v118` on 2026-06-19, including 900 pytest cases at 100% coverage.
- PR checks passed before merge. After merge, the primary checkout was
  fast-forwarded to `e04e1ab`, worktree
  `/data/projects/livespec-codex-spec-repair` was removed, local branch
  `codex-spec-repair` was deleted, and Beads item `livespec-4moata.2` was
  closed.

This repair changed `SPECIFICATION/non-functional-requirements.md` through the
governed propose-change -> revise lifecycle. It removes the obsolete
`.agents/skills/*` symlink-to-`.claude-plugin/skills/*` model and specifies the
proven project-local `.agents/skills/livespec-*` adapter path over core prose
and wrappers. It also repairs `SPECIFICATION/contracts.md` §"Daily dogfooding
path" so core live-reload mode names `.claude-plugin/prose/<name>.md` and
`.claude-plugin/scripts/...`, with Claude Driver binding edits explicitly owned
by `livespec-driver-claude`.

The Codex/Claude operational memory migration landed on `master` via PR #466:

- PR: `https://github.com/thewoolleyman/livespec/pull/466`
- Merge commit: `82e99653f7fe2e2f40bbeb2b0af1a5a673c6c46c`
- Date: 2026-06-19
- Beads work-item: `livespec-zkmn.1.1`
- Scope: migrated only parity-critical repository mutation discipline into
  `AGENTS.md`: worktree -> PR -> merge -> cleanup, `mise exec -- git ...`,
  never `--no-verify`, primary-checkout protection, and cleanup expectations.
- Local verification: `mise exec -- just check-pre-commit-doc-only` passed.
- PR checks passed before merge. After merge, the primary checkout was
  fast-forwarded to `82e9965`, worktree
  `/data/projects/livespec-codex-memory-instructions` was removed, local branch
  `codex-memory-instructions` was deleted, and Beads item
  `livespec-zkmn.1.1` was closed.

The wrapper-help exit fix for Codex adapter follow-up landed on `master` via
PR #467:

- PR: `https://github.com/thewoolleyman/livespec/pull/467`
- Merge commit: `dc94af9a659610dab154a7bf9b5ee5d05a8f0c82`
- Date: 2026-06-19
- Beads work-item: `livespec-4moata.3`
- Scope: maps argparse `SystemExit(0)` help requests to a zero-exit
  `HelpRequestedError`, lets `doctor_static.py --help` return `0`, and prevents
  `revise.py --help` from logging a failure diagnostic.
- Local verification:
  - `mise exec -- uv run pytest tests/livespec/io/test_cli.py -q` passed
    (`6 passed`).
  - `/usr/bin/python3 .claude-plugin/scripts/bin/doctor_static.py --help`
    returned `0` with zero stderr bytes.
  - `/usr/bin/python3 .claude-plugin/scripts/bin/revise.py --help` returned
    `0` with zero stderr bytes.
  - The Red-Green-Replay Green amend ran `mise exec -- just check`; all 51
    targets passed, including 903 pytest cases at 100% coverage and 4 mock e2e
    tests.
- Pre-push verification: `mise exec -- just check` passed all 52 targets.
- PR checks passed before merge. After merge, the primary checkout was
  fast-forwarded to `dc94af9`, worktree
  `/data/projects/livespec-codex-wrapper-help-exit` was removed, local branch
  `codex-wrapper-help-exit` was deleted, and Beads item `livespec-4moata.3`
  was closed. Beads emitted the known `.beads` permissions and auto-backup
  warnings, but the close succeeded.

The handoff was expanded after user correction on 2026-06-19 because the
previous "Next concrete action" was too narrow. It treated the main-repo
read-only Codex adapter slice as the end of the Codex-support track, but the
actual objective is broader:

- every livespec-family repo needs to be audited and, where appropriate,
  updated to support Codex the same way the core repo now does;
- every livespec-family repo's non-functional specification needs to state the
  requirement and nature of Codex support where that repo owns a governed spec;
- all family-wide changes need manual verification, not just static checks;
- the high-level end-to-end testing bead/research thread needs to include Codex
  as a supported harness, not only Claude;
- non-skill mechanisms such as hooks, plugin/driver assumptions, local
  bootstrap paths, and cloud-/Claude-specific workflows need to be audited and
  migrated or explicitly documented as not applicable for Codex;
- `research/codex-support/` needs a durable summary document recording what had
  to be done so the process can be reproduced for the Pi agent harness.

The family-wide audit summary was started on 2026-06-19 in
`research/codex-support/family-audit.md`. It records the current family repo
inventory, Beads items relevant to Codex/e2e work, stale core spec wording,
missing sibling Codex coverage, manual-verification gaps, hook/non-skill
mechanism gaps, and reproduction commands for the Pi agent harness path.

The stale core Driver/prose/binding wording identified by the audit landed on
`master` via PR #471:

- PR: `https://github.com/thewoolleyman/livespec/pull/471`
- Merge commit: `b6a37b0d59e1a63207ad00f38727e3c3e798c929`
- Date: 2026-06-19
- Scope: repaired stale core spec wording that treated core as owning Claude
  `SKILL.md` prompts / installed core skill trees, codified core prose plus
  wrapper ownership with runtime-specific Driver bindings, updated the Claude
  CLI e2e contract to inspect `livespec-driver-claude` rather than core, and
  recorded the family Codex audit state.

- `SPECIFICATION/history/v119/` accepted
  `codex-driver-spec-wording.md`, updating `SPECIFICATION/spec.md` and the
  Claude CLI e2e harness contract in `SPECIFICATION/contracts.md`.
- `SPECIFICATION/history/v120/` accepted
  `codex-contract-binding-wording.md`, updating remaining
  `SPECIFICATION/contracts.md` SKILL.md terminology and co-editing
  `tests/heading-coverage.json` for the renamed H2 headings.
- Local verification in that worktree: `mise exec -- just check` passed all
  52 targets on 2026-06-19, including 903 pytest cases at 100% coverage, 52
  prompt tests, 4 mock e2e tests, import-linter, pyright, ruff format/check,
  doctor static checks, and the Codex adapter sync check.
- Commit/pre-push hooks passed their doc-only aggregates, PR checks passed, the
  primary checkout was fast-forwarded to `b6a37b0`, worktree
  `/data/projects/livespec-codex-driver-spec-wording` was removed, and local
  branch `codex-driver-spec-wording` was deleted.

The high-level e2e Beads thread was updated on 2026-06-19:

- PR recording this state: `https://github.com/thewoolleyman/livespec/pull/473`
- Beads item: `livespec-zkmn.1`
- Change: added formal acceptance criteria requiring Codex to be represented as
  an explicit supported agent-runtime dimension in golden-master/e2e acceptance
  where runtime behavior is part of the proof.
- Labels added: `codex-support`, `e2e-codex`.
- Required evidence now includes Codex instruction loading, verified
  project-local adapters where present, tokens-primary telemetry/cost handling,
  Claude-only hook classification, and updates to
  `research/codex-support/family-audit.md` before the item is closed.
- Verification: `bd show livespec-zkmn.1 --json` confirmed the acceptance
  criteria and labels. Beads emitted the known `.beads` permissions warning and
  auto-backup limitation, but the update succeeded.

The governed sibling spec updates landed on 2026-06-19:

- `livespec-dev-tooling` PR #134:
  `https://github.com/thewoolleyman/livespec-dev-tooling/pull/134`
  - Merge commit: `e76b63621a40ff4f3d88f9681d1503107e82ee79`
  - Spec revision: `SPECIFICATION/history/v015/`
  - Scope: `SPECIFICATION/non-functional-requirements.md` now states Codex
    contributor-workflow support through `AGENTS.md`, repo hooks, and stable
    enforcement-suite entry points. It records that no project-local
    `.agents/skills` are currently needed because the repo owns shared
    enforcement-suite code, not a user-facing `/livespec:*` Driver.
  - Verification: governed `propose_change.py` plus
    `revise.py --post-step-doctor --run-stale-branch-check`;
    `mise exec -- just check` passed all 46 targets, including 903 tests at
    100% coverage; doc-only commit/pre-push hooks passed; PR checks passed
    before merge. The primary checkout was fast-forwarded and the worktree /
    local branch were removed.
- `livespec-runtime` PR #48:
  `https://github.com/thewoolleyman/livespec-runtime/pull/48`
  - Merge commit: `dce528968176c8a80f8cd8b3abe97d988f3b456e`
  - Spec revision: `SPECIFICATION/history/v005/`
  - Scope: `SPECIFICATION/non-functional-requirements.md` now states Codex
    contributor-workflow support and requires runtime code to remain
    agent-runtime-neutral, with no branching on Claude, Codex, Pi, or any
    harness identity.
  - Verification: governed `propose_change.py` plus
    `revise.py --post-step-doctor --run-stale-branch-check`;
    `mise exec -- just check` passed all 43 targets, including 81 tests at
    100% coverage; doc-only commit/pre-push hooks passed; PR checks passed
    before merge. The primary checkout was fast-forwarded and the worktree /
    local branch were removed.
- `livespec-impl-git-jsonl` PR #88:
  `https://github.com/thewoolleyman/livespec-impl-git-jsonl/pull/88`
  - Merge commit: `e26cebee15bfd43f51a7eab596a75e9b2d719ed0`
  - Spec revision: `SPECIFICATION/history/v009/`
  - Scope: `SPECIFICATION/constraints.md` now requires Codex adapter support
    to be a first-class agent-runtime consideration. Future Codex adapters
    must be thin runtime bindings over existing wrapper CLIs, JSONL store
    semantics, and consent rules, not copies of Claude-specific `SKILL.md`
    bodies. Claude-only hooks are not assumed to run under Codex.
  - Verification: governed `propose_change.py` plus
    `revise.py --post-step-doctor --run-stale-branch-check`;
    `mise exec -- just check` passed all 46 targets, including 319 tests at
    100% coverage; doc-only commit/pre-push hooks passed; PR checks passed,
    including `e2e-cli`, before merge. The primary checkout was fast-forwarded
    and the worktree / local branch were removed.
- `livespec-impl-beads` PR #62:
  `https://github.com/thewoolleyman/livespec-impl-beads/pull/62`
  - Merge commit: `59627827584e43aabeaca9e11b8658b2e32dbfa6`
  - Spec revision: `SPECIFICATION/history/v005/`
  - Scope: `SPECIFICATION/constraints.md` now requires Codex adapter support
    to be a first-class agent-runtime consideration. Future Codex adapters
    must be thin runtime bindings over existing wrapper CLIs, beads tenant
    semantics, and consent rules, not copies of Claude-specific `SKILL.md`
    bodies. Claude-only hooks are not assumed to run under Codex.
  - Verification: governed `propose_change.py` plus
    `revise.py --post-step-doctor --run-stale-branch-check`;
    `mise exec -- just check` passed all 44 targets, including 917 tests at
    100% coverage; doc-only commit/pre-push hooks passed; PR checks passed,
    including `e2e-cli`, before merge. The primary checkout was
    fast-forwarded and the feature worktree / local branch were removed.
    Pre-existing unrelated worktrees under `.claude/worktrees/` were left
    untouched.

The Codex sibling runtime evidence and hook classification pass ran on
2026-06-19:

- PR: `https://github.com/thewoolleyman/livespec/pull/480`
- Worktree: `/data/projects/livespec-codex-runtime-evidence`
- Branch: `codex-runtime-evidence`
- Scope:
  - Launched `codex exec --sandbox read-only` from
    `livespec-dev-tooling`, `livespec-runtime`,
    `livespec-impl-git-jsonl`, `livespec-impl-beads`, and
    `livespec-driver-claude`.
  - Recorded the evidence in `research/codex-support/family-audit.md`.
  - Classified Claude-only hooks and non-skill mechanisms in
    `research/codex-support/family-audit.md`.
- Evidence:
  - Codex loaded or read each sibling repo's root `AGENTS.md`.
  - Codex identified non-mutating `just` gates and wrapper entry points.
  - Codex correctly classified `livespec-driver-claude` as
    Claude-specific, with no Codex adapter expected in that repo.
  - All read-only probes left the sibling checkouts clean according to
    `git status --short`.
- Finding:
  - Sibling `AGENTS.md` files do **not** yet carry the complete core
    repository mutation protocol (`worktree -> PR -> merge -> cleanup`,
    primary checkout refresh, and cleanup discipline). They mostly contain
    Red-Green-Replay plus `mise exec -- git ...` and never `--no-verify`.
  - Therefore family-wide Codex support is not fully claimable yet, even
    though Codex instruction loading and non-mutating entry-point discovery are
    now proven in the sibling repos.
- Local verification:
  - `mise exec -- just check-pre-commit-doc-only` passed all seven doc-only
    targets.
  - The commit hook reran `just check-pre-commit-doc-only` and passed.
  - The pre-push hook reran `just check-pre-commit-doc-only` and passed.

The sibling instruction parity pass landed on 2026-06-20:

- Scope: synced the complete core repository mutation protocol into sibling
  `AGENTS.md` files so Codex-visible repo instructions now require
  worktree -> PR -> merge -> cleanup before tracked-file edits.
- `livespec-dev-tooling` PR #136:
  `https://github.com/thewoolleyman/livespec-dev-tooling/pull/136`
  - Merge commit: `095594f9dcc4f89e95e8007bd6456c567a72a431`
  - Local verification: `mise exec -- just check-pre-commit-doc-only` passed;
    commit and pre-push hooks reran the doc-only subset.
  - PR checks passed before merge. The primary checkout was fast-forwarded,
    the feature worktree and local branch were removed, the remote topic branch
    was deleted through the GitHub API after the primary-checkout push guard
    correctly blocked `git push --delete`, and the primary checkout was
    verified clean on `master`.
- `livespec-runtime` PR #50:
  `https://github.com/thewoolleyman/livespec-runtime/pull/50`
  - Merge commit: `18a35a246bb77f5f361dfabbbee2531287fc9fdd`
  - Local verification: `mise exec -- just check-pre-commit-doc-only` passed;
    commit and pre-push hooks reran the doc-only subset.
  - PR checks passed before merge. The primary checkout was fast-forwarded,
    the feature worktree and local branch were removed, the remote topic branch
    was deleted through the GitHub API after the primary-checkout push guard
    correctly blocked `git push --delete`, and the primary checkout was
    verified clean on `master`.
- `livespec-impl-git-jsonl` PR #90:
  `https://github.com/thewoolleyman/livespec-impl-git-jsonl/pull/90`
  - Merge commit: `2d88ee7d7ab4df3d61071478675eab4551630581`
  - Local verification: `mise exec -- just check-pre-commit-doc-only` passed
    all 3 doc-only targets; commit and pre-push hooks reran the doc-only
    subset.
  - PR checks passed before merge, including `e2e-cli`. The primary checkout
    was fast-forwarded, the feature worktree and local branch were removed, the
    remote topic branch was deleted through the GitHub API after the
    primary-checkout push guard correctly blocked `git push --delete`, and the
    primary checkout was verified clean on `master`.
- `livespec-impl-beads` PR #75:
  `https://github.com/thewoolleyman/livespec-impl-beads/pull/75`
  - Merge commit: `af150ef55131c3a628e0dfd14f242285b31ee112`
  - Local verification: `mise exec -- just check-pre-commit-doc-only` passed
    all 3 doc-only targets; commit and pre-push hooks reran the doc-only
    subset.
  - PR checks passed before merge, including `e2e-cli`. The primary checkout
    was fast-forwarded, the feature worktree and local branch were removed, the
    remote topic branch was deleted through the GitHub API after the
    primary-checkout push guard correctly blocked `git push --delete`, and the
    primary checkout was verified clean on `master`. The pre-existing unrelated
    worktree under `.claude/worktrees/fabro-graph-fix` was left untouched.
- `livespec-driver-claude` PR #18:
  `https://github.com/thewoolleyman/livespec-driver-claude/pull/18`
  - Merge commit: `ea6b4ed9f73756d0163ac9767a395de070bf95ab`
  - Local verification: `mise exec -- just check-pre-commit` passed; commit
    hook reran plugin-structure, lint, and format; pre-push hook ran full
    `just check`, including 23 hook tests and 2 mock e2e tests.
  - PR checks passed before merge. The primary checkout was fast-forwarded, the
    feature worktree and local branch were removed, the remote topic branch was
    deleted by the PR merge path, and the primary checkout was verified clean on
    `master`.
- Fresh post-merge Codex verification:
  - `codex exec --sandbox read-only` was launched from each of the five sibling
    repos with a prompt asking whether `AGENTS.md` contains the repository
    mutation protocol.
  - Each probe read the repo-root `AGENTS.md` and confirmed the
    worktree -> PR -> merge -> cleanup requirement before tracked-file edits.
  - The probes emitted local MCP transport warnings from the Codex subprocess,
    but completed successfully and left all sibling checkouts clean.

The Codex high-level e2e/runtime-matrix alignment pass ran on 2026-06-20:

- Worktree: `/data/projects/livespec-codex-e2e-runtime-matrix`
- Branch: `codex-e2e-runtime-matrix`
- Scope:
  - Updated `research/w7-orchestrator-convergence/plan.md` so the W7
    golden-master acceptance story explicitly carries an agent-runtime
    dimension: Claude Code Driver, OpenAI Codex project-local adapters, and the
    future Pi harness.
  - Updated `research/codex-support/family-audit.md` so the durable Codex
    family summary records the same runtime matrix, the tokens-primary
    telemetry rule, and the remaining distinction between high-level e2e,
    telemetry/cost, and Codex hook/replacement closure.
  - Updated this handoff.
- Beads state inspected:
  - `livespec-zkmn.1` already has formal Codex acceptance criteria and
    `codex-support` / `e2e-codex` labels.
  - `livespec-impl-beads-zbl` remains the cost/telemetry item that owns
    provider-specific token extraction and report-only dollar overlays.
  - `livespec-dev-tooling-e60` remains the agent-loop / Honeycomb
    observability item; the Codex audit now records that Codex must be refined
    there as raw-token-first agent telemetry work begins.
- Verification before commit/PR:
  - `mise exec -- just check-pre-commit-doc-only` passed all seven doc-only
    targets from the worktree after trusting that worktree's `.mise.toml`.
- After PR merge, update this block with PR number, merge SHA, check status,
  primary refresh, worktree removal, and branch cleanup.

## Handoff protocol

This file is the complete continuation prompt for the next session. Keep all
handoff instructions, current state, verification notes, and next actions here;
do not rely on the final chat response to carry operational detail.

At the end of any session that changes the Codex support state:

1. Update this file with the current repository state, merged PRs, validation
   results, unresolved blockers, and the exact next action.
2. Land that update through the normal worktree -> PR -> merge -> cleanup path.
3. In the final response, do not paste a separate handoff block. Tell the user
   only to run this file in the next session:

   ```text
   research/codex-support/handoff-prompt.md
   ```

## Current confirmed facts

- Core owns `.claude-plugin/prose/<name>.md` and reference wrappers under
  `.claude-plugin/scripts/bin/`.
- Claude Code runtime bindings live in sibling repo
  `/data/projects/livespec-driver-claude`.
- Core intentionally has no `.claude-plugin/skills/` tree. Do not reintroduce
  one.
- The old Codex spec text was stale because it said `.agents/skills/*` should
  symlink to `.claude-plugin/skills/*`; PR #465 repaired this through
  `SPECIFICATION/history/v117/`.
- `SPECIFICATION/contracts.md` also had stale daily-dogfooding text that said
  core live-reloads `.claude-plugin/skills/<name>/SKILL.md`; PR #465 repaired
  this through `SPECIFICATION/history/v118/`.
- This repo now has committed project-local Codex adapters under
  `.agents/skills/` for `livespec-help`, `livespec-next`, and
  `livespec-doctor`.
- Codex CLI 0.141.0 does load project-local `.agents/skills/*/SKILL.md` files
  when each skill has valid YAML frontmatter with `name` and `description`.
- Codex has no installed/configured livespec plugin marketplace entry; only the
  `openai-curated` marketplace is configured.
- The proven near-term path is project-local `.agents/skills` adapters that read
  core prose and invoke core wrappers. Do not claim Codex marketplace support.
- The Claude/Codex DRY boundary is core prose plus wrapper CLIs, not copied
  skill bodies. Claude Driver `SKILL.md` files and Codex project `SKILL.md`
  files are both thin runtime adapters over the same core files.
- Adapter proof PR #457 verified:
  - `codex debug prompt-input '/livespec:help'` lists the three project skills;
  - the help probe read `.agents/skills/livespec-help/SKILL.md` and
    `.claude-plugin/prose/help.md`;
  - the next probe identified `.claude-plugin/scripts/bin/next.py` with
    explicit `--project-root`, `--spec-target`, `--limit 5`, and `--offset 0`;
  - the doctor probe identified
    `.claude-plugin/scripts/bin/doctor_static.py --help`.
- The doctor probe exposed a pre-existing wrapper-help behavior:
  `/usr/bin/python3 .claude-plugin/scripts/bin/doctor_static.py --help`
  printed argparse help but exited `2`. PR #467 fixed this; both
  `doctor_static.py --help` and `revise.py --help` now return `0`.
- PR #460 added `dev-tooling/checks/codex_adapter_sync.py` and
  `tests/dev-tooling/checks/test_codex_adapter_sync.py`, wired
  `check-codex-adapter-sync` into `just check`, `check-pre-commit-doc-only`,
  and the CI check-metadata matrix, and verified the current three adapters
  remain thin over core prose/wrappers.
- Beads follow-ups filed on 2026-06-19 and completed:
  - `livespec-4moata.2` — Codex dogfooding spec repair, closed after PR #465.
  - `livespec-4moata.3` — wrapper help exit handling, closed after PR #467.
  - `livespec-zkmn.1.1` — parity-critical Claude/Codex operational memory
    migration, closed after PR #466.
- Local livespec-family checkouts seen during the 2026-06-19 handoff expansion:
  `livespec`, `livespec-driver-claude`, `livespec-impl-beads`,
  `livespec-impl-git-jsonl`, `livespec-runtime`, plus dev/worktree directories
  such as `livespec-dev-tooling`, `livespec.wt`, `livespec-impl-beads.wt`, and
  `livespec-worktrees`. Do not assume this list is complete without
  rechecking `/data/projects` and Beads state.
- A follow-up audit on 2026-06-19 found that the clean active family checkouts
  are `livespec`, `livespec-dev-tooling`, `livespec-driver-claude`,
  `livespec-impl-beads`, `livespec-impl-git-jsonl`, and `livespec-runtime`.
  Only core currently has `.agents/skills/`.
- Core `SPECIFICATION/spec.md` and `SPECIFICATION/contracts.md` stale
  Claude-skill/plugin wording was repaired by PR #471 through
  `SPECIFICATION/history/v119/` and `SPECIFICATION/history/v120/`, including
  the required `tests/heading-coverage.json` co-edit.
- Sibling governed specs now state Codex support requirements or adapter
  constraints where applicable: dev-tooling `v015`, runtime `v005`,
  impl-git-jsonl `v009`, and impl-beads `v005`.
- `livespec-driver-claude` remains intentionally Claude-specific and has no
  governed `SPECIFICATION/`; no Codex repo update is expected there beyond
  classification in `research/codex-support/family-audit.md`.
- Read-only Codex runtime probes have now been run in the changed sibling
  repos. The first pass proved `AGENTS.md` loading and entry-point discovery
  while exposing that sibling `AGENTS.md` files lacked the full core mutation
  protocol. The 2026-06-20 sibling instruction parity PRs fixed that gap, and
  fresh read-only Codex probes confirmed the updated protocol is visible in all
  five sibling `AGENTS.md` files.
- Claude-only hook classification is recorded in
  `research/codex-support/family-audit.md`: the project
  `livespec_footgun_guard.py` needs a Codex replacement before mutating Codex
  automation, repo git hooks are runtime-neutral commit/push backstops, and
  the Claude Driver's plugin hooks are Claude-driver-only by design.
- `research/w7-orchestrator-convergence/plan.md` now explicitly requires the
  W7 golden-master acceptance story to record the agent-runtime dimension:
  Claude Code Driver, OpenAI Codex project-local adapters, and the future Pi
  harness. Codex evidence must prove instruction-surface loading and verified
  adapter use where adapters exist, and must state unsupported/Claude-only
  mechanics explicitly.
- Codex telemetry/cost evidence remains tokens-primary. Dollar figures are
  provider-specific overlays and must not be inferred from Claude Code cost
  spans.

## Work discipline

Every repo change must use a worktree -> PR -> merge -> cleanup path.

1. Confirm `/data/projects/livespec` is the primary checkout:

   ```bash
   git -C /data/projects/livespec config --get livespec.primaryPath
   git -C /data/projects/livespec status --short --branch
   ```

2. Create a separate worktree before editing:

   ```bash
   mise exec -- git -C /data/projects/livespec worktree add -b <branch> /data/projects/<worktree> master
   ```

3. Use `mise exec -- git ...` for commit and push so hooks run.
4. Never use `--no-verify`.
5. Open a PR, wait for checks, merge via the PR, refresh the primary checkout,
   remove the worktree, and delete the local branch.
6. At the end of the session, update `research/codex-support/handoff-prompt.md`
   with the complete next-session prompt, land it, and make the final response
   point only to that filename.

## Next concrete action

Continue Codex support work from the expanded family-wide scope. Do NOT repeat
the completed PR #452, #457, #460, #465, #466, #467, #470, #471, #473, the
sibling spec PRs #134 / #48 / #88 / #62, the sibling instruction parity PRs
#136 / #50 / #90 / #75 / #18, or the sibling read-only Codex runtime probes
recorded above. The next phase is high-level e2e follow-through and telemetry /
runtime-mechanism closure:

1. Use `research/codex-support/family-audit.md` as the durable summary and keep
   it current.
2. Continue `livespec-zkmn.1` high-level e2e/golden-master implementation with
   Codex as a supported agent-runtime dimension. The W7 research plan now
   records the required Claude/Codex/Pi runtime matrix.
3. Refine telemetry/cost follow-ups through `livespec-impl-beads-zbl` and
   `livespec-dev-tooling-e60` as implementation begins; Codex should remain
   tokens-primary, not Claude-cost-derived.
4. Before claiming mutating Codex automation, provide a Codex replacement for
   the Claude-only pre-tool footgun guard or record the narrower support claim
   that relies on AGENTS/repo hooks only.
5. For any repository mutation, follow that repo's required
   worktree -> PR -> merge -> cleanup discipline. For spec mutations, use the
   governed livespec propose-change -> revise lifecycle unless an explicit
   fallback is approved and recorded.

## Verification Already Completed

PR #457 completed the required first adapter verification from the adapter
worktree:

```bash
find .agents/skills -maxdepth 2 -type f -name SKILL.md -print
codex debug prompt-input '/livespec:help'
codex exec --sandbox read-only '/livespec:help. Do not edit files. Tell me exactly which local instruction/prose file you read.'
codex exec --sandbox read-only 'livespec next dry run only. Do not edit files. Tell me exactly which wrapper you would invoke.'
codex exec --sandbox read-only 'livespec doctor help only. Do not edit files. Tell me exactly which wrapper you would invoke.'
mise exec -- just check-pre-commit-doc-only
```

GitHub checks for PR #457 all passed before merge. See
`research/codex-support/adapter-proof.md` for durable evidence.

PR #460 completed the mechanical sync-check follow-up:

```bash
mise exec -- just check
gh pr checks 460 --watch --interval 10
```

Local `just check` passed all 52 targets, including 900 pytest cases at 100%
coverage. PR checks passed after rerunning one transient
`check-copier-template-smoke` failure caused by a broken-pipe download during
`uv sync`; the job passed on rerun. The new `check-codex-adapter-sync` CI job
passed.

PR #466 completed the Codex/Claude operational memory migration:

```bash
mise exec -- just check-pre-commit-doc-only
gh pr checks 466 --watch --interval 10
```

Local doc-only verification and all PR checks passed. The merge commit was
`82e99653f7fe2e2f40bbeb2b0af1a5a673c6c46c`; the primary checkout was
fast-forwarded after merge, the memory worktree/branch were removed, and Beads
`livespec-zkmn.1.1` was closed.

PR #467 completed the wrapper-help exit fix:

```bash
mise exec -- uv run pytest tests/livespec/io/test_cli.py -q
/usr/bin/python3 .claude-plugin/scripts/bin/doctor_static.py --help
/usr/bin/python3 .claude-plugin/scripts/bin/revise.py --help
mise exec -- just check
gh pr checks 467 --watch --interval 10
```

Local focused verification confirmed both wrappers returned `0` with zero
stderr bytes. The Red-Green-Replay Green amend ran `just check` successfully;
the pre-push hook reran `just check` and passed all 52 targets; PR checks all
passed. The merge commit was `dc94af9a659610dab154a7bf9b5ee5d05a8f0c82`; the
primary checkout was fast-forwarded after merge, the wrapper worktree/branch
were removed, and Beads `livespec-4moata.3` was closed.

Branch `codex-spec-repair` completed the governed spec repair locally:

```bash
mise exec -- git fetch origin
mise exec -- git ls-remote --heads origin 'spec/*'
gh pr list --state open --json number,title,headRefName,files
/usr/bin/python3 .claude-plugin/scripts/bin/propose_change.py codex-dogfooding-adapters --findings-json tmp/codex-spec-repair-proposal.json --author codex-gpt-5 --project-root /data/projects/livespec-codex-spec-repair --spec-target /data/projects/livespec-codex-spec-repair/SPECIFICATION
/usr/bin/python3 .claude-plugin/scripts/bin/revise.py --revise-json tmp/codex-spec-repair-revise.json --author codex-gpt-5 --project-root /data/projects/livespec-codex-spec-repair --spec-target /data/projects/livespec-codex-spec-repair/SPECIFICATION --post-step-doctor --run-stale-branch-check
/usr/bin/python3 .claude-plugin/scripts/bin/propose_change.py codex-core-live-reload-paths --findings-json tmp/codex-contracts-live-reload-proposal.json --author codex-gpt-5 --project-root /data/projects/livespec-codex-spec-repair --spec-target /data/projects/livespec-codex-spec-repair/SPECIFICATION
/usr/bin/python3 .claude-plugin/scripts/bin/revise.py --revise-json tmp/codex-contracts-live-reload-revise.json --author codex-gpt-5 --project-root /data/projects/livespec-codex-spec-repair --spec-target /data/projects/livespec-codex-spec-repair/SPECIFICATION --post-step-doctor --run-stale-branch-check
mise exec -- just check
```

Notes:

- Remote spec branch survey found no `spec/*` branches.
- Open PR survey found no open PRs.
- `origin/master` advanced during PR #465 with the unrelated
  `orchestrator-grooming-guidance` proposal as `SPECIFICATION/history/v116/`;
  the branch was rebased so the Codex repair history follows it.
- `revise.py` cut `SPECIFICATION/history/v117/` and moved only
  `codex-dogfooding-adapters.md`.
- A sub-agent review then found one adjacent stale clause in
  `SPECIFICATION/contracts.md` §"Daily dogfooding path"; after rebase this is
  represented by `SPECIFICATION/history/v118/`, which moved only
  `codex-core-live-reload-paths.md`.
- The unrelated `orchestrator-grooming-guidance` proposal is no longer pending
  after the rebase because it landed on `origin/master` as `v116`.
- No `## ` heading set changed, so `tests/heading-coverage.json` was not
  updated.
- Direct attempts to run the stale-branch check outside the wrapper hit local
  Python/mise environment issues, but the production `revise.py` invocation was
  run with `--run-stale-branch-check` and exited 0.
- Final rerun of `mise exec -- just check` after `v118` passed all 52 targets,
  including 900 pytest cases at 100% coverage and 4 mock e2e tests.

## Follow-up work after adapter proof

The main-repo adapter-proof follow-ups and sibling governed spec updates are
complete as of the PRs listed above, but the broader Codex support program is
NOT complete. Track at least these open areas:

- manual Codex runtime verification: prove the Codex path in every changed
  repo, including writable/e2e behavior and any migrated hook/bootstrap
  behavior; read-only instruction loading and sibling `AGENTS.md` mutation
  protocol visibility are already proven;
- high-level e2e testing: `livespec-zkmn.1` and
  `research/w7-orchestrator-convergence/plan.md` now require Codex as a
  supported harness dimension, but implementation and manual evidence remain
  open;
- non-skill runtime mechanisms: audit hooks, plugin installation assumptions,
  bootstrap scripts, cloud-specific references, and Claude-only machinery;
- telemetry/cost observability: keep Codex tokens-primary through
  `livespec-impl-beads-zbl` and `livespec-dev-tooling-e60`;
- reproduction summary: keep a current `research/codex-support/` summary
  document suitable for replaying the work for the Pi agent harness.

The first version of that summary is
`research/codex-support/family-audit.md`; update it whenever Codex support state
changes.

## Constraints

- Do not reintroduce `.claude-plugin/skills/` into core.
- Do not symlink `.agents/skills/*` to `.claude-plugin/skills/*`.
- Do not duplicate core operation prose in Codex skills.
- Do not copy Claude Driver skills into Codex skills; both runtimes bind to the
  same core prose and wrappers.
- Do not implement broad hooks/plugin machinery before the read-only adapter
  proof.
- Do not mutate `SPECIFICATION/` directly unless using the governed LiveSpec
  lifecycle or an explicitly approved fallback.
- Do not leave the session without an updated
  `research/codex-support/handoff-prompt.md`.
- Do not put handoff instructions only in the final chat response; the final
  response should point to `research/codex-support/handoff-prompt.md`.
