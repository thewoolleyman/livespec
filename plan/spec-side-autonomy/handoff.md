# spec-side-autonomy — handoff

The track is at a clean stopping point as of 2026-08-07. Increments 1, 2, and 3
are all complete and ratified. This session owns no remaining feature worktree,
branch, PR, subprocess, or ledger mutation. Do not recreate or redispatch any
closed slice.

Before any future ledger operation, read `AGENTS.md`,
`.ai/agent-disciplines.md`, and `.ai/beads-gaps-workarounds.md`, then use the
installed orchestrator skill for the target tenant. Batch ledger reads under the
configured credential wrapper and never print secret values.

**Ledger anchor:** epic `livespec-jvdvx4`

## Landed state

### Increment 1 — complete

Core slices A/B/C/D merged as PRs #1939, #1942, #1949, and #1944. Do not
redispatch them.

### Increment 2 — complete

- Ratified with decision `modify` as spec **v193**. PR #1978 rebase-merged at
  `98300b9f3bbe6a60650a74a602b6ece137d68279` after a separate read-only Fable
  review returned literal `NO BLOCKERS`.
- Slice A (control surface, `livespec-jvdvx4.3`, closed): `revise_decision_mode`
  registry key (`manual|delegated|consensus`, safe default `manual`) shipped via
  PR #1980, rebase-merge `2ffebf1b0744e07a5c385c5be25b475bb1dfbd75`.
- Slice B (resolver/floors/predicate/journal, `livespec-jvdvx4.4`, closed):
  shipped via PR #1987, rebase-merge `3a024ad71abe137112c916850d6eb41904f63f68`.

### Increment 3 — complete

Both halves ratified and the implementation shipped:

| Piece | Where | Evidence |
|---|---|---|
| Doctrine, core | `livespec` **v196** | PR #2033, merge `0f06129ff9b4f6f0d347733e5e282b8b439799ca` |
| Doctrine, paired | `livespec-orchestrator-beads-fabro` **v058** | PR #1307, merge `a269345c4aac9d235da389347dfb4bc13487c496` |
| `drift_acceptance_mode` implementation | `livespec` | PR #2058, merge `b6e8d4d81e5d587b4d31f3ce31d87ebe64d47467` |

- All three merge SHAs are confirmed ancestors of their repo's `origin/master`.
- `drift_acceptance_mode` is live in
  `.claude-plugin/scripts/livespec/spec_governance/` (config, schema, editing,
  effective, and the api-configurable-keys manifest).
- It ships as enum `[human, consensus]`, safe default `human`, global-only
  (`per_proposal_override: null`), with `delegated` REFUSED at exit 2.
- Ledger `livespec-jvdvx4.5` is CLOSED. So are `.1`, `.3`, `.4`, and the four
  Increment-1 slices.
- **livespec `SPECIFICATION/history/` tip is v199, not v196** — three later
  revisions landed from other lanes. Do not report v196 as the current tip;
  v196 is only the doctrine-ratification version for this track.
- `livespec-orchestrator-beads-fabro` history tip is v058.

## Open items on this epic

- **`livespec-jvdvx4.2`** — status `backlog`. Legs 1, 2a, 2b are CLOSED. Leg 2,
  the multi-repo `spec_governance` backfill, is all that remains, and it is
  **NOT YET AUTHORIZED to start**. Do not begin it, file children for it, or
  dispatch anything until a fresh maintainer brief authorizes it.

  Correction to carry into that future work: the previously recorded backfill
  target set of ten repos was wrong — it is **twelve repos**. `openbrain` and
  `homelab` were omitted on the stated grounds that they "carry no
  `.livespec.jsonc`"; both do carry the file (`openbrain` since 2026-04-23,
  `homelab` since 2026-07-18), but their default branch is `main`, not
  `master`, so a sweep reading `git show origin/master:.livespec.jsonc` failed
  with `invalid object name 'origin/master'` — indistinguishable from "file
  absent" to a check that only asks whether the read succeeded. When this leg
  starts, re-derive the target set at execution time, resolving each repo's
  own default branch, and read each repo's credential wrapper from its OWN
  committed `.livespec.jsonc` (they differ: `/usr/local/bin/with-livespec-env.sh`
  for the nine fleet repos, `with-dolt-server-env.sh`, `./with-resume-env.sh`,
  `with-openbrain-env.sh`, `with-homelab-aws.sh`).

- `livespec-bhammf` — `blocked`, needs-human. The relocated `spec_pr_merge`
  redesign. Not this thread's unfinished business; record it as-is.

## Next action — wait for a fresh maintainer brief

There is no authorized implementation action remaining on this epic. On
restart, report the clean completed state above and wait for a fresh
maintainer brief. Do not mutate the epic, file or dispatch another slice, or
infer authorization to begin `livespec-jvdvx4.2` leg 2.

## Standing constraints

- All tracked edits use dedicated worktrees; never edit or commit tracked files
  directly in `/data/projects/livespec`.
- Never pass `--no-verify`; use worktree → PR → rebase-merge → primary refresh
  → cleanup and halt on hook failure.
- Never touch another session's worktree, branch, sandbox, ledger item, or
  admission label. Never kill the acting overseer daemon.
- The detailed historical milestone trail remains
  `tmp/overseer/spec-side-autonomy/worker-status.log`.
