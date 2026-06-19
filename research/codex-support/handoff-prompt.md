# Codex support handoff prompt

You are starting a new session in `/data/projects/livespec`.

Goal: make livespec usable from OpenAI Codex as a maintainer dogfooding
surface, starting with the minimum project-skill/bootstrap path.

## Start here

Read these files first:

1. `AGENTS.md`
2. `research/codex-support/audit.md`
3. `research/codex-support/plan.md`

The audit and plan landed on `master` via PR #452:

- PR: `https://github.com/thewoolleyman/livespec/pull/452`
- Merge commit: `a819f5107e9a4f04cab9084247f4c392e6d9aebb`
- Date: 2026-06-19

Do not redo the initial audit unless new evidence contradicts it. Continue from
the plan.

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
- This repo currently has no committed `.agents/` or `.codex/` project tree.
- Codex CLI 0.141.0 does load project-local `.agents/skills/*/SKILL.md` files
  when each skill has valid YAML frontmatter with `name` and `description`.
- Codex has no installed/configured livespec plugin marketplace entry; only the
  `openai-curated` marketplace is configured.
- The proven near-term path is project-local `.agents/skills` adapters that read
  core prose and invoke core wrappers. Do not claim Codex marketplace support.
- The Claude/Codex DRY boundary is core prose plus wrapper CLIs, not copied
  skill bodies. Claude Driver `SKILL.md` files and Codex project `SKILL.md`
  files are both thin runtime adapters over the same core files.

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

Implement the minimum read-only Codex adapter proof from
`research/codex-support/plan.md`.

Recommended first PR:

```text
.agents/
  skills/
    livespec-help/
      SKILL.md
    livespec-next/
      SKILL.md
    livespec-doctor/
      SKILL.md
```

Adapter rules:

- Each `SKILL.md` must have Codex YAML frontmatter.
- Skill names should be `livespec-help`, `livespec-next`, and
  `livespec-doctor`, not bare `help`, `next`, or `doctor`.
- Do not copy Claude Driver `SKILL.md` bodies. Do not create a new shared
  cross-runtime skill body. The shared abstraction is already
  `.claude-plugin/prose/<name>.md` plus `.claude-plugin/scripts/bin/<name>.py`.
- The body should be a thin Codex runtime adapter:
  - read the matching `.claude-plugin/prose/<name>.md` completely;
  - follow that prose;
  - invoke the matching wrapper under `.claude-plugin/scripts/bin/` when the
    prose calls for a CLI;
  - do not copy or restate operation behavior.

Suggested mapping:

| Codex skill | Core prose | Wrapper |
|---|---|---|
| `livespec-help` | `.claude-plugin/prose/help.md` | none |
| `livespec-next` | `.claude-plugin/prose/next.md` | `.claude-plugin/scripts/bin/next.py` |
| `livespec-doctor` | `.claude-plugin/prose/doctor.md` | `.claude-plugin/scripts/bin/doctor_static.py` |

Keep mutating operations (`seed`, `propose-change`, `critique`, `revise`,
`prune-history`) out of the first adapter PR.

## Required verification for adapter PR

Run from the adapter worktree.

```bash
find .agents/skills -maxdepth 2 -type f -name SKILL.md -print
codex debug prompt-input '/livespec:help'
codex exec --sandbox read-only '/livespec:help. Do not edit files. Tell me exactly which local instruction/prose file you read.'
codex exec --sandbox read-only 'livespec next dry run only. Do not edit files. Tell me exactly which wrapper you would invoke.'
codex exec --sandbox read-only 'livespec doctor help only. Do not edit files. Tell me exactly which wrapper you would invoke.'
mise exec -- just check-pre-commit-doc-only
```

Expected:

- `codex debug prompt-input` lists the project skills from `.agents/skills`.
- The help probe reads both `.agents/skills/livespec-help/SKILL.md` and
  `.claude-plugin/prose/help.md`.
- The next probe identifies `.claude-plugin/scripts/bin/next.py` with explicit
  `--project-root`, `--spec-target`, `--limit 5`, and `--offset 0`.
- The doctor probe identifies `.claude-plugin/scripts/bin/doctor_static.py`,
  preferably with `--help` for the first non-mutating proof.

Record important command outputs in `research/codex-support/` if they add new
evidence beyond `audit.md`.

## Required DRY follow-up

After the first read-only adapters are proven, add mechanical sync checks rather
than relying on humans to keep Claude and Codex skill text aligned:

- every Codex adapter references an existing core prose file;
- every wrapper-backed Codex adapter references the expected core wrapper;
- Codex adapters do not contain copied core `## Steps`, failure-handling tables,
  or output-schema narration;
- verification probes show Codex reads the adapter and then the core prose.

## Follow-up work after adapter proof

1. File or attach Beads work-items for:
   - stale Codex dogfooding spec repair;
   - Codex read-only adapter proof;
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
