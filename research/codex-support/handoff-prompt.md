# Codex support handoff prompt

You are starting a new session in `/data/projects/livespec`.

Goal: make livespec usable from OpenAI Codex as a maintainer dogfooding
surface, starting with the minimum project-skill/bootstrap path.

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

The Codex/Claude operational memory migration is now in progress:

- Worktree: `/data/projects/livespec-codex-memory-instructions`
- Branch: `codex-memory-instructions`
- Beads work-item: `livespec-zkmn.1.1`
- Intended scope: migrate only parity-critical operational rules into
  committed instructions: worktree discipline, `mise exec --` git operations,
  no `--no-verify`, end-on-master cleanup, Beads access, no primary-checkout
  edits, and no orphaned worktrees.
- Do not dump all Claude memory into `AGENTS.md`; route durable operational
  rules by audience and authority.

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
- The doctor probe also exposed a pre-existing wrapper-help behavior:
  `/usr/bin/python3 .claude-plugin/scripts/bin/doctor_static.py --help`
  printed argparse help but exited `2`. This did not block the read-only
  adapter proof, but it is worth filing or folding into follow-up work.
- PR #460 added `dev-tooling/checks/codex_adapter_sync.py` and
  `tests/dev-tooling/checks/test_codex_adapter_sync.py`, wired
  `check-codex-adapter-sync` into `just check`, `check-pre-commit-doc-only`,
  and the CI check-metadata matrix, and verified the current three adapters
  remain thin over core prose/wrappers.
- Beads follow-ups filed on 2026-06-19:
  - `livespec-4moata.2` — Codex dogfooding spec repair.
  - `livespec-4moata.3` — `doctor_static.py --help` prints help while exiting
    `2`.
  - `livespec-zkmn.1.1` — migrate parity-critical Claude operational memory
    into committed instructions.

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

Finish `livespec-zkmn.1.1` in branch `codex-memory-instructions`:

1. Keep the `AGENTS.md` update narrowly focused on repo-mutation discipline.
2. Keep the handoff update current with PR #465's landed state and this
   branch's validation/PR status.
3. Run `mise exec -- just check-pre-commit-doc-only` for the doc-only change.
4. Commit with `mise exec -- git ...`, push, open a PR, wait for checks, merge
   through the PR, refresh `/data/projects/livespec`, remove
   `/data/projects/livespec-codex-memory-instructions`, delete local branch
   `codex-memory-instructions`, and close Beads item `livespec-zkmn.1.1`.
5. After that, continue to Beads item `livespec-4moata.3`.

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

1. Finish migrating only parity-critical Claude memory into committed
   instructions (Beads `livespec-zkmn.1.1`).
2. Fix the wrapper help behavior (Beads `livespec-4moata.3`):
   `/usr/bin/python3 .claude-plugin/scripts/bin/doctor_static.py --help` prints
   argparse help but exits `2`; `revise.py --help` showed the same exit-2
   pattern during the spec-repair session. Treat this as likely shared wrapper
   supervisor behavior.

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
