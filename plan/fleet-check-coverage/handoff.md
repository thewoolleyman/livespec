# Handoff — fleet-check-coverage

The single resumable entry point for the **fleet-check-coverage** thread: make
every structural check shipped by `livespec-dev-tooling` cover every tracked
first-party `.py` in every fleet repo, automatically — by replacing per-repo
coverage allowlists (which fail OPEN) with filesystem-derived coverage plus
fail-closed guards, rolled out **warn → burndown → per-repo-fail** so nothing
breaks all at once. A fresh session can execute the next action from this file
alone via the read-first chain — no chat history required.

## For a fresh session — read first

- **What this is.** A `dispatcher.py` (>2,600 lines,
  `livespec-orchestrator-beads-fabro/.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/dispatcher.py`)
  sailed past the fleet's per-file logical-line ceiling because the `file_lloc`
  check walks a HARDCODED `.claude-plugin/scripts/livespec/` tree that does not
  exist in a repo whose package dir is named `livespec_orchestrator_beads_fabro/`
  — so it walked zero files and exited 0. Every other structural check has the
  same class of blindness there (its per-repo `[tool.livespec_dev_tooling]` block
  restates core's `livespec/` paths verbatim). Read the research docs before
  acting:
  - `plan/fleet-check-coverage/research/root-cause.md` — why the allowlist model
    fails open, with reproduce commands.
  - `plan/fleet-check-coverage/research/design.md` — the target
    (filesystem-derived universe via `git ls-files`, fail-closed empty guard,
    partition-completeness meta-check), the exemption policy (`_vendor/` + tests +
    `@generated`-marked + `templates/**`), the three-phase rollout, and the
    (now-resolved) open questions.
  - `plan/fleet-check-coverage/research/check-inventory.md` — the Phase-0
    classification: which checks derive their universe vs stay role-scoped, the
    per-repo first-party `.py` counts, and the wiring/severity facts.
  - **`plan/fleet-check-coverage/research/phase1-grooming.md` — READ FIRST for the
    burndown.** The AUTHORITATIVE Phase-1 slice spec: the v0.35.2 WARN inventory,
    the load-bearing correction (role declaration IS the Phase-2 flip, so partition
    is not a Phase-1 bucket), the footgun per-copy disposition, the driver/console
    wiring prerequisite, factory-safety routing, and the per-repo slice table. It
    supersedes the ordering in `phase1-inventory.md`.
- **The FOUNDATION primitive is already LANDED** (see Progress log). It lives in
  `livespec-dev-tooling`'s `livespec_dev_tooling/config.py`, released in
  **v0.34.1**, and is the substrate the Phase-0 reroute sequence built on:
  - `iter_first_party_py_files(*, repo_root)` — the git-index-derived universe
    (`git ls-files '*.py'` minus exemptions). IO wrapper; raises `GitLsFilesError`.
  - `filter_first_party_py(*, tracked_py, repo_root, tests_tree_prefix)` — the
    pure exemption filter (`_vendor` segment, root `tests_tree_prefix` + any
    `conftest.py`, `templates/**`, `@generated`-marked).
  - `is_generated(*, path)` — `@generated` sentinel via the ecosystem-generic
    comment-syntax registry `_COMMENT_PREFIXES_BY_EXTENSION` (line-comment markers
    AND block-comment open delimiters `/*`, `<!--`).
  - `has_first_party_py(*, repo_root)` — trivial derivation, ahead of need for the
    empty-walk guard.
  These are the substrate. **PR1 (2026-07-08) wired them into `file_lloc`**
  (released **v0.34.2**, adversarially reviewed NO-BLOCKERS, accepted — see
  Progress log). **PR2 + PR2b (2026-07-09) then rerouted the 7 `config:source_trees`
  checks through the shared `resolve_check_universe()` and reshaped the resolver to
  OWN root-resolution** (released **v0.34.4**, independently reviewed NO-BLOCKERS,
  accepted — see Progress log). **PR3 (2026-07-09) then rerouted the raw-`rglob`/
  hybrid stragglers + `no_lloc_soft_warnings`, and rejected empty
  `tests_tree_prefix`** (released **v0.34.5**, independently reviewed NO-BLOCKERS,
  accepted — see Progress log). **PR4 (the partition-completeness meta-check)**
  then landed in `livespec-dev-tooling` and is released as **v0.35.1** after a
  bump-pin wiring hotfix (see Progress log). The `main_guard` role-scope fix then
  released **v0.35.2** (fanned out fleetwide). The `livespec` template-projection
  repair landed in PR #982. Phase 1 is now GROOMED (corrected model in
  `research/phase1-grooming.md`); the next action is DISPATCH — see "The next
  action".
- **Companion adversarial prompt.**
  `plan/fleet-check-coverage/live-adversarial-review-prompt.md` — hand this to an
  independent reviewer session; a NO-BLOCKERS verdict is a precondition for
  accepting any Phase-2 flip. (It already earned its keep: the independent review
  of the foundation PR caught the block-comment gap — see Progress log.)
- **Epic anchored.** `livespec-i5ebqd` [EPIC] is the thread's status anchor; the
  Phase-0 mechanism is tracked as child `livespec-fa3eu5` (MAINTAINER-DRIVEN
  host-side `livespec-dev-tooling` work — do NOT auto-dispatch to the factory).
  Status is READ live from the ledger (`bd show <id>`), never stored here.
- **⚑ Golden rules.**
  - **DRIVE THE WHOLE PLAN AUTONOMOUSLY.** On resume, do NOT stop to ask the
    maintainer which action to take. Execute the next action end-to-end —
    groom the epic into ready per-repo tracks, close stale ledger items,
    detect gaps, dispatch/drive implementation through the factory, land PRs,
    run the independent adversarial review, accept — continuously until you
    hit ~50% context (then rotate this handoff and print the resume command)
    OR you are genuinely BLOCKED (an irreversible/outward-facing action needing
    authorization, a real product/values decision, or an unresolvable ambiguity).
    A structured picker offering "do the obvious next thing vs. defer it" is the
    anti-pattern the maintainer explicitly rejected (2026-07-09): if the next
    action is obvious from this handoff, JUST DO IT. Surface findings and
    decisions as you go, but keep working — never idle waiting for a go-ahead.
  - Ready, factory-safe implementation is **factory-dispatched** — never
    hand-coded inline in the overseer session. The overseer FILES and DISPATCHES;
    the factory (Dispatcher / the `drive` operation) builds each item under the
    `just check` + `/livespec:doctor` janitor gate. (EXCEPTION already in play:
    the Phase-0 MECHANISM in `livespec-dev-tooling` is host-side maintainer-driven,
    authored via scoped agents in worktrees under maintainer review — it is the
    shared enforcement package, not factory-safe app work.)
  - **`livespec-dev-tooling` AUTO-MERGES on green CI** (an `enable-auto-merge`
    job). A PR cannot be "held for review" — it merges the moment CI passes, and
    release-please cuts a release. So the review model here is: land on green →
    independent adversarial review of the merged commit → **fix-forward** (never a
    force-update of a merged PR). Plan every PR expecting it to auto-merge.
  - **Stage the mechanism into a small PR sequence, not one mega-PR.** Rerouting
    the checks interacts with the release fail-lever (next section) and touches a
    self-covering package; land it in reviewable, live-verified increments.
  - **Parallel, not sequential.** Phase 1 burndown runs every repo's track
    concurrently through the factory; do NOT serialize repo-by-repo. Phase 0 is
    the one barrier (its dev-tooling release must be pinned first); after it, fan
    out wide.
  - The Phase-2 per-repo FLIP adds **NO escape hatch / severity lever / skip** to
    pass (`.ai/ci-gate-discipline.md`) — it is severity, never a bypass.
  - Secrets are probe-only (`printenv NAME | wc -c`); never echo values.
  - The overseer session **rotates before ~50% context**: refresh THIS file
    (current state, in-flight PRs/agents per repo, next action), then print the
    resume command verbatim as the LAST line of the recap.
  - Print an `Epic · Track (repo) · Status · %Complete` table (read live) before
    any gate or status report, and refresh it every ~15 minutes while tracks run.
- **Resume command:** `/livespec-orchestrator-beads-fabro:plan fleet-check-coverage`

## The fleet — every repo in scope

The mechanism lands in `livespec-dev-tooling`; the burndown + flip touch every
repo that ships first-party Python. Counts below are LIVE from the landed
`iter_first_party_py_files` (v0.34.2), verified 2026-07-08 — authoritative over
any older figure in the research docs:

| Repo | Role | first-party `.py` | Note |
|---|---|---:|---|
| `livespec-dev-tooling` | the shared check package | 88 | mechanism lands here; self-covers |
| `livespec` (core) | hub / dogfood | 120 | was fail-open on the 7 (empty source_trees) → now WARN-only on 120 until Phase-2 |
| `livespec-orchestrator-beads-fabro` | orchestrator | 78 | the trigger (dispatcher.py + siblings) |
| `livespec-console-beads-fabro` | operator console app | **0** | the ONE genuinely empty-universe repo; empty-walk guard MUST PASS |
| `livespec-orchestrator-git-jsonl` | orchestrator | 40 | real coverage; verify |
| `livespec-runtime` | library | 27 | real coverage; verify |
| `livespec-driver-claude` | thin runtime binding | 2 | NOT codeless: 2 hook `.py` — MUST be covered |
| `livespec-driver-codex` | thin runtime binding | 3 | NOT codeless: 3 hook `.py` — MUST be covered |

The empty-walk guard's correctness on the ONE genuinely empty-universe repo
(`livespec-console-beads-fabro`, 0 tracked `.py` → MUST pass) is a first-class
acceptance case — as is confirming the Driver repos' hook `.py` are COVERED (they
are NOT codeless). See the adversarial prompt.

**Pin / fan-out status (UPDATED 2026-07-09 after PR4 + hotfix).**
`livespec-dev-tooling` is at **v0.35.1**. PR4 first released
`check-partition-completeness` as **v0.35.0**, then `livespec-dev-tooling` PR #296
fixed the bump-pin composite action so new canonical check slugs are reconciled
into consumer `justfile` aggregate wiring. Release **v0.35.1** fanned out and
confirmed the fix in the Python consumers that had failed `check-aggregate-completeness`
under v0.35.0: `livespec-runtime` PR #156, `livespec-orchestrator-git-jsonl`
PR #219, `livespec-orchestrator-beads-fabro` PR #386, plus both Driver repos
(`livespec-driver-claude` PR #112, `livespec-driver-codex` PR #91). The
`livespec` v0.35.1 bump PR #981 merged with two non-required checks still red:
`check-copier-template-smoke` and `check-canonical-slugs-projection`. `livespec`
PR #982 regenerated `templates/orchestrator-plugin/canonical-slugs.yml`, added
`check-partition-completeness`, and merged with those checks green so new
orchestrator-plugin adopters also inherit the new slug.

Earlier note retained because it keeps preventing bad reads: an earlier handoff
claimed four repos were "stranded at v0.33.5" — that was a **FALSE ALARM from
stale local `origin/master` refs** (reading `git show origin/master:` in a sibling
clone WITHOUT fetching it first shows a stale ref; the bump-pin PRs had in fact
merged, e.g. `livespec-runtime` #151→v0.34.2). **Lesson: `git fetch` a sibling
clone before reading its `origin/master` for cross-repo state.**

## Progress log

- **2026-07-08 — planning complete.** Epic `livespec-i5ebqd` anchored; dev-tooling
  check set enumerated + classified (`research/check-inventory.md`); OQ1 (generic
  `@generated` sentinel), OQ2 (cover own hooks, exempt `templates/**`), OQ4
  (classification), OQ5 (first-party predicate) resolved (`research/design.md`).
- **2026-07-08 — Phase-0 FOUNDATION landed (pure addition, no reroute).**
  - `livespec-dev-tooling` PR #281 → **v0.34.0**: `iter_first_party_py_files`,
    `filter_first_party_py`, `is_generated` + comment-syntax registry,
    `has_first_party_py`, `GitLsFilesError`, with hermetic tests.
  - Independent adversarial review REFUTED the `@generated` claim: the C-family
    registry had only `//`, so a `/* @generated */` block comment was missed. PR
    #281 had already AUTO-MERGED + released 0.34.0 by the time the finding landed.
  - Fixed FORWARD: `livespec-dev-tooling` PR #283 → **v0.34.1** added block-comment
    open delimiters (`/*`) to the C-family registry + red tests. (Defect was
    latent — primitive not wired into any check, zero `@generated` files fleetwide.)
  - Fan-out already bumped `livespec` core's pin to `livespec-dev-tooling` v0.34.1.
  - **Coordination note:** another session left an orphaned worktree/branch
    `fix/generated-block-comment-syntax` (commit `abd5430`) — a redundant parallel
    block-comment fix that never opened a PR (superseded by #283). It is NOT this
    thread's branch; leave it for that session/maintainer to reap. (Still present
    2026-07-08 — a PR #285 has since been opened on it by that other session; NOT
    ours to touch.)
- **2026-07-08 — Phase-0 REROUTE PR1 landed + ACCEPTED (`file_lloc`, the trigger).**
  - `livespec-dev-tooling` PR #286 → merged commit `4562773` → released **v0.34.2**.
    `file_lloc` now derives its universe from `iter_first_party_py_files` (dropped
    the hardcoded `_COVERED_TREES` walk); the three legacy paths were repurposed as
    a severity classifier `_LEGACY_HARDFAIL_TREES`.
  - **Severity model DECIDED — delta-WARN** (the "how does the lever behave for the
    newly-covered set" question, now resolved for Phase-0): a file UNDER a legacy
    tree keeps today's severity (soft-warn 201–250, **hard-fail >250, exit 1**); a
    file NEWLY pulled into the git-derived universe emits ALL LLOC diagnostics at
    **WARN (exit 0), even >250**. This is strictly safer than design.md's blanket
    "all WARN": it regresses NO existing gate (core keeps its hard ceiling) AND
    keeps dev-tooling's OWN release unblocked (the newly-covered 88 files are all
    WARN, dodging the release-lever trap). Phase-2 flips a repo by dropping it from
    the legacy classifier so its whole universe hard-fails (a natural OQ3 story).
    This is the established pattern for EVERY subsequent applies-to-all reroute.
  - **Live cross-repo evidence** (overseer-run, then independently reproduced):
    `livespec-orchestrator-beads-fabro` exit 0 / `dispatcher.py` (1586 LLOC) WARNS /
    0 errors; `livespec-console-beads-fabro` exit 0 on empty universe;
    `livespec` core exit 0 / 10 legacy-soft-band warnings / **0 errors** (no
    regression); `livespec-dev-tooling` exit 0 / 88 WARN / 0 errors (own release
    unblocked).
  - **Independent Fable adversarial review: NO-BLOCKERS** — every claim reproduced
    with throwaway git fixtures (no-allowlist-regression incl. a `livespec_extra/`
    sibling-prefix edge that `is_relative_to` classifies correctly; delta-WARN both
    directions; codeless pass; exemptions un-launderable; wiring intact).
  - **Residuals carried to later increments (non-blocking):** (1) invoking a check
    from a repo SUBDIRECTORY walks zero and exits 0 silently — the deferred
    empty-walk guard as designed (`has_first_party_py` on the same cwd) would NOT
    catch it either; the guard PR must address the invocation contract (recipes run
    at repo root). (2) `no_lloc_soft_warnings` is still fail-open (not yet rerouted)
    — in the PR2 set. (3) The `@generated` sentinel is position-unconstrained (a
    full-line sentinel comment anywhere exempts) — possible future head-of-file
    tightening.
  - Cleanup: PR1 executor's worktree/branch reaped; `livespec-dev-tooling` primary
    clean on master. Ledger child `livespec-fa3eu5` → `in_progress`, PR1 acceptance
    journaled as a comment.
- **2026-07-09 — Phase-0 REROUTE PR2 (source_trees family) + PR2b (reshape) landed + ACCEPTED.**
  - PR #288 → merged `d3b1441` → **v0.34.3**: the 7 `config:source_trees` checks (`all_declared`,
    `assert_never_exhaustiveness`, `global_writes`, `keyword_only_args`, `match_keyword_only`,
    `no_inheritance`, `private_calls`) + `file_lloc` rerouted to the git-derived universe via a
    shared `resolve_check_universe()`; delta-WARN (legacy = `config.source_trees` for the 7 /
    `_LEGACY_HARDFAIL_TREES` for file_lloc keeps today's severity; newly-covered WARN, exit 0). Added
    `resolve_repo_root()` (root-anchoring), `is_under_any_tree()` (shared classifier), `GitToplevelError`.
  - PR #290 → merged `c72db0e` → **v0.34.4**: resolver reshape. An independent adversarial review
    (Codex watcher + Fable) caught the empty-walk guard as VACUOUS dead code —
    `not universe and has_first_party_py(repo_root)` is `not X and bool(X)` == always False (both
    sides the same call). Fixed fix-forward: `resolve_check_universe()` now OWNS root-resolution (no
    `repo_root` param; returns `(root, universe)`), the vacuous guard + `EmptyUniverseError` removed,
    `file_lloc` + the 7 route through the single entry point, the monkeypatch-only dead-code test
    replaced with a real `GitToplevelError` fail-closed test.
  - **`refactor:` DID cut a release here (v0.34.4)** — dev-tooling's `release-please-config.json`
    marks `{"type":"refactor","hidden":false}`, so the general "refactor cuts no release" seam does
    NOT hold for this repo. Harmless (behavior-preserving; consumers got the reshape immediately).
  - **Author identity:** PR2b onward authored `thewoolleyman <chad@thewoolleyman.com>` (maintainer
    chose to switch; the stale local `Test <test@example.com>` override in dev-tooling's `.git/config`
    was unset → uses the correct global). `d3b1441` predates the fix (git-authored Test; GitHub PR
    author thewoolleyman) — not rewritten.
  - **Fan-out:** all 7 consumers repinned to **v0.34.4** (auto-merged on green CI).
  - **Live evidence (independent Fable review reproduced 48 check runs against the real clones):**
    console 0-py codeless-pass; driver-claude universe=2 / driver-codex universe=3 hooks COVERED;
    orchestrator universe=78, `file_lloc` WARNs dispatcher.py+16, 0 hard errors (+ proved v0.34.2
    scanned ZERO on the orchestrator = the original bug); core universe=120, 0 hard errors, WARN on
    newly-covered. Fleet CI green under both v0.34.3 and v0.34.4.
  - **Independent Fable adversarial review: NO-BLOCKERS** (all 6 dimensions reproduced).
  - **Concern filed → `livespec-sw19`:** reject empty `tests_tree_prefix` (a residual fail-open
    corner — `startswith("")` exempts every file → empty universe; pre-existing with the foundation
    filter, no fleet repo hits it today). Resolved in PR3.
  - **Correction (Concern 2) — core was ALSO fail-open on the 7:** core/orchestrator/drivers OMIT
    `source_trees` in their `[tool.livespec_dev_tooling]` block → effective `config.source_trees=()`
    (block-present + omitted key defaults empty, NOT the core fallback). So pre-PR2 the 7
    config-driven checks scanned ZERO on core too (Fable proved it with v0.34.2), not just the
    orchestrator. Post-PR2 the ONLY repo where the 7 hard-fail anything is dev-tooling
    (`source_trees=["livespec_dev_tooling"]`); everywhere else the whole universe is newly-covered
    (WARN) until the Phase-2 flip. `root-cause.md` + `check-inventory.md` corrected in this PR.
- **2026-07-09 — Phase-0 REROUTE PR3 (remaining stragglers) landed + ACCEPTED.**
  - `livespec-dev-tooling` PR #292 → merged `c047da19` (carrying authored commit
    `ae1c797`) → release PR #293 → **v0.34.5**. Red→Green replay preserved the
    Red trailers for `tests/livespec_dev_tooling/checks/test_config_driven_checks.py`
    and Green verified at `2026-07-09T05:12:25Z`.
  - Rerouted the remaining applies-to-all checks through `resolve_check_universe()`:
    `no_lloc_soft_warnings`, `no_write_direct`, `comment_line_anchors`,
    `main_guard`, and `rop_pipeline_shape`. `no_write_direct` keeps its
    command/supervisor write-permitted exemptions; the other four use the shared
    git-derived universe and legacy classifier. Legacy offenders keep today's
    severity; newly-covered offenders emit `phase="0-warn"` +
    `newly_covered=True` and exit 0.
  - Folded in **`livespec-sw19`**: `tests_tree_prefix = ""` now raises
    `ConfigParseError` instead of exempting every tracked `.py`.
  - **Fan-out:** all 7 consumers repinned to **v0.34.5** (auto-merged on green CI):
    `livespec` PR #978, `livespec-orchestrator-beads-fabro` PR #384,
    `livespec-orchestrator-git-jsonl` PR #217, `livespec-runtime` PR #154,
    `livespec-driver-claude` PR #110, `livespec-driver-codex` PR #89,
    `livespec-console-beads-fabro` PR #121.
  - **Live evidence (Codex overseer run against fetched `origin/master` secondary
    worktrees using released v0.34.5 code):** all five PR3 checks exited 0 in
    every consumer; no errors; newly-covered diagnostics were WARN-only. Counts:
    core (`livespec`) WARNs `10/10/0/10/0` for
    `no_lloc_soft_warnings`/`no_write_direct`/`comment_line_anchors`/`main_guard`/
    `rop_pipeline_shape`; `livespec-orchestrator-beads-fabro` WARNs
    `4/69/0/10/0`; `livespec-orchestrator-git-jsonl` WARNs `0/2/0/4/0`;
    `livespec-runtime` WARNs `0/0/0/3/0`; `livespec-driver-claude` WARNs
    `0/1/0/1/0`; `livespec-driver-codex` WARNs `0/2/0/2/0`;
    `livespec-console-beads-fabro` WARNs `0/0/0/0/0`.
  - **Independent Godel adversarial review: NO-BLOCKERS.** The reviewer verified
    all five checks route through `resolve_check_universe()`, WARN-only
    newly-covered diagnostics include the required fields, legacy buckets still
    control exit status, empty `tests_tree_prefix` is rejected and covered, and
    resolver-backed fixtures use real git repos.
  - Cleanup: `livespec-dev-tooling` PR worktree/branch reaped; primary checkout
    fast-forwarded to `origin/master` at v0.34.5 and clean. The pre-existing
    unrelated `fix/generated-block-comment-syntax` worktree remains outside this
    thread's cleanup scope, per the earlier coordination note.
- **2026-07-09 — Phase-0 PR4 (partition-completeness meta-check) landed; fan-out
  hotfix landed.**
  - `livespec-dev-tooling` PR #294 → **v0.35.0** added
    `check-partition-completeness`, the first role-partition meta-check. It
    verifies every first-party `.py` is claimed by exactly one configured role or
    a named exclusion, with Phase-0 WARN severity.
  - v0.35.0 exposed a real fan-out gap: the new canonical slug auto-joined
    `canonical_check_slugs()`, but the bump-pin composite action did not insert
    missing canonical slugs into consumer `justfile` aggregates. That made
    `check-aggregate-completeness` fail in Python consumers such as
    `livespec-runtime` PR #155 and `livespec-orchestrator-git-jsonl` PR #218.
  - `livespec-dev-tooling` PR #296 → **v0.35.1** fixed the bump-pin composite
    action to reconcile canonical justfile wiring: add missing slugs to the
    aggregate `check:` target and append generic zero-argument recipes when the
    consumer already uses `check-aggregate-completeness`. It deliberately does
    not edit CI matrices.
  - v0.35.1 fan-out verified the hotfix: aggregate completeness passed and the
    bump PRs merged in `livespec-runtime` (#156),
    `livespec-orchestrator-git-jsonl` (#219),
    `livespec-orchestrator-beads-fabro` (#386), `livespec-driver-claude` (#112),
    `livespec-driver-codex` (#91), and `livespec-console-beads-fabro` (#123).
  - `livespec` PR #981 merged its v0.35.1 pin but left two non-required checks
    red because the orchestrator-plugin template projection had not been stamped
    with the new canonical slug. `livespec` PR #982 fixed that by running
    `just stamp-canonical-slugs`, adding `check-partition-completeness` to
    `templates/orchestrator-plugin/canonical-slugs.yml`, and merging with
    `check-canonical-slugs-projection` + `check-copier-template-smoke` green.
- **2026-07-09 — Phase-1 GROOMED: live inventory measured, 7 per-repo tracks filed.**
  - Closed stale ledger item `livespec-sw19` (empty `tests_tree_prefix` — landed
    in PR3/v0.34.5, verified on dev-tooling `config.py:259`; item was stale-open).
  - Measured the full fleet Phase-1 `newly_covered` WARN inventory at v0.35.1 and
    recorded it in `research/phase1-inventory.md` (authoritative). **Measurement
    lesson (bit me once mid-session): NEVER measure with a repo's OWN local venv —
    they were all stale (runtime/drivers at v0.33.5; orchestrator between
    v0.34.2–v0.34.5). Measure with the dev-tooling v0.35.1 venv python from the
    target repo cwd, or in a fresh factory sandbox.** Fleet totals (WARN):
    core 176 (partition 120), orchestrator-beads-fabro 164 (no_write_direct 69,
    file_lloc 16 incl dispatcher.py 1586), dev-tooling 104 (main_guard 64),
    runtime 55, git-jsonl 39, driver-codex 15, driver-claude 10, console 0. ≈563.
  - **7 child tracks filed** (each narrates epic membership in its description; NO
    `depends_on` to the open epic; labeled `origin:freeform`):
    `livespec-9bym` core, `livespec-236f` orchestrator-beads-fabro,
    `livespec-iily` dev-tooling (HOST-SIDE, do NOT auto-dispatch to the factory),
    `livespec-8x7d` runtime, `livespec-t4e0` orchestrator-git-jsonl,
    `livespec-gqte` driver-codex, `livespec-v74p` driver-claude. (console: no track.)
  - **TWO design findings surfaced (see `research/phase1-inventory.md` §"Two
    findings"); they block a clean burndown until decided:**
    1. **main_guard mis-classification.** main_guard BANS `if __name__ ==
       "__main__":` in the source tree (core's convention: entry points live in
       `bin/*.py` wrappers). dev-tooling's 64 hits are modules correctly invoked
       as `python -m …` that legitimately carry main guards — NOT violations. PR3
       rerouted main_guard as applies-to-all, but it is actually ROLE-SCOPED (only
       valid under the bin/-wrapper convention). FIX is in the CHECK (dev-tooling),
       not deleting 64 correct guards; it shrinks Phase-1 scope fleetwide
       (also hits orchestrator 10, git-jsonl 4, runtime 3, drivers 1–2).
    2. **Shared-hook single-source.** `livespec_footgun_guard.py`
       (keyword_only_args etc.) is COPIED into ≥4 repos with identical violations;
       fix the canonical copy once and propagate vs. 4 divergent per-repo edits.
- **2026-07-09 — design finding #1 RESOLVED + main_guard fix landed; #2 self-resolved.**
  - **Maintainer decided: main_guard is ROLE-SCOPED** (not fleet-wide-intentional).
    Fix the check, do NOT refactor 64 correct guards. Decision + predicate recorded
    on ledger `livespec-iily`.
  - **`livespec-dev-tooling` PR #300** (branch `reclassify-main-guard-scope`, commit
    `06f97dc`) lands it: main_guard now inspects ONLY files under a
    `.claude-plugin/scripts/` tree (any package, git-derived — no fail-open
    regression). Files outside it (dev-tooling's `livespec_dev_tooling/**` run via
    `python -m`, libraries, harness hooks) are skipped. Delta-WARN preserved
    (legacy `.claude-plugin/scripts/livespec/` ERROR; other plugin trees WARN).
    Red→Green single commit; drift-swept the shared
    `test_config_driven_checks.py::test_main_guard_warns_for_newly_covered_package`
    fixture into a `.claude-plugin/scripts/` tree; main_guard.py 100% per-file
    coverage; all 50 `just check` targets green. Measured effect: dev-tooling
    main_guard 64→0; keeps the real `.claude-plugin/scripts/**` plugin-tree hits
    (orchestrator etc.).
  - **ACCEPTED + released + fanned out.** PR #300 rebase-merged to dev-tooling
    master as commit `8b88bb2` (byte-identical to the branch `06f97dc`), released
    as **dev-tooling v0.35.2** (release PR #301). Bump-pin fan-out repinned the
    consumers to v0.35.2: `livespec` #988, `livespec-orchestrator-beads-fabro`
    #388, `livespec-runtime` #158, `livespec-orchestrator-git-jsonl` #221,
    `livespec-driver-claude` #114, `livespec-driver-codex` #93 (all merged);
    `livespec-console-beads-fabro` #126 (open, 0-py, trivial). **Independent Fable
    adversarial review returned NO-BLOCKERS** — reproduced all 6 checks live
    (64→0; in-scope still bites WARN/ERROR; delta-WARN both arms; drift-sweep real;
    17 tests; fail-open angles dismissed). Acceptance journaled on `livespec-iily`.
  - **Finding #2 self-resolved:** `livespec_footgun_guard.py` is copied into all 7
    repos (6 at `.claude/hooks/`, driver-codex at `livespec/hooks/`); no copier
    template source. Disposition: treat livespec core's `.claude/hooks/` copy as
    canonical, fix once, propagate to the other 6 (identify the sync path) rather
    than 6 divergent edits. Folded into the driver/core track notes.
- **2026-07-09 — Phase-1 GROOMED with a corrected model; both gate-findings resolved.**
  (This session. Primary refreshed to `f7a3642` = merged handoff PR #989 + v0.35.2
  pin bump #988; the merged `gate-cleared` worktree reaped.) Wrote
  `research/phase1-grooming.md` — now the AUTHORITATIVE slice spec — after two
  read-only research passes and a check-source study that CORRECTED the plan:
  - **Re-measured the fleet at v0.35.2:** grand total **474** newly_covered WARN
    (−89 vs v0.35.1, entirely the main_guard fix). Per-repo: core 166,
    orchestrator 156, runtime 53, dev-tooling 40, git-jsonl 37, driver-codex 13,
    driver-claude 9, console 0. (Orchestrator + git-jsonl keep 2 main_guard rows
    each — REAL `.claude-plugin/scripts/**` hits, not check bugs.) file_lloc
    per-file lists + orchestrator no_write breakdown are in the grooming note §1.
  - **THE CORRECTION (grooming note §2):** `partition_completeness` is NOT a
    separate burndown bucket, and the handoff's "partition-config restate FIRST"
    ordering was BACKWARDS. Every `[tool.livespec_dev_tooling]` role key is a
    check SEVERITY classifier (`source_trees`→the 7; `covered_trees`→no_write +
    no_lloc_soft; `source_tree_prefixes`→coverage gate). So declaring roles to
    claim files for partition IS the Phase-2 hard-fail flip — it would break CI
    if the code violations aren't fixed first. Corrected model: **Phase 1 fixes
    the NON-partition code violations while files stay newly_covered/WARN; Phase 2
    declares the role layout = claim-for-partition + severity flip in one reviewed
    config commit.** The 165 fleetwide partition WARN resolve automatically at the
    flip. This resolves the bulk of OQ3: the flip lever is a committed pyproject
    role declaration, not an env var. RESIDUAL: file_lloc's legacy tree is
    hardcoded to `.claude-plugin/scripts/livespec/`, so non-core repos can't flip
    file_lloc via config — a dev-tooling follow-up under `livespec-iily`.
  - **Finding #2 (footgun) CORRECTED:** there is NO sync mechanism and the 7
    copies are hand-forked into 4 behaviorally-divergent groups; "fix core, copy
    to 6" would CLOBBER driver-codex's intentional variant. Disposition:
    **per-copy signature fix** (behavior-neutral `*,` + keyword call sites),
    folded into each repo's keyword_only slice — NOT propagation.
  - **New prerequisite found (§4):** driver-claude, driver-codex, console wire
    ZERO structural checks into justfile+CI — their hook coverage is theoretical
    until wired. §6.1 is the maintainer decision (full suite vs subset).
  - **All 7 tracks made READY:** acceptance criteria + corrected-scope notes
    appended via `bd update` (scope = code fixes only; partition/flip is a
    separate host-side Phase-2 item; footgun per-copy). The grooming note §5 table
    is the per-repo slice spec.
  - **MAINTAINER DECISION 2026-07-10 (grooming §6.1 resolved):** WIRE THE FULL
    applies-to-all structural suite into the 3 unwired repos (both Drivers +
    console) via `check-aggregate-completeness` — uniform coverage. Slice0 = wire
    full suite (prerequisite) before each thin repo's WARN fix + flip. Recorded on
    `livespec-gqte`, `livespec-v74p`, and a NEW console track **`livespec-q7bx`**
    (console = wire + verify empty-universe no-op flip). All 8 in-scope repos are
    now tracked and UNBLOCKED. Next action: DISPATCH (below).
- **2026-07-10 — the two BIG tracks GROOMED into ready layered factory slices; a
  DISPATCH-MODEL blocker surfaced.** Ran the `groom` operation on both (set to
  `backlog` first; both now CLOSED / regroomed-out):
  - **Orchestrator `livespec-236f` → 4 chained slices** (by check-family, layered
    A→B→C→D by `dispatcher.py`/`_dispatcher_*` file overlap): **`livespec-y4f7hp`**
    236f-A mechanical (keyword_only 29 + all_declared 26 + private_calls 1) — READY;
    **`livespec-tlvsn4`** 236f-B no_write_direct (69→io/); **`livespec-my2s7k`**
    236f-C structural (no_inheritance 4 + main_guard 2 + no_lloc_soft 3);
    **`livespec-umabdn`** 236f-D file_lloc (16 split/exempt, dispatcher.py 1586 the
    tentpole, highest review). B/C/D gated behind their blocker.
  - **Core `livespec-9bym` → 3 chained slices:** **`livespec-2j46re`** 9bym-A
    mechanical (all_declared 17 + keyword_only 8 incl footgun + global_writes 1) —
    READY; **`livespec-7jcdfk`** 9bym-B no_write_direct (10→io/); **`livespec-txn2bq`**
    9bym-C no_lloc_soft (10 band). Partition (120) + role-flip stay host-side Phase-2.
  - **⚠ DISPATCH-MODEL BLOCKER (cross-repo/tenant — do NOT guess):** `drive
    --action impl:<id>` resolves the work-item from the `--repo`'s OWN beads tenant
    (`resolve_store_config(cwd=repo)`) and builds THERE. But every sibling repo has
    its OWN per-repo Dolt tenant, and ALL this thread's tracks/slices were filed in
    the **livespec HUB tenant** (matching how the original 8 tracks were filed). So a
    hub-tenant slice whose WORK is in a sibling repo (orchestrator/runtime/git-jsonl/
    drivers) canNOT be cleanly factory-dispatched: `--repo=livespec` would build in
    the WRONG repo; `--repo=<sibling>` can't find the hub-tenant item. **Only CORE
    slices (work-repo == hub tenant, e.g. `livespec-2j46re`) dispatch cleanly
    as-filed.** This is a genuine architectural question about the thread's
    dispatch/tenanting model — surfaced to the maintainer, NOT self-resolved. Options
    under consideration: (1) re-file each sibling repo's factory slices into THAT
    repo's own tenant (the factory's per-repo model; the `file_approved_slices`
    cross_repo path exists for exactly this); (2) scoped-agent per-repo dispatch
    reading the spec from the hub; (3) a factory cross-repo-tenant enhancement.
    RECOMMEND (1). Until decided, do NOT dispatch sibling-repo slices.
- **2026-07-10 — DISPATCH-MODEL DECIDED: re-tenant sibling slices into per-repo
  tenants (maintainer chose option 1).** Each sibling repo's factory slices must be
  filed in THAT repo's OWN beads tenant (the hub epic `livespec-i5ebqd` stays as
  cross-tenant rollup, membership narrated). The maintainer's choice authorizes the
  cross-tenant writes. **Confirmed sibling tenant prefixes** (reachable via the fleet
  wrapper, `cd /data/projects/<repo>` then `bd`): orchestrator **`bd-ib`**, runtime
  **`livespec-runtime`**, git-jsonl **`bd-gj`**, driver-claude
  **`livespec-driver-claude`**, console **`livespec-console-beads-fabro`**,
  driver-codex prefix UNSET (empty tenant — set on first create). CORE slices stay in
  the hub tenant (work-repo == hub = correct).
  - **⚠ CLEANUP OWED:** the 4 orchestrator slices I filed via `groom` are in the
    WRONG (hub) tenant: `livespec-y4f7hp` / `livespec-tlvsn4` / `livespec-my2s7k` /
    `livespec-umabdn`. Re-file their equivalents into the **`bd-ib`** tenant
    (`cd /data/projects/livespec-orchestrator-beads-fabro`; preserve the A→B→C→D
    chain + scope/acceptance from the Progress log above / grooming §5), THEN CLOSE
    the 4 hub copies with a "re-tenanted to <bd-ib id>" note. `livespec-236f` is
    already regroomed-out (hub) — do NOT try to re-groom it; file the bd-ib slices
    fresh (bd create with chain deps, or the capture-work-item/append_work_item path
    run with cwd=orchestrator). Do NOT dispatch the hub-tenant orchestrator copies.
  - **Re-tenant procedure (per sibling repo):** run the filing with
    `cwd=/data/projects/<repo>` so `resolve_store_config` picks THAT tenant; narrate
    epic membership (no cross-tenant `depends_on` to the hub epic); keep intra-repo
    chain deps within the tenant. Core (`livespec-2j46re`/`7jcdfk`/`txn2bq`) needs NO
    re-tenant. dev-tooling (`livespec-iily`) is host-side (not factory) — may stay a
    hub tracking item.

## The next action

> **Phase 0 is DONE + ACCEPTED (fleet at dev-tooling v0.35.2). Phase 1 is GROOMED
> with a CORRECTED model — read `research/phase1-grooming.md` FIRST; it is the
> authoritative slice spec and supersedes the ordering in `phase1-inventory.md`.**
> All 7 tracks are READY (acceptance + scope set on the ledger). The two
> pre-dispatch gate-findings are BOTH resolved (partition-vs-flip correction;
> footgun per-copy). What remains is DISPATCH + the flips.
>
> **The corrected model (grooming note §2, load-bearing):** Phase 1 fixes only the
> NON-partition code violations (keyword_only `*,`; all_declared `__all__`;
> no_write→`io/` surface; no_lloc_soft + file_lloc split/exempt; no_inh/priv/global
> where present) while files stay newly_covered/WARN. Declaring role config is
> NOT a Phase-1 step — it claims-for-partition AND flips severity to hard in one
> action, so it is the reviewed **Phase-2** flip. Do NOT groom a "partition-config
> first" slice; partition WARN resolves at the flip.
>
> **DISPATCH-MODEL DECIDED (Progress log 2026-07-10): re-tenant sibling slices into
> per-repo tenants.** Concrete next steps, in order:
> 1. **Dispatch CORE now** (cleanly dispatchable, work-repo == hub tenant):
>    `drive --action impl:livespec-2j46re --repo /data/projects/livespec` (9bym-A
>    mechanical), then 9bym-B `livespec-7jcdfk` → 9bym-C `livespec-txn2bq`. This
>    validates the factory flow while re-tenanting proceeds.
> 2. **Re-tenant the orchestrator slices** (CLEANUP OWED — Progress log): re-file the
>    A→B→C→D chain into the **`bd-ib`** tenant (`cwd=/data/projects/livespec-orchestrator-beads-fabro`),
>    then CLOSE the 4 hub copies (`y4f7hp`/`tlvsn4`/`my2s7k`/`umabdn`). Dispatch the
>    bd-ib mechanical slice.
> 3. **Groom + re-tenant** runtime (`livespec-8x7d`→tenant `livespec-runtime`) and
>    git-jsonl (`livespec-t4e0`→tenant `bd-gj`): split each into mechanical + file_lloc
>    slices (same pattern), file into their tenants, dispatch.
> 4. **Drivers + console** (`gqte`/`v74p`/`q7bx`): Slice0 = wire full suite (DECIDED),
>    re-tenant into `livespec-driver-claude` (claude) / driver-codex tenant (prefix
>    UNSET — set on first create) / `livespec-console-beads-fabro`, then fix + flip.
>
> **The big tracks are GROOMED** (both regroomed-out into ready layered slices —
> Progress log 2026-07-10 has every id). Ready NOW:
> - **`livespec-2j46re`** (9bym-A core mechanical) — CLEANLY DISPATCHABLE (work-repo
>   == hub tenant): `drive --action impl:livespec-2j46re --repo /data/projects/livespec`.
>   Then 9bym-B `livespec-7jcdfk` → 9bym-C `livespec-txn2bq`.
> - **`livespec-y4f7hp`** (236f-A orchestrator mechanical) READY but BLOCKED on the
>   dispatch-model decision (sibling tenant). Then B/C/D (`tlvsn4`/`my2s7k`/`umabdn`).
> - `livespec-8x7d` runtime (53), `livespec-t4e0` git-jsonl (37) — still COARSE
>   single tracks (mechanical + a little file_lloc mixed); groom each into
>   mechanical + file_lloc slices before dispatch (same pattern), and re-tenant.
> Re-measure each sandbox against the current pin with the dev-tooling venv python
> (NEVER a repo's own stale venv). NOTE: because newly_covered diagnostics are WARN
> (exit 0), green `just check` does NOT prove the WARN dropped — acceptance MUST
> measure the WARN delta. Each slice PR: green `just check` + independent adversarial
> NO-BLOCKERS review before acceptance (auto-merge repos: land→review→fix-forward).
>
> **HOST-SIDE maintainer-driven (NOT factory):** `livespec-iily` dev-tooling (40)
> AND the file_lloc flip-mechanism follow-up (make its legacy tree config-driven so
> non-core repos can flip file_lloc — grooming note §2 residual); each repo's
> Phase-2 role-declaration flip.
>
> **DISPATCH the thin-repo tracks (wiring DECIDED 2026-07-10 = full suite):**
> `livespec-gqte` driver-codex (13), `livespec-v74p` driver-claude (9), and
> `livespec-q7bx` console (0). Each begins with **Slice0 = wire the full
> applies-to-all structural suite into justfile + CI** (via
> `check-aggregate-completeness`, the app-repo mechanism), THEN fix the repo's
> WARN, THEN flip. Console's Slice0 is wire-only → its flip is a verified
> empty-universe no-op. FACTORY-SAFE.
>
> **Then Phase 2 per repo** — declare the role layout (= claim-for-partition +
> severity flip) the moment the repo is warning-clean, after an independent
> NO-BLOCKERS review. Severity only — NO escape hatch (`.ai/ci-gate-discipline.md`).
> The flip lever is the committed pyproject role declaration (OQ3 largely resolved,
> grooming note §2); the file_lloc residual (non-core) needs the dev-tooling
> follow-up first.
>
> Do NOT archive this thread until every in-scope repo is warning-clean AND flipped
> to hard-fail, and the maintainer explicitly accepts archival.
