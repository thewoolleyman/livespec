# spec-side-autonomy — handoff

Resume the Increment 2 doctrine amendment. Read
`/data/projects/livespec/tmp/overseer/spec-side-autonomy/brief-13-resume-increment-2.md`
and then
`/data/projects/livespec/tmp/overseer/spec-side-autonomy/brief-14-worktree-pack.md`
in full before acting. This file is the authoritative resume state as of
2026-08-04T01:43Z; do not infer state from an old transcript.

**Ledger anchor:** livespec epic `livespec-jvdvx4`.

## Current state

- Increment 1 is complete. Slices A/B/D merged as PRs #1939, #1942,
  and #1944. Slice C was supervisor-owned and merged as PR #1949. Never
  touch or redispatch Slice C.
- Increment 2's proposal-only PR #1948 is merged. The only pending
  proposal is expected to be
  `SPECIFICATION/proposed_changes/spec-governance-revise-decision-mode.md`,
  but re-enumerate the live queue immediately before revise.
- Handoff PR #1961 was rebased after the compatibility repair, passed the
  complete fresh forge matrix, and rebase-merged as `11bd1b72`. The primary
  checkout was fast-forwarded to that SHA and its completed handoff worktree
  and branch were removed. The pre-existing dirty
  `plan/spec-side-autonomy/supervisor-handoff.md` remains untouched.
- The live spec remains v192. Railway landed as v191. Any eventual Increment
  2 ratification is v193 only if no newer ratification lands first; fetch and
  re-enumerate immediately before revise.
- The ratification worktree is
  `/home/ubuntu/.worktrees/livespec/spec/ratify-spec-governance-increment-2`
  on branch `spec/ratify-spec-governance-increment-2`, refreshed to current
  master `11bd1b72`.
  It deliberately has four uncommitted candidate files and nothing else:
  `SPECIFICATION/spec.md`, `contracts.md`, `constraints.md`, and
  `scenarios.md` (71 insertions, 8 deletions).
- The corrected candidate fixes both doctrine-text blockers: it adds the
  durable revision-record audit clause; makes the overview policy-governed
  with human default/floors; states delegated/manual-spawn interaction and
  revise prose ownership; covers delegated plus consensus override; and uses
  the exact `revise_decision` journal token. H2 headings are unchanged and
  the Increment 3 drift-doctrine sentence remains byte-identical.
- The ratification worktree's ignored worktree pack is currently absent.
  Before any hook-backed validation there, run
  `mise exec -- just install-worktree-pack`, then immediately run
  `mise exec -- git checkout -- .livespec.jsonc`; confirm the tracked config
  is clean. The old candidate digest `5792ffc...` is stale and must not be used
  as evidence.

## Active blocker — digest repair still precedes review

The producer/core compatibility outage is over. livespec-dev-tooling PR #1212
and livespec core parser PR #1963 are merged, and the cross-repo gate is green.
Do NOT redo either change and do not touch the dev-tooling fallout items.

The remaining ratification blocker is the original v190 digest mismatch. On
fresh core master, `.claude-plugin/scripts/livespec/commands/_revise_ratification.py`
still hashes decimal-ASCII length framing, omits the
raw proposal bytes, and does not sort paths by unsigned UTF-8 bytes; that cannot
validate the ratified `LP(P)` + uint64-BE + bytewise-path contract in candidate
`contracts.md`. The doctrine candidate must not weaken that contract.

Use the existing repair child `livespec-jvdvx4.1` under epic
`livespec-jvdvx4`; its dispatch-sized description is preserved at
`tmp/overseer/spec-side-autonomy/digest-repair-description.md`. Two historical
factory runs failed before Red commit and delivered no branch/PR/merge:
`01KZ4BMPE617AKNYHSNFA6BB9G` and `01KZ4CC86BBZZWYAMJ8BG8ZMAD`.
Re-read the current ledger item through the sanctioned driver before acting;
do not duplicate the item or assume its old stale claim still has the same
state. Resolve/requeue only through the documented orchestrator surface, then
dispatch that same item exactly once now that the compatibility gate is green.

## Resume sequence

1. Read the installed `livespec-orchestrator-beads-fabro:drive` skill from the
   current plugin catalog and `.ai/beads-gaps-workarounds.md` completely. The
   prior session's guessed versioned skill path was absent; resolve the current
   catalog path rather than assuming `0.49.10` is materialized locally.
2. Batch-read the current ledger state for `livespec-jvdvx4.1`, repair any
   terminal stale claim only through the sanctioned surface, and dispatch that
   same item exactly once. Do not create a replacement item and do not rerun
   core parser PR #1963.
3. Wait for the digest repair to merge. Fetch livespec master, then refresh the
   owned ratification worktree onto the new master while preserving exactly the
   four uncommitted candidate files. Recheck that only those four spec files
   differ and that the Increment-3 drift-doctrine sentence remains byte-exact.
4. Install the ratification worktree's ignored worktree pack and revert the
   installer-only `.livespec.jsonc` edit. Run
   `mise exec -- just check-pre-commit-doc-only`, recompute the canonical proposal+resulting-files
   digest from the freshly fetched bytes, and update the existing read-only
   review brief at
   `tmp/overseer/spec-side-autonomy/reviews/revise-decision-mode-v192-corrected.md`
   for the new base and exact bytes.
5. Spawn a fresh, separate Fable-model READ-ONLY adversarial reviewer. It must
   independently verify the three prior blockers plus every criterion in the
   review brief and end with literal `VERDICT: NO BLOCKERS`. Any blocker routes
   to the maintainer with a recommended fix; never self-waive it.
6. Immediately before revise, fetch again and re-derive every full-file
   `resulting_files[]` entry from those fresh bytes. Re-enumerate every proposal
   queue, ensure only `spec-governance-revise-decision-mode.md` is consumed,
   and run the required stale-branch precondition. Drive `livespec:revise` with
   matching evidence and `--post-step-doctor`; do not touch the Increment-3
   drift-doctrine sentence. Commit, push, open the ratification PR, wait for
   checks, rebase-merge, refresh master, and clean the worktree/branch.
7. Only after core ratifies, file—but do not implement or dispatch—the
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
