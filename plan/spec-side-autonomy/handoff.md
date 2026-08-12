# spec-side-autonomy — handoff

Updated 2026-08-12. **The spec amendment `livespec-jvdvx4.9` was waiting on is
RATIFIED as v202.** That item is now UNBLOCKED and ready to IMPLEMENT — it is
no longer waiting on a decision, a design pass, or a review. Its full
implementation brief is attached as a NOTE ON THE LEDGER ITEM; read that note
before starting.

There is NO uncommitted work and NO worktree belonging to this thread.

**Ledger anchor:** epic `livespec-jvdvx4`

## What landed this session

**v202 — `shared-ci-logic-channel-and-partition-repair`.** Ratifying commit
`4c4748ba`, rebase-merge `45de58f2`, PR #2195 in `thewoolleyman/livespec`.
Filed by PR #2191, corrected by #2192, #2193 and #2194 across four review
rounds. Two proposals in one file, at maintainer direction, because both edit
the same sentences:

- **The partition contradiction (`livespec-n0ka`) is repaired structurally, not
  per-instance, and that bug is CLOSED.** The drift sweep found the
  shared-content channel partition asserted in SIX places, not the two the bug
  reported — lines 9, 109, 117 and 216 as well as 463 and 496. The existing
  section §"Shared content provenance" is now the SINGLE authority; every other
  site is a reference forbidden to restate it; and no site may assert a cardinal
  count of channels. The enumeration also gained the shared-runtime bullet it
  never had.
- **The shared-CI-logic lane is named.** `livespec` itself publishes reusable
  GitHub Actions workflows plus the core scripts they invoke; consumers
  downstream call them at a pinned release tag; the derivation lives in ONE
  implementation every caller executes. Core as producer is `consumer →
  producer`, which the No-Circular-Dependency Directive permits.

## THE LIVE TASK — `livespec-jvdvx4.9`, now ready to implement

Read its ledger note first; it carries the ordered implementation plan, the
ratified clauses the implementation must honor, and the scope correction. In
brief:

1. Core hosts `.github/workflows/reusable-spec-pr-merge-policy.yml`, checking
   core out at a PINNED RELEASE TAG (`@vX.Y.Z`, never `@master`).
2. ONE core-shipped script carries the derivation, invoked by both callers.
3. Refactor core's root `auto-enable-merge.yml` to call the shared surface.
4. The copier template calls the same surface.
5. Correct the item's two factually-wrong acceptance clauses.
6. Live leg in a `livespec-orchestrator-*` repo — NOT an adopter, which cannot
   exist — reading all three diagnostic checks IN ORDER.

**PORT THE FIXED SHAPE FROM `livespec-jvdvx4.13`, NEVER THE v200-ERA
ORIGINAL**: `--no-renames` local derivation, the `added|renamed|copied` API
filter, and the `grep_allow_empty` errexit repair. The reference file is at
`f8c98ced`. Copying the original reintroduces two defects already fixed once.

**Not factory-dispatchable.** Both a core-hosted reusable workflow and the
template `.jinja` are workflow surfaces, and the dispatch credential withholds
the `workflows` grant. This lands maintainer-side via worktree and reviewed PR.

## Filed this session — do not fold into the epic

- **`livespec-jvz8`** (P2, bug) — `livespec-dev-tooling` and `livespec-runtime`
  ratify their own specifications with NO spec-PR merge-policy gate, and v202
  permanently excludes them from the only shared lane, because a repository core
  itself consumes must not carry a pinned artifact resolving core. The exclusion
  is architecturally FORCED and correct; the gap PRE-EXISTS v202 (neither repo is
  template-generated, so the ratified requirement's derived set already excluded
  them). **Do NOT close it by having either repo consume the core channel** —
  that is the banned shape and the reason the item exists.

## Still open, unchanged

- **`livespec-odkk`** (P2, bug) — `templates/orchestrator-plugin/` pins four
  reusable workflows at `@master` while the ratified requirement demands
  `@vX.Y.Z` and core's own five usages pin a release tag. Independently
  reproduced during review. Any fifth template workflow `.9` adds MUST pin
  `@vX.Y.Z`; `@master` is a DEFECT, never "the established sibling convention".
- **`livespec-jvdvx4.2`** — `backlog`. Leg 2 (the multi-repo `spec_governance`
  backfill across TWELVE repos — re-derive the target set at execution time,
  resolving each repo's own default branch and committed credential wrapper) is
  **NOT YET AUTHORIZED**. Do not start it.

## What this session learned that the next one should not re-pay for

- **A ratifying PR here needs a MANUAL merge, and that is correct.** Core has
  never declared `spec_governance.spec_pr_merge`, so it inherits the safe
  `manual` default. Do not wait for auto-merge on one, and do not read its
  absence as a fault. Verified live on #2195: run `31550839305` concluded
  success, the policy step emitted `pull-request effective policy: manual
  (source: default)` then `effective policy is manual; leaving for human merge`,
  and only then was `autoMergeRequest` absent. **Read those three legs in that
  order** — a crashed step and a manual-policy step both leave auto-merge unset,
  which is exactly how `livespec-jvdvx4.13` shipped broken.
- **A proposal-filing PR auto-merges before review finishes, by design.** Line
  443 exempts a plain propose-change filing from the spec-PR fold. So filing and
  reviewing are NOT sequential gates on one PR: the filing lands unreviewed, and
  review gates RATIFICATION. Plan on a follow-up correction PR rather than
  holding the filing open.
- **`* [new branch]` on a second push means the branch was auto-deleted after
  merging and your push RECREATED it**, orphaning your commit with no PR. It
  happened twice here. Verify against the forge rather than reading it as a
  routine push message.
- **Review the FIX as adversarially as the original.** Four rounds found ten
  blockers; THREE of the ten were introduced by a fix round that was itself
  correcting real defects, and the last was a citation made MORE precise and
  thereby FALSE — it named the authority section for a prohibition that section
  does not state. A correction is not safe because it corrects something real.
- **Give each reviewer a DIFFERENT instrument.** Round 1's two reviewers
  returned disjoint findings, so neither could have substituted for the other.
  The mechanical-composition instrument — literally applying every edit to a
  scratch copy and reading the product — found a doubled em dash that no amount
  of reading the edits could catch.
- **Ratification evidence mechanics that are easy to get wrong:** the CLI
  requires `reviewer_identity` to EQUAL `reviewer_model`, and that model to equal
  the configured value (`fable`), so both fields read `fable` and the real agent
  name goes in the rationale. Minimum review age is 1s; `reviewed_at` must not
  precede the proposal's `created_at`. Verify the digest by IMPORTING
  `_canonical_ratification_digest` from the plugin rather than reimplementing its
  uint64-BE framing.
- **Nothing downstream checks that the CLI wrote what you reviewed.** Diff the
  written file against the reviewed bytes yourself.

## Standing constraints

- All tracked edits use dedicated worktrees; never edit or commit tracked files
  directly in `/data/projects/livespec`, which is the pane's cwd.
- Never pass `--no-verify`; worktree → reviewed PR → rebase-merge → primary
  refresh → cleanup; halt and report on hook failure.
- This thread holds NO worktree of its own. Every worktree under
  `$HOME/.worktrees/livespec/` belongs to another session — do not enter, edit,
  push, force-push, remove, or reap any of them, and never run the worktree
  reaper in this repository. **Enumerate rather than trusting any list here; it
  drifts.**
- Another session lands commits on this repo's `master` concurrently — it moved
  three times during this session. Rebase rather than assuming your base is
  current, and force-push ONLY your own branch.
- This repo rebase-merges, so one change has TWO SHAs. Test the merge commit or
  ask the forge; never `--is-ancestor` on a branch tip.
- The `github_rate_limit_guard` hook denies any command carrying a loop keyword
  (`for`, `while`, `until`, `select`, `sleep`) alongside a forge read —
  **including inside inline Python list comprehensions and `jq` `select(...)`**,
  both of which tripped it here. Capture a forge read in one call and parse it in
  another; use `map`/`filter` instead of a comprehension.
- Query the forge's jobs API with `per_page=100` and compare against
  `total_count`.
- When a pull-request-triggered workflow produces ZERO runs, read `.mergeable`
  and `.mergeable_state` BEFORE suspecting the workflow.
- Never kill the acting overseer daemon (tmux `livespec-overseer:1.1`).
- The detailed milestone trail remains
  `tmp/overseer/spec-side-autonomy/worker-status.log`.
