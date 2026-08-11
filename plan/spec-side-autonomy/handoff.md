# spec-side-autonomy — handoff

Updated 2026-08-11 at session wind-down. **The epic's implementation work is
DONE and closed.** One child remains open — `livespec-jvdvx4.9` — and it is
**waiting on a maintainer decision, not on more investigation.** Its design
pass is complete and the full write-up is attached as a NOTE ON THE LEDGER
ITEM; read that note before doing anything on `.9`.

There is NO uncommitted work and NO worktree belonging to this thread.

**Ledger anchor:** epic `livespec-jvdvx4`

## Landed state (all closed, do not redispatch)

- **Increment 1** (core levers): PRs #1939, #1942, #1949, #1944. Closed.
- **Increment 2** (revise delegation): ratified v193 (PR #1978). Slice A
  `livespec-jvdvx4.3` (PR #1980) and Slice B `livespec-jvdvx4.4`
  (PR #1987). Closed.
- **Increment 3** (drift consensus doctrine + `drift_acceptance_mode`):
  ratified `livespec` v196 (PR #2033) + `livespec-orchestrator-beads-fabro`
  v058 (PR #1307); implementation PR #2058. Closed.
- **`livespec-bhammf`** (the spec-PR-merge redesign) — ratified as
  **v200** (`spec-governance-pr-merge-redesign`, commit `2970ad0a`,
  landed 2026-08-10) after FOUR independent-review rounds (each round
  found real, verified-against-live-bytes defects — see
  `tmp/overseer/spec-side-autonomy/worker-status.log` for the blow-by-
  blow if you need the history). `livespec-bhammf` itself is closed.
- **`livespec-jvdvx4.7`** (CLI half: `--proposal-stem`,
  `--pr-effective-policy` on `spec_governance.py --show-effective`) —
  PR #2133, merge `91bd0754c6e1eff7f1ecfd3e7081820eea39181a`. Closed,
  live-exercised (well-formed/malformed events, existing types
  unaffected — done in a later slice, see `.8` below for the actual
  journal-event exercise).
- **`livespec-jvdvx4.8`** (journal event type `spec_pr_merge` on
  `--journal-event-json`) — PR #2137, merge
  `12a8136523fd9083d7336dd8b6f5f2c5a2487118`. Closed. Live-exercised
  post-merge: well-formed event accepted + appended, malformed event
  rejected (exit 2, no append), unknown `event_type` now gets the fixed
  generic rejection message (enumeration removed, not extended, so it
  can't rot again), and the four pre-existing event types are
  unaffected.
- **`spec-pr-merge-durable-evidence-locus`** proposal — first filed as
  `restore-spec-pr-merge-durable-evidence` (PR #2139), then renamed and
  reframed. **RATIFIED as v201** — ratifying commit `f55feb6b`, PR #2153,
  rebase-merge `edadee1e`. Cleared by TWO independent adversarial
  reviewers plus a third review of the exact final bytes (the revise CLI
  binds evidence to a digest over `proposal_bytes + sorted(resulting_files)`,
  so proposal-level approvals structurally cannot satisfy it). ADDS one
  sentence to the
  `spec_pr_merge` journal clause in `contracts.md`: the GitHub PR
  timeline MAY be the durable final-evidence leg, so the journal is a
  decision GATE (append before mutation, append-failure blocks
  registration) rather than that event's durable archive. This settles
  why the journal living under ephemeral `tmp/` in a CI runner is
  intentional, not a defect. **It is a NEW clause, not a restoration** —
  the first filing claimed to restore text v200 had dropped, which was
  FALSE: that language came from a v190 proposal that was REJECTED and
  ordered refiled, and v200 was the refile. **The lesson, because that
  error reached six artifacts before a reviewer stopped it:** a file under
  `history/vNNN/proposed_changes/` is NOT a design record. A history cut
  archives accepted and rejected proposals side by side; only the paired
  `<stem>-revision.md` `decision:` field distinguishes them. Read it, and
  grep the cut's own ratified spec files, before treating any archived
  clause as prior art. One of the six — a false citation in
  `.github/workflows/auto-enable-merge.yml` — is still live, tracked as
  `livespec-jvdvx4.11`.

## Landed since the section above (briefs 37 and 38 — all CLOSED, do not redo)

- **`livespec-jvdvx4.6`** — the ROOT-REPO spec-PR merge gate. PR #2145,
  rebase-merge `c4b67063`. Closed on both its live legs.
- **`livespec-jvdvx4.13`** (P1) — that gate shipped BROKEN, and is now FIXED.
  PR #2157, rebase-merge `f8c98ced`. Two defects, fixed together in the
  required order because repairing the crash alone would have made it fail
  OPEN. (A) A ratifying pull request MOVES the proposal: git scores `R100`,
  the hosting API reports `renamed`, and both derivations filtered to ADDED
  only — so both missed it and AGREED they had, which the dual-source
  hardening structurally cannot catch. (B) The runner shell is
  `/usr/bin/bash -e {0}` and the script's own `set -uo pipefail` does not
  cancel that inherited `-e`, so a no-match `grep` exiting 1 killed the step
  before it emitted any output. The crash was NOT confined to ratifications —
  it hit every plain propose-change filing, so the KNOWN-EMPTY branch was
  UNREACHABLE in production rather than merely untested.
  Closed on THREE live legs, each verified in this order: the run CONCLUDED
  SUCCESS, the policy step EMITTED ITS OWN OUTPUT, and only then the
  `auto_merge` field. Rename leg PR #2159 run `31470489523`; known-empty leg
  PR #2160 run `31470710223`; non-spec leg PR #2157 run `31470202653`. Probe
  pull requests closed unmerged, with a positive control confirming no probe
  artifact reached `master`.
- **`livespec-jvdvx4.11`** — the false "restored v190 design record" citation.
  CLOSED, but discharged by `f8c98ced` and NOT by `00dac97a` alone: that
  earlier commit removed the false citation and replaced it with one naming a
  `proposed_changes/` path that stopped resolving, plus a "NOT ratified"
  assertion that expired when v201 landed.
- **`livespec-jvdvx4.10`**, **`livespec-jvdvx4.12`**, **`livespec-0ybg`** —
  agent-guidance corrections. PR #2161, rebase-merge `b5dc8ed4`. A fourth
  review defect class (independent reviewers sharing a flawed instrument);
  the conflicted-pull-request verification instance; and retirement of the
  dead `dispatcher.host_dispatch_cap` key.

## THE LIVE TASK — `livespec-jvdvx4.9`: design DONE, awaiting a DECISION

**Do NOT start implementing, and do NOT re-run the investigation.** The design
pass is complete. Its full evidence — candidates, disqualification reasons,
measurements, recommendation, and costs — is attached as a NOTE ON
`livespec-jvdvx4.9` in the ledger. Read that note first; this section is only
the pointer and the state.

**Decided on evidence.** Four of six candidate distribution mechanisms are
DISQUALIFIED. Shipping `spec_governance.py` through the `livespec-dev-tooling`
pip package, or through `livespec-runtime`, each puts downstream code inside an
upstream artifact. Hosting the reusable workflow in `livespec-dev-tooling`
makes upstream pin downstream. A bare pinned checkout is dominated, because it
duplicates the derivation — which this item's own acceptance forbids.

**The recommendation** composes the two survivors: core hosts
`.github/workflows/reusable-spec-pr-merge-policy.yml`, whose steps check out
core at the pinned RELEASE tag and invoke a core-shipped script carrying the
derivation, with core's root workflow AND the template both calling it. One
`uses:` line per consumer; one script, so drift is structurally impossible
rather than merely discouraged; and the logic becomes unit-testable, which
120 lines of embedded YAML bash cannot be.

**Why it stopped short of implementing.** Under the LIVE partition clause
(`non-functional-requirements.md` line 496), none of the three ratified
delivery lanes carries core's own executable CI logic: `copier` is
static-only, `livespec-dev-tooling` ships build-time checks, and
`livespec-runtime` explicitly has NO reusable GitHub Actions surface and may
not depend on core. The recommendation therefore needs a ratified spec
amendment, which requires `/livespec:propose-change` plus an independent
adversarial review plus `/livespec:revise`, and is NOT self-ratifiable. That
is the maintainer decision this item now waits on.

**A measurement that removes a whole class of worry.** `spec_governance.py`
runs in a COMPLETELY BARE environment — verified under
`env -i PATH=/usr/bin:/bin` with system `python3`: no venv, no pip, no uv, no
network — because `.claude-plugin/scripts/_vendor/` vendors every dependency.
This item is NOT blocked on packaging or installability. It is blocked only on
getting the file onto a runner, and on the missing lane.

**Two acceptance clauses on the item are FACTUALLY WRONG.** "An adopter repo's
generated workflow … exercised live in a real adopter" names a target that
cannot exist: `.copier-answers.yml` is present in EXACTLY TWO repos —
`livespec-orchestrator-beads-fabro` and `livespec-orchestrator-git-jsonl` —
and in ZERO adopters. The live leg IS reachable, but in a
`livespec-orchestrator-*` repo: both carry the generated workflow, both show
zero `spec_pr_merge` hits confirming the gap is real, and both have genuine
ratification history plus a pending proposal. Correct the acceptance wording
when the item is picked up.

**When implementation eventually happens, port the FIXED shape** from
`livespec-jvdvx4.13` — the `--no-renames` local derivation, the
`added|renamed|copied` API filter, and the `grep_allow_empty` errexit repair.
**NEVER the v200-era original**: copying it reintroduces two defects that are
already understood and already fixed once.

## Filed during the design pass — NOT children of this epic, do not fold in

- **`livespec-n0ka`** (P2, bug) — the ratified spec states the shared-content
  partition TWICE with contradictory counts and axes. Line 463 says "the two
  channels … static-vs-executable"; line 496 says "the three channels …
  static-vs-buildtime-vs-runtime". Ratified clause-lockstep. **Linked as a
  BLOCKER of `livespec-jvdvx4.9`**, because `.9`'s amendment must not amend
  into a clause that contradicts itself. Needs the full propose-change path.
- **`livespec-odkk`** (P2, bug) — `templates/orchestrator-plugin/` pins four
  reusable workflows at `@master`, while the ratified §"Shared code sync"
  requires `@vX.Y.Z` and core's own five usages all pin `@v1.20.4`. Every repo
  generated from the template inherits the violation. **For anyone reading
  older notes: `@master` is a DEFECT, not "the established sibling
  convention"** — both the work item and a brief described it as convention
  and reasoned from it, which is how it would have propagated.

## Other open items on this epic — do not start

- **`livespec-jvdvx4.2`** — `backlog`. Legs 1/2a/2b closed; leg 2 (the
  multi-repo `spec_governance` backfill across TWELVE repos, not ten —
  re-derive the target set at execution time, resolving each repo's own
  default branch and its own committed credential wrapper) is **NOT YET
  AUTHORIZED**. Do not start it.

## Standing constraints

- All tracked edits use dedicated worktrees; never edit or commit tracked
  files directly in `/data/projects/livespec`, which is the pane's cwd.
- Never pass `--no-verify`; worktree → reviewed PR → rebase-merge → primary
  refresh → cleanup; halt and report on hook failure.
- This thread holds NO worktree of its own. Every worktree under
  `$HOME/.worktrees/livespec/` belongs to another session — do not enter,
  edit, push, force-push, remove, or reap any of them, and never run the
  worktree reaper in this repository. Present at wind-down (this list DRIFTS,
  so enumerate rather than trusting it): `ci-concurrency-group`,
  `docs/ci-hetzner-chain-finding`, `fabro-handoff-ci-capacity`,
  `fix-spec-governance-config-railway`, `phase0-selfhosted-shadow-lane`.
- Another session lands commits on this repo's `master` concurrently — one
  collided with PR #2161 mid-review, taking a number this thread had used.
  Rebase rather than assuming your base is current, and force-push ONLY your
  own branch.
- **When a pull-request-triggered workflow produces ZERO runs, read
  `.mergeable` and `.mergeable_state` BEFORE suspecting the workflow.** A
  conflicted pull request has no merge ref, so no run object is created at
  all, which is indistinguishable from a broken trigger. This cost a full
  misdiagnosis here; it is now instance 30 of
  `.ai/verifying-against-the-right-source.md`.
- Query the forge's jobs API with `per_page=100` and compare against
  `total_count`. The default first page once showed thirty green jobs while
  `master` was red, because the failing job sat outside it.
- Verify against the forge after a fetch, never against a possibly stale
  working tree. This repo rebase-merges, so one change has two SHAs: test the
  merge commit or ask the forge, never `--is-ancestor` on a branch tip.
- The `github_rate_limit_guard` hook denies any command carrying a loop
  keyword (`for`, `while`, `until`, `select`, `sleep`) alongside a forge read
  — **including those words in ordinary English prose** in a title, body, or
  comment. Write long bodies to a file and pass `--body-file`, and capture a
  forge read in one call while parsing it in another.
- Never kill the acting overseer daemon (tmux `livespec-overseer:1.1`).
- The detailed milestone trail remains
  `tmp/overseer/spec-side-autonomy/worker-status.log`.
