# spec-side-autonomy — handoff

Resume the Increment 2 doctrine amendment from the independent-review blocker
below. This is the authoritative state as of 2026-08-04T04:07Z. Do not resume
from an earlier brief or transcript. Read `AGENTS.md` §"Independent Fable review
before every ratification", `.ai/spec-proposal-review.md`, and
`/data/projects/livespec/tmp/overseer/spec-side-autonomy/brief-17-review-and-revise.md`
before acting.

**Ledger anchor:** livespec epic `livespec-jvdvx4`.

## Current state

- Increment 1 is complete. Core slices A/B/C/D merged as PRs #1939, #1942,
  #1949, and #1944. Do not redispatch them.
- Increment 2's proposal-only PR #1948 is merged. At the last fresh enumeration,
  the only in-flight proposal was
  `SPECIFICATION/proposed_changes/spec-governance-revise-decision-mode.md`.
  Re-enumerate every spec-target queue immediately before revise.
- The hard digest predecessor `livespec-jvdvx4.1` is CLOSED. Its repair passed
  Red-Green-Replay and the full local/forge matrices, then PR #1974
  rebase-merged onto livespec master as
  `066a29fbb204b4be2e2e3ab56e73053ec52bb646`. Do not redo it.
- The owned ratification worktree is
  `/home/ubuntu/.worktrees/livespec/spec/ratify-spec-governance-increment-2`
  on branch `spec/ratify-spec-governance-increment-2`. Its HEAD and derivation
  base are exact fetched `origin/master`
  `6dab6033a2ea428409049b1d3daf19b18841033d`.
- Exactly four candidate files are deliberately uncommitted there:
  `SPECIFICATION/spec.md`, `contracts.md`, `constraints.md`, and `scenarios.md`.
  They were discarded and re-derived from the fresh base before review. The
  diff is 71 insertions / 8 deletions; every H2 set is unchanged; the paragraph
  beginning `**Drift's human gate is load-bearing doctrine.**` is byte-identical
  to base; no Increment-3 doctrine was touched.
- The exact pre-review digest was
  `39198f3099d54ff20541251626151388c49a128c1b1808fcae6ff5721dfe7a5b`,
  computed as uint64-BE LP(raw proposal bytes) first, then the four full-file
  entries sorted by unsigned UTF-8 path bytes. It is evidence for the BLOCKERS
  review only and MUST NOT be reused after any candidate edit or re-derivation.
- No revise, ratification version, candidate commit, candidate push, or
  ratification PR has occurred. The live spec remained v192 at the last check;
  derive the next version from fresh history rather than assuming v193.

## Active blocker — routed, never self-waived

A separate read-only `fable` model was spawned with the exact candidate bytes.
It independently reproduced the digest, verified that the three former blockers
are fixed, and returned literal `VERDICT: BLOCKERS`.

The sole blocker is mechanical. Two new design-record citations use the
section-reference form against a same-repo `plan/` file:

- candidate `SPECIFICATION/spec.md`, the `Delegated revise is stronger than
  manual revise` paragraph; and
- candidate `SPECIFICATION/contracts.md`, the `decision_policy` wire-surface
  paragraph.

Both append
`§"Proposed design — a core-owned \`spec_governance\` lever family"` to
`plan/spec-side-autonomy/research/brainstorm.md`. The ratified
`doctor-no-cross-spec-reference` check resolves section citations only against
same-tree spec headings or allowlisted sibling-spec headings. Fable ran
doctor-static on the exact tree: it failed at `contracts.md` and independently
confirmed the `spec.md` citation is the same second violation. These bytes are
therefore not cleanly ratifiable.

**Recommended fix, awaiting supervisor authorization:** retain the bare
repo-plus-path citations in both sentences and remove only the two `§"…"`
suffixes. Do not add an external-reference allowlist entry: that registry is for
sibling `SPECIFICATION/` headings, not a same-repo plan heading. After any fix,
the old digest and review are stale; recompute and obtain a fresh independent
Fable review. Brief 17 says a blocker routes to the supervisor with its
recommended fix rather than being silently fixed and re-reviewed, so do not
apply it until the supervisor explicitly directs continuation.

## What the blocker review already verified

- Digest mechanics match the ratified candidate contract and shipped code:
  proposal bytes first, unsigned uint64 big-endian framing, unsigned UTF-8
  bytewise path ordering, and proposal lookup/read failure before mutation.
- The former durable-audit blocker is fixed: candidate `contracts.md` requires
  the paired revision record to preserve decision mode/source and delegated or
  consensus evidence with `MUST`.
- The former overview blocker is fixed: the loop is policy-governed and
  human-gated by default and at every doctrine floor.
- All four unconditional first branches remain human-only: cited design-record
  contradiction, absent/unreachable design record, every ratification-review
  blocker, and drift origin. Consensus arms nothing until its separately
  ratified tier/evidence exists.
- Topic and filename stem match; no heading-coverage co-edit is owed; the
  proposal queue held only this proposal; the orchestrator executor exclusion
  and independent-review floor remain intact.

Fable also recorded non-blocking concerns to preserve during the next review:

1. The proposal says the durable revision-record audit clause `SHOULD` preserve
   evidence, while the corrected candidate intentionally strengthens it to
   `MUST`; drive the eventual revise as `modify`, not plain `accept`, and record
   that strengthening in `## Modifications`.
2. The audit-field home is not named; an implementation follow-up should
   standardize it, plausibly under `## Ratification Review`.
3. Increment-scoped drift sentences must be swept deliberately by Increment 3.
4. The predicate enumeration omits the proposal's explicit word `mismatched`,
   although the exact-valid-mode condition and constraints preserve safety.
5. The orchestrator needs-attention human lane remains correct under the manual
   safe default; its retirement is the post-ratification sibling follow-up.

## Resume sequence after authorization

1. Fetch livespec `origin/master`. If it moved from `6dab6033`, discard the four
   full-file candidates and re-derive the entire 71/8 semantic change from the
   new predecessor bytes; never splice stale full-file content. If it did not
   move, apply only the authorized two-suffix correction.
2. Confirm only the four candidate files differ, all H2 sets remain unchanged,
   and the Increment-3 drift paragraph remains byte-identical.
3. Install the owned worktree's ignored pack with
   `mise exec -- just install-worktree-pack`, immediately restore the installer
   edit with `mise exec -- git checkout -- .livespec.jsonc`, and verify config
   is clean. Run doctor-static and `mise exec -- just check-pre-commit-doc-only`.
   Never use `--no-verify`; halt on any hook/gate failure.
4. Recompute the canonical proposal-plus-resulting-files digest from the exact
   final bytes. Update the Fable packet for the new base/digest and spawn a fresh,
   separate read-only Fable-model reviewer. A literal `NO BLOCKERS` verdict is
   mandatory and never self-waived; report any blocker rather than silently
   iterating again.
5. Only after `NO BLOCKERS`, fetch again. If master moved, re-derive and obtain
   another review because every full-file byte and digest may have changed.
   Run the required stale-`spec/*`-branch precondition and re-enumerate queues.
6. Assemble exactly one revise decision with
   `proposal_topic: spec-governance-revise-decision-mode`, decision `modify`,
   the `MUST` strengthening recorded in `modifications`, the four exact
   `resulting_files[]`, and fresh matching Fable evidence. Invoke the config-named
   revise CLI with `--post-step-doctor`; follow the complete `livespec:revise`
   post-step contract. Do not touch the Increment-3 drift-doctrine sentence.
7. Commit only the governed revise output, push, open the ratification PR, wait
   for the complete forge matrix, rebase-merge, refresh primary master, and
   remove the ratification worktree/branch.
8. Only after core ratifies, file—but do not implement or dispatch—the
   orchestrator child that retires its needs-attention revise lane when the
   shared predicate is false. Its draft and notes remain under
   `tmp/overseer/spec-side-autonomy/`; replace version/PR placeholders and
   parent it to `livespec-jvdvx4`.

## Standing constraints

- Increment 2 is doctrine-sensitive; every four-floor and exact-byte clause is
  load-bearing.
- All tracked edits stay in dedicated worktrees. Never edit or commit tracked
  files in `/data/projects/livespec`.
- Never pass `--no-verify`; use worktree → PR → rebase-merge → primary refresh
  → cleanup.
- Never touch another session's worktree, branch, sandbox, ledger item, or
  admission label. Never kill the acting overseer daemon.
- The detailed milestone trail is
  `tmp/overseer/spec-side-autonomy/worker-status.log`.
