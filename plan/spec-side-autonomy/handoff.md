# spec-side-autonomy — handoff

Resume the Increment 2 doctrine amendment. Read
`/data/projects/livespec/tmp/overseer/spec-side-autonomy/brief-09-increment-2.md`
in full before acting. This file is the authoritative resume state as of
2026-08-03; do not infer state from an old transcript.

**Ledger anchor:** livespec epic `livespec-jvdvx4`.

## Current state

- Increment 1 is complete. Slices A/B/D merged as PRs #1939, #1942,
  and #1944. Slice C was supervisor-owned and merged as PR #1949. Never
  touch or redispatch Slice C.
- Increment 2's proposal-only PR #1948 is merged. The only pending
  proposal is expected to be
  `SPECIFICATION/proposed_changes/spec-governance-revise-decision-mode.md`,
  but re-enumerate the live queue immediately before revise.
- The livespec primary checkout is clean at v192 commit `73cf2dbc`
  (`chore(spec): ratify self-hosted CI runner host requirements as v192`).
  Railway landed as v191. Any eventual Increment 2 ratification is v193
  only if no newer ratification lands first.
- The ratification worktree is
  `/home/ubuntu/.worktrees/livespec/spec/ratify-spec-governance-increment-2`
  on branch `spec/ratify-spec-governance-increment-2`, based on v192.
  It deliberately has four uncommitted candidate files and nothing else:
  `SPECIFICATION/spec.md`, `contracts.md`, `constraints.md`, and
  `scenarios.md` (71 insertions, 8 deletions).
- The corrected candidate fixes all earlier content blockers: it adds the
  durable revision-record audit clause; makes the overview policy-governed
  with human default/floors; states delegated/manual-spawn interaction and
  revise prose ownership; covers delegated plus consensus override; and uses
  the exact `revise_decision` journal token. H2 headings are unchanged and
  the Increment 3 drift-doctrine sentence remains byte-identical.
- The doc-only gate passed before the final tiny journal-token wording edit.
  Rerun it before review. The old candidate digest
  `5792ffc...` is stale and must not be used as evidence.

## Active blocker — do not dispatch again yet

The first independent exact-byte review found that the current revise digest
implementation violates the ratified v190 LP(P)/uint64-BE/bytewise-path
contract. The existing repair child is `livespec-jvdvx4.1` under epic
`livespec-jvdvx4`. Its dispatch-sized description (1483 bytes) is preserved at
`tmp/overseer/spec-side-autonomy/digest-repair-description.md`.

Two factory runs failed before Red commit, with no branch, PR, or merge:

- `01KZ4BMPE617AKNYHSNFA6BB9G`
- `01KZ4CC86BBZZWYAMJ8BG8ZMAD`

The item remains `active`, assignee `fabro`, after terminal failure. Do not
launch a third run or race the stale claim.

The exact failure, reproduced against fresh origin/master sibling clones, is
`doctor-wiring-completeness-cross-repo: livespec-dev-tooling→:no-check-recipe`.
The breaking change is livespec-dev-tooling PR #1179 / commit
`20a43f85cad2eb6fc6ad1d2b04f506a31f82e305`, which replaced the directly
enumerable `justfile` `check:` aggregate with `scripts/just/check.sh` before
core's ratified checker could consume that shape. The host checkout looked
green only because `/data/projects/livespec-dev-tooling` was stale; a fresh
origin clone fails.

Per `.ai/ci-gate-discipline.md`, do not add a lever, bypass, or warning
demotion. The recommended world-gate repair is a full server-side revert of
livespec-dev-tooling PR #1179, followed by a separately ordered re-land once
core supports the new shape. Supervisor authorization for that cross-repo
revert was requested but had not arrived when this session wound down. Obtain
or consume an explicit maintainer decision before mutating that repo.

## Resume sequence

1. Re-read `.ai/ci-gate-discipline.md`. If the maintainer authorizes the
   recommendation, open and merge a full revert PR for livespec-dev-tooling
   #1179 and record/file the correctly ordered re-land work. Do not broaden
   the revert and do not bypass a gate.
2. Verify a fresh-origin cross-repo check is green. Then repair the stale
   ledger claim for `livespec-jvdvx4.1` using the sanctioned intake/drive
   surfaces and dispatch that same item exactly once. Do not duplicate it.
3. Wait for the digest repair to merge. Fetch livespec master, then update the
   ratification worktree onto the new master while preserving the four
   uncommitted candidate files. Recheck that no stale full-file splice reverted
   v191/v192 and that only those four spec files differ.
4. Run `mise exec -- just check-pre-commit-doc-only`, recompute the exact
   candidate digest, and launch a fresh independent Fable exact-byte review
   using
   `tmp/overseer/spec-side-autonomy/reviews/revise-decision-mode-v192-corrected.md`
   updated for the new base/digest. Ratification requires `VERDICT: NO BLOCKERS`.
5. Immediately before revise, re-enumerate `proposed_changes/`, ensure the
   operation consumes only this thread's proposal, and perform the stale-branch
   check required by Brief 09. Run revise from the fresh master lineage; never
   use an old full-file payload. Commit, push, open the ratification PR, wait
   for checks, rebase-merge, refresh master, and clean its worktree/branch.
6. Only after core ratifies, file—but do not implement or dispatch—the
   orchestrator child that retires the needs-attention revise lane when the
   shared predicate is false. Its 1447-byte draft and notes are at
   `tmp/overseer/spec-side-autonomy/increment-2-orchestrator-slice-description.md`
   and `increment-2-orchestrator-slice-notes.md`; replace version/PR
   placeholders with final values and parent it to `livespec-jvdvx4`.

## Standing constraints

- Increment 2 is doctrine-sensitive: every Brief 09 clause is load-bearing.
- Never pass `--no-verify`; use the worktree → PR → rebase-merge → cleanup
  protocol. Do not commit at a primary checkout.
- Do not mutate unrelated ledger items, admission labels, branches, or
  supervisor-owned work. Do not kill the livespec-overseer tmux daemon.
- The detailed milestone trail is
  `tmp/overseer/spec-side-autonomy/worker-status.log`.
