# spec-side-autonomy — handoff

Updated 2026-08-11 after `livespec-jvdvx4.6` landed and BOTH live-exercise
legs were observed. There is no uncommitted work in any worktree belonging
to this thread; the worktree the previous handoff described has been
committed, merged, and removed.

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

## LANDED — `livespec-jvdvx4.6` (ROOT-REPO-ONLY), closed on both live legs

Driven under `brief-36-finish-jvdvx4.6.md`, which superseded briefs
32/34/35. The root-repo workflow shipped and both live-exercise legs were
observed with their evidence recorded. Nothing on this item remains open.

- **Implementation:** PR #2145, rebase-merge
  `c4b6706324f2f415287de004170107e57998ba6a`, branch commit `e2d97df7`.
  Scope was the root file `.github/workflows/auto-enable-merge.yml` only,
  +209 lines, zero lines removed — so no pre-existing gate was weakened.
- The worktree the previous handoff described as holding uncommitted work
  (`feat-spec-pr-merge-auto-enable-workflow`) has been committed, merged,
  and REMOVED, and its branch deleted.

- **What shipped.** A checkout step (`fetch-depth: 0`, deliberately — a
  shallow checkout is a named SOURCE-level failure) plus a "Resolve
  spec-PR effective policy" step implementing: touches-no-spec-root
  fall-through, merge-base computation, the entirely-empty-diff
  hardening, the REQUIRED dual-source hardening (local-git derivation
  vs. the hosting API's `pulls/.../files` listing MUST agree —
  disagreement is derivation FAILURE), stem derivation, KNOWN-EMPTY
  fall-through (kept distinct from FAILURE — conflating them would
  silently revert the 2026-05-26 cadence fix), the CLI invocation
  (`spec_governance.py --show-effective --pr-effective-policy
  --proposal-stem <stem>...`), and the journal-as-GATE append (append
  BEFORE registering; append failure blocks registration; no invented
  persistence — the PR timeline is the durable leg). The "Enable
  auto-merge" step is gated on
  `steps.policy.outputs.decision != 'blocked'`.
- **A fail-open defect was found and fixed while adopting the inherited
  worktree.** Three error paths captured output with
  `$(cmd | grep ...)`, which reports only the LAST pipeline stage — so a
  git or hosting-API error became an empty file list rather than an
  error. When the other source was also legitimately empty, the two
  "agreed" into a false KNOWN-EMPTY and auto-enabled. `spec.md` requires
  a git or hosting-API error to be derivation FAILURE, which blocks.
  Each source is now captured and status-checked BEFORE any filtering.
  A no-match `grep` still exits 1 and that remains an empty RESULT
  rather than an error, so the filters stay deliberately exempt.
- **Verification before merge:** the embedded script was extracted
  byte-for-byte from the YAML via `yaml.safe_load` (not hand-copied) and
  run in disposable git repos with a controlled `gh`, against EIGHT
  scenarios — non-spec-touching PR, `manual`-floored proposal,
  `auto-on-green` proposal (journal event appended and validated),
  KNOWN-EMPTY, dual-source disagreement, journal-write failure,
  hosting-API error with an empty local derivation, and a git error.
  All eight resolved as the spec requires; the last two are the
  regression cases for the defect above.
- `templates/orchestrator-plugin/.github/workflows/auto-enable-merge.yml.jinja`
  — deliberately NOT touched. Tracked as `livespec-jvdvx4.9` (see below).
  The asymmetry is documented in the shipped workflow's header comment so
  it does not read as an oversight.

### The split (decided, do not re-litigate)

- `livespec-jvdvx4.6` was NARROWED to the ROOT-REPO file only. The
  one-PR/no-drift rule from briefs 32/34 is RETIRED for this item — with
  the template half deliberately deferred and TRACKED, there is one
  implementation and one recorded gap, not two drifting ones.
- The template half plus the core-to-CI distribution mechanism (reusable
  workflow vs. shipping the module via the pip package — both named for
  evaluation) is **`livespec-jvdvx4.9`**, filed and still open. No
  adopter runner can reach `spec_governance.py` today, so writing the
  template now would fail closed in every adopter and silently disable
  spec-PR auto-merge fleet-wide. Do not start `.9` without a fresh brief.

### ⚠ READ THIS BEFORE THE LEG EVIDENCE BELOW — the gate is BROKEN on the shape that matters

Both legs below passed honestly and their evidence is accurate. **They do
not prove the gate works on a real ratification**, and the FIRST real
ratification through it (v201, PR #2153) proved it does not. Tracked as
**`livespec-jvdvx4.13` (P1)**.

- Leg 1's probe ADDED a proposal file. A real ratifying PR **MOVES** the
  proposal into `history/vNNN/proposed_changes/` — git records `R100`,
  the API reports `renamed`. The workflow derives stems from ADDED files
  only, on BOTH sources (`--diff-filter=A` and `status=="added"`), so both
  miss it and both AGREE they miss it. Dual-source hardening cannot catch
  a filter-level bug; `spec.md` states that residual honestly. Derived
  stem set on a real ratification: EMPTY.
- On PR #2153 the policy step CRASHED (run `31466134643` concluded
  FAILURE, step exited 1 emitting zero output) because the runner shell is
  `bash -e`, the script sets `pipefail`, and a no-match `grep` kills the
  assignment. Auto-merge was correctly absent — but only because a crashed
  step writes no `decision` output and the enable step is guarded on
  `!= 'blocked'`. **The floor held by accident.**
- **FIX ORDER IS LOAD-BEARING.** Repair the rename derivation FIRST. Fix
  the crash alone and an empty stem set reaches the KNOWN-EMPTY branch,
  resolves `auto`, and silently auto-merges EVERY ratifying spec PR.
- Consequence: on the real path the CLI is never invoked and no
  `spec_pr_merge` journal event is appended, so the journal-as-gate
  behavior v201 ratified is itself unexercised in production.
- Diagnostic rule for whoever re-tests: **a silent exit 1 looks exactly
  like a pass if the only check is that auto-merge is off.** Verify the
  policy step emitted its own output AND that the run concluded success.

The generalizable lesson: a synthetic probe validates the shape you
built, not the shape the system generates.

### The LIVE exercise — both legs observed, evidence recorded

- **Leg 1 — PASSED.** PR #2147 (head `a2e5594b`) added a synthetic
  non-`-revision` file at
  `SPECIFICATION/history/v999-live-exercise/proposed_changes/live-exercise-floor-probe.md`
  carrying no `spec_pr_merge_policy` key, confirmed to resolve `manual`
  against the shipped CLI before opening. Run `31463749002` logged
  `pull-request effective policy: manual (source: default)` and the
  human-merge fall-through line; job step 5 "Enable auto-merge" reported
  `conclusion=skipped`; the API reported `.auto_merge` null. Auto-merge
  was NOT registered. The PR carried NO `do-not-merge` label on purpose —
  that label is evaluated by the job-level `if:` and would have skipped
  the whole job, proving nothing, so the `spec_pr_merge` floor had to be
  the only blocker. The PR was CLOSED, its branch deleted, and its
  worktree removed; nothing reached `master`.
- **Leg 2 — PASSED.** The control still auto-enables. Recorded twice:
  first on PR #2145 itself (because `pull_request` events run the HEAD
  branch's workflow definition, #2145 exercised the new step on itself),
  where run `31462961430` logged
  `PR does not touch SPECIFICATION; spec_pr_merge does not apply` then
  `Auto-merge enabled on PR #2145 (rebase strategy)` with the API
  reporting `auto_merge` SET (rebase); and again on the post-merge
  control PR that carried this handoff refresh.

### One residual, stated rather than overclaimed

Both live legs exercised the **step-1 fall-through** control path (a PR
touching no spec root). The **KNOWN-EMPTY** control sub-path — a PR that
DOES touch the spec root but ratifies nothing, which is the shape the
2026-05-26 cadence fix specifically protects — is covered by the
extracted-script harness but was NOT exercised live, because doing so
would have meant fabricating a spec-touching PR that would not otherwise
be landed. The next plain propose-change-filing PR exercises it for free;
read that run's log to close the residual.

### Master CI was red when this thread finished — NOT caused by this work

Surfaced 2026-08-11 rather than left silent. Run `31464485796` on
`75e332bc` (`chore(master): release 0.30.0`) failed. This thread's merge
`c4b67063` was CI SUCCESS and `3d6dca95` after it was SUCCESS, so the red
begins at the release commit, not here.

The failing job is `check-fleet-marketplace-relative-sources`, but its
`just check-fleet-marketplace-relative-sources` step was SKIPPED — the
failure is the preceding `mise trust + install` step, where mise could
not install `aqua:koalaman/shellcheck@0.11.0`: TLS
`certificate verify failed ... (self-signed certificate)` fetching from
github.com releases in the HOSTED container lane. That is an
infrastructure / TLS-interception failure, not a check violation, so a
re-run may clear it; if it recurs it belongs to the CI-lane work, not to
this epic.

**A verification trap worth carrying forward:** the GitHub jobs API
returned 30 of **75** jobs by default, and ALL THIRTY were green. Reading
that first page would have reported master all-green while it was red —
the failing job sat outside it. Always request `per_page=100` and check
`total_count` against the number of jobs returned.

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
  NOT this thread's, re-enumerated 2026-08-11 (this list drifts — run
  `git worktree list` rather than trusting it):
  `ci-concurrency-group`, `docs-refresh-spec-side-autonomy-binder`,
  `fabro-handoff-ci-capacity`, `fix-spec-governance-config-railway`,
  `phase0-selfhosted-shadow-lane`, `refactor/lloc-band-regrowth`,
  `spec-ratify-durable-evidence-locus`.
- Never kill the acting overseer daemon (tmux `livespec-overseer:1.1`).
- This thread now holds NO worktree of its own. The former
  `feat-spec-pr-merge-auto-enable-workflow` worktree was committed,
  merged as `c4b67063`, and removed, so the previous handoff's
  "do not reap while it sits uncommitted" caveat is spent. Every
  remaining worktree in this repo belongs to another session — do not
  enter, edit, push, remove, or reap any of them.
- Verify against the forge after a fetch, never a possibly stale
  working tree. This repo rebase-merges: one change has two SHAs; test
  the merge commit or ask the forge, never `--is-ancestor` on a branch
  tip.
- The detailed historical milestone trail remains
  `tmp/overseer/spec-side-autonomy/worker-status.log`.
