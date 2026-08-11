# spec-side-autonomy — handoff

Session wind-down as of 2026-08-11T07:2xZ, mid-task. There is real,
tested, uncommitted work sitting in a worktree — read this whole file
before doing anything, especially before touching any worktree.

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
  reframed. **Filed, NOT ratified.** ADDS one sentence to the
  `spec_pr_merge` journal clause in `contracts.md`: the GitHub PR
  timeline MAY be the durable final-evidence leg, so the journal is a
  decision GATE (append before mutation, append-failure blocks
  registration) rather than that event's durable archive. This settles
  why the journal living under ephemeral `tmp/` in a CI runner is
  intentional, not a defect. **It is a NEW clause, not a restoration** —
  the first filing claimed to restore text v200 had dropped, which was
  FALSE: that language came from a v190 proposal that was REJECTED and
  ordered refiled, and v200 was the refile. Sits
  pending in `SPECIFICATION/proposed_changes/`; needs an independent
  adversarial review + `/livespec:revise` before it ratifies. Do not
  ratify it yourself — that is a separately-spawned-reviewer step.

## IN PROGRESS — `livespec-jvdvx4.6` (now ROOT-REPO-ONLY), UNBLOCKED, not yet landed

**This is the live task. Read `brief-32-implement-jvdvx4.6.md`,
`brief-34-restore-evidence-leg-then-resume.md` (phase 2), AND
`brief-35-land-root-workflow.md` in full before touching it, IN THAT
ORDER** — 35 is the current authorization and narrows scope; 32/34
still carry the ratified-contract pointers, the four easy-to-get-wrong
items, and the live-exercise procedure brief-35 explicitly keeps in
force. Do NOT dispatch this item and do NOT mark it `ready` — its
scope is a `.github/workflows/` file, the factory sandbox's dispatch
credential deliberately withholds the `workflows` grant, and that
rejection is the boundary working (`.ai/ci-gate-discipline.md`). You
implement this one yourself, maintainer-side.

**What exists right now, uncommitted:**

```
$HOME/.worktrees/livespec/feat-spec-pr-merge-auto-enable-workflow
  branch: feat/spec-pr-merge-auto-enable-workflow
  based on primary at 43df3761 (post restore-durable-evidence merge)
```

- `.github/workflows/auto-enable-merge.yml` — **fully implemented and
  locally tested**, uncommitted, modified in the worktree. It adds a
  checkout step (`fetch-depth: 0`, deliberately — a shallow checkout is
  a named SOURCE-level failure) and a "Resolve spec-PR effective
  policy" step implementing: touches-no-spec-root fall-through,
  merge-base computation, the entirely-empty-diff hardening, the
  REQUIRED dual-source hardening (local-git derivation vs. the hosting
  API's `pulls/.../files` listing MUST agree — disagreement is
  derivation FAILURE), stem derivation, KNOWN-EMPTY fall-through
  (distinct from FAILURE — conflating them would silently revert the
  2026-05-26 cadence fix), the CLI invocation
  (`spec_governance.py --show-effective --pr-effective-policy
  --proposal-stem <stem>...`), and the journal-as-GATE append (append
  BEFORE registering; append failure blocks registration; no invented
  persistence — the PR timeline is the durable leg per the restored
  v190 design record above). The final "Enable auto-merge" step is
  gated on `steps.policy.outputs.decision != 'blocked'`.
- I tested the **exact embedded script** (extracted byte-for-byte from
  the YAML via a Python `yaml.safe_load`, not a hand-copy) against six
  scenarios in disposable scratch git repos, using the real
  `spec_governance.py` from this worktree: a PR not touching
  `SPECIFICATION/` (falls through immediately), a `manual`-floored
  ratified proposal (blocked, no journal append), an `auto-on-green`
  proposal (journal event appended correctly, `decision=auto`),
  KNOWN-EMPTY (touches spec root but adds no proposal — falls through,
  CLI never invoked), a dual-source disagreement (blocked), and a
  journal-write failure via a read-only `tmp/` dir (blocked, per
  contract). All six passed. This file is ready to commit as-is unless
  you find a defect re-reading it.
- `templates/orchestrator-plugin/.github/workflows/auto-enable-merge.yml.jinja`
  — deliberately **not touched by this item.** See "The split" below —
  it is now tracked separately as `livespec-jvdvx4.9`, not this item's
  scope.

### THE BLOCKER IS RESOLVED — read `brief-35-land-root-workflow.md` in full

Brief-35 verified the cross-repo CLI-distribution gap independently
(confirmed: no adopter runner can reach `spec_governance.py` today;
the fleet's established shared-CI pattern is a reusable workflow —
`release-dispatch.yml.jinja` / `pin-freshness.yml.jinja` both `uses:
thewoolleyman/livespec-dev-tooling/.github/workflows/reusable-*.yml
@master` — and core hosts no such workflow yet) and made the call:
**halting instead of inventing a fleet-wide mechanism was correct, and
the fix is to split the work, not to guess.**

**The split (decided, do not re-litigate):**

- `livespec-jvdvx4.6` is NARROWED to the ROOT-REPO file only
  (`.github/workflows/auto-enable-merge.yml`). The one-PR/no-drift rule
  from brief-32/34 is explicitly RETIRED for this item — with the
  template half deliberately deferred and TRACKED elsewhere, there is
  one implementation and one recorded gap, not two drifting ones.
- The template half plus the distribution mechanism (reusable workflow
  vs. shipping the module via the pip package — both named for
  evaluation) is now **`livespec-jvdvx4.9`**, filed and explicitly NOT
  this item's scope. Do not start `.9` under this brief.

**Next action, in order (all still pending — nothing further landed
after this handoff was written; if a later session already did some of
this, re-verify against the forge/ledger before repeating any of it):**

1. Add ONE more code comment to the already-tested root workflow file
   in the worktree, naming `livespec-jvdvx4.9` as the reason the
   template twin is not yet aligned (so the asymmetry reads as tracked,
   not as an oversight), then commit it in the existing worktree
   (`feat/spec-pr-merge-auto-enable-workflow`, based on `43df3761`
   — rebase onto current `origin/master` first if it has moved), open a
   PR, and land it through the normal reviewed rebase-merge path. The
   implementation itself does not need re-writing — it was tested
   against six scenarios (see above) and brief-35 didn't ask for
   changes beyond the one comment.
2. Then run the LIVE exercise below and close `livespec-jvdvx4.6` only
   after both legs are observed with their evidence recorded.
3. Do NOT start `livespec-jvdvx4.9` under this same thread of work
   unless a fresh brief authorizes it.

Do NOT close `livespec-jvdvx4.6` on unit tests. Per brief-32/34/35, run
the LIVE exercise:

- **Leg 1** — open a PR that adds a non-`-revision` file under
  `SPECIFICATION/history/*/proposed_changes/<stem>.md` with no
  `spec_pr_merge_policy` override (floors to `manual`). Confirm
  auto-merge is NOT registered (read the actual evidence — the
  workflow run log / journal — not an inference from the PR not yet
  having merged). **This PR must never merge. Close it and delete its
  branch as soon as you have the observation.** If it DOES register
  auto-merge, that is an implementation defect: close the PR
  immediately, treat it as a defect, and report rather than retry.
- **Leg 2** — a genuinely harmless, genuinely mergeable PR that touches
  no `SPECIFICATION/history/*/proposed_changes/` files (or none at
  all) must still auto-enable exactly as today. Do not fabricate
  something you would not otherwise land.
- If leg 2 fails (the control is wrongly blocked), you have broken
  auto-merge for the whole repository: **REVERT immediately**, then
  re-land correctly. Never a lever, flag, or severity demotion — that
  rule is absolute (`.ai/ci-gate-discipline.md`).
- Close `livespec-jvdvx4.6` only after BOTH legs are observed with
  their evidence recorded.

## Other open items on this epic (unrelated to the above, do not start)

- **`livespec-jvdvx4.2`** — `backlog`. Legs 1/2a/2b closed; leg 2 (the
  multi-repo `spec_governance` backfill across TWELVE repos, not ten —
  re-derive the target set at execution time, resolving each repo's
  own default branch and its own committed credential wrapper) is
  **NOT YET AUTHORIZED**. Do not start it.
- `livespec-bhammf` is now CLOSED (see Landed state) — the earlier
  handoff's "not this thread's business" note is stale; the redesign
  IS this thread's business and finished the 4-round filing/ratify
  cycle described above.

## Standing constraints

- All tracked edits use dedicated worktrees; never edit or commit
  tracked files directly in `/data/projects/livespec`.
- Never pass `--no-verify`; worktree → PR → rebase-merge → primary
  refresh → cleanup; halt on hook failure.
- Never touch another session's worktree, branch, sandbox, ledger
  item, or admission label. Peer worktrees currently present that are
  NOT this thread's (re-enumerate — this list drifts):
  `ci-concurrency-group`, `docs-refresh-spec-side-autonomy-binder`,
  `fabro-handoff-ci-capacity`, `fix/spec-governance-config-railway`,
  `phase0-selfhosted-shadow-lane`.
- Never kill the acting overseer daemon (tmux `livespec-overseer:1.1`).
- Do not run the worktree reaper while `feat-spec-pr-merge-auto-enable-workflow`
  sits uncommitted — it is real work, not stale.
- Verify against the forge after a fetch, never a possibly stale
  working tree. This repo rebase-merges: one change has two SHAs; test
  the merge commit or ask the forge, never `--is-ancestor` on a branch
  tip.
- The detailed historical milestone trail remains
  `tmp/overseer/spec-side-autonomy/worker-status.log`.
