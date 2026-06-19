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
Continue with the governed spec repair and work-item filing below.

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
- The old Codex spec text is stale because it says `.agents/skills/*` should
  symlink to `.claude-plugin/skills/*`.
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

Repair the stale Codex dogfooding specification and file/attach the remaining
work-items. The mechanical sync check is now landed, so the next change should
use the governed livespec lifecycle for spec text, not direct edits to
`SPECIFICATION/`.

Recommended next PR sequence:

1. File or attach Beads work-items for the remaining follow-ups listed below.
2. Use propose-change -> revise to repair
   `SPECIFICATION/non-functional-requirements.md` so it no longer says Codex
   adapters symlink to `.claude-plugin/skills/*`.
3. Keep Codex support scoped to the proven project-local `.agents/skills`
   adapter path over core prose and wrappers. Codex marketplace support remains
   explicitly unclaimed.

Keep mutating operations (`seed`, `propose-change`, `critique`, `revise`,
`prune-history`) out of Codex adapters until the stale spec text is repaired.

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

## Follow-up work after adapter proof

1. File or attach Beads work-items for:
   - stale Codex dogfooding spec repair;
   - `doctor_static.py --help` printing help while exiting `2`;
   - Claude-memory-to-committed-instructions migration.
2. Repair `SPECIFICATION/non-functional-requirements.md` through the governed
   propose-change -> revise path:
   - remove `.claude-plugin/skills/*` symlink requirements;
   - define Codex adapters over core prose and wrappers;
   - keep Codex marketplace support explicitly unclaimed until proven.
3. Migrate only parity-critical Claude memory into committed instructions:
   worktree discipline, `mise exec --` git operations, no `--no-verify`,
   end-on-main cleanup, Beads access, no primary-checkout edits, and no orphaned
   worktrees.

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
