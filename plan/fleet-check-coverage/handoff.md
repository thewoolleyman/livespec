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
  bump-pin wiring hotfix (see Progress log). The `livespec` template-projection
  repair landed in PR #982. The next action is Phase 1 burndown planning.
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

## The next action

> **Phase 0 — REROUTE, continuing (WARN-only). PR1 (`file_lloc`), PR2 (7 `source_trees` checks),
> PR2b (reshape), and PR3 (remaining stragglers + `tests_tree_prefix` guard) are DONE + ACCEPTED
> (through PR3, fleet reached v0.34.5). PR4 (`check-partition-completeness`) is LANDED in `livespec-dev-tooling`
> and released as v0.35.1 after the bump-pin wiring hotfix.** The shared
> `resolve_check_universe()` (OWNS root-resolution, returns `(root, universe)`) + delta-WARN
> (legacy = `config.source_trees` / `_LEGACY_HARDFAIL_TREES` / check-specific legacy classifiers)
> is the established pattern.
>
> **Next: Phase 1** — per-repo burndown in parallel through the factory; `groom` the epic into one
> ready track per repo. Before filing those tracks, read the live ledger and print the
> `Epic · Track (repo) · Status · %Complete` table. NOTE (corrected): for the 7
> config-driven checks EVERY non-dev-tooling repo is currently WARN-only
> (empty/nonexistent `source_trees`), so their Phase-1 = bring the whole first-party
> universe warning-clean, and DECIDE per repo whether to set `source_trees` (to hard-gate
> a subtree earlier) or rely on the Phase-2 whole-universe flip. Do NOT link a child to
> the epic via `depends_on` (an OPEN-epic edge perpetually blocks the child via
> `lifecycle._entry_blocks`) — narrate epic membership in the description.
>
> Each PR: release + fan-out, confirm LIVE (not just green CI), independent adversarial review of the
> merged commit before recording acceptance. Expect auto-merge on green; `refactor:` DOES cut a
> release here.
>
> **Then Phase 2** — flip warn→fail per repo the moment it is warning-clean, after an independent
> adversarial NO-BLOCKERS review. Severity only — NO new escape hatch (`.ai/ci-gate-discipline.md`).
> The per-repo flip mechanism (env lever vs committed marker) is still-open OQ3. PREREQUISITE: the
> aggregate `check:` wiring is non-uniform — `livespec-console-beads-fabro` + both Driver repos do
> NOT wire the structural checks into their justfiles, so driver-hook coverage only bites in their
> CI once the wiring/fan-out lands.
>
> Do NOT archive this thread until every in-scope repo is warning-clean AND flipped to hard-fail,
> and the maintainer explicitly accepts archival.
