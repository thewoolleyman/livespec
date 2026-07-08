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
  **v0.34.1**, and is the substrate the next action builds on:
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
  Progress log). The remaining **12 applies-to-all checks + the empty-walk guard +
  the partition meta-check** are the next action.
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
| `livespec` (core) | hub / dogfood | 120 | verify no regression |
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

**Pin / fan-out status (CORRECTED 2026-07-08 after PR1).** `livespec-dev-tooling` is
at **v0.34.2** (carries the `file_lloc` reroute), and the fan-out is **healthy —
ALL seven consumers are pinned to v0.34.2** (`livespec`, both orchestrators, both
Drivers, `livespec-runtime`, `livespec-console-beads-fabro`), verified against each
repo's `origin/master` after `git fetch`. An earlier note in this handoff claimed
four repos were "stranded at v0.33.5" — that was a **FALSE ALARM from stale local
`origin/master` refs** (reading `git show origin/master:` in a sibling clone WITHOUT
fetching it first shows a stale ref; the bump-pin PRs had in fact merged, e.g.
`livespec-runtime` #151→v0.34.2). **Lesson: `git fetch` a sibling clone before
reading its `origin/master` for cross-repo state.** Because every consumer now pins
v0.34.2, the reroute's WARN coverage is LIVE fleet-wide. Live universe confirmed via
the shipped code: `livespec-driver-claude` universe=2 (both hooks covered),
`livespec-driver-codex` universe=3 (all hooks covered) — the Drivers are NOT
codeless; `livespec-console-beads-fabro` universe=0 (`has_first_party_py=False` —
genuinely codeless, passes on empty); `livespec-orchestrator-git-jsonl`=40,
`livespec-runtime`=27 (matching the fleet table). No fan-out fix is needed.

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

## The next action

> **Phase 0 — REROUTE, continuing (WARN-only), the next PR in `livespec-dev-tooling`.**
> **PR1 (`file_lloc`) is DONE + ACCEPTED (v0.34.2)** — see Progress log. The
> **delta-WARN** severity model it established is the pattern for EVERY remaining
> applies-to-all reroute: git-derived universe via `iter_first_party_py_files`;
> files under `_LEGACY_HARDFAIL_TREES` keep today's severity; newly-covered files
> emit at WARN (exit 0). MAINTAINER-DRIVEN host-side; expect auto-merge on green CI.
> Read `research/check-inventory.md` §2 for the per-check classification.
>
> **Remaining applies-to-all reroutes (12), in small PRs — recommended grouping:**
> - **PR2 — the `config:source_trees` family (7, one coherent batch, same universe
>   pattern):** `all_declared`, `assert_never_exhaustiveness`, `global_writes`,
>   `keyword_only_args`, `match_keyword_only`, `no_inheritance`, `private_calls`.
>   Introduce the **empty-walk guard as a shared helper** here (now NON-vacuous:
>   these resolve from config trees that can be empty-while-code-exists — the exact
>   original bug). Guard: universe empty AND `has_first_party_py` → error; genuinely
>   codeless (console) → pass. **Address the subdir-invocation residual** (Fable
>   PR1 finding): a check invoked from a repo subdirectory walks zero and exits 0
>   silently, and `has_first_party_py` on the same cwd would not catch it — resolve
>   the git repo ROOT (e.g. `git rev-parse --show-toplevel`) rather than trusting
>   `cwd`, so the universe and the guard are both root-anchored.
> - **PR3 — the raw-`rglob` hardcoded + hybrid stragglers:** `main_guard`,
>   `rop_pipeline_shape`, `comment_line_anchors`, and `no_write_direct` (HYBRID —
>   git-derived universe, keep `commands_trees`/`supervisor_entry_files` as
>   write-permitted exemptions). Plus `no_lloc_soft_warnings` — STILL FAIL-OPEN
>   (Fable PR1 finding); it carries the `LIVESPEC_FAIL_IF_LLOC_SOFT_WARNINGS_EXIST`
>   release lever, so its newly-covered set MUST emit at WARN regardless of the
>   release context (delta-WARN), or dev-tooling's own release gate FAILs on
>   newly-covered soft-band files — the release-lever trap.
> - **PR4 — the partition-completeness meta-check** (new `checks/` module): every
>   first-party `.py` is claimed by exactly one role OR a named exclusion; unclaimed
>   → error naming the file (WARN this phase). NOTE: a new `checks/<name>.py`
>   auto-joins `canonical_check_slugs()`, so it requires wiring `check-<slug>` into
>   EVERY consumer justfile — the fan-out `bump-pin` reconciles the `check:` block
>   (precedent `livespec-dev-tooling-adqmnm`, "the fan-out writes the wiring").
>
> Exemptions unchanged across all: `_vendor/` + test tree (+conftest) +
> `@generated`-marked + `templates/**`; each repo's OWN hooks ARE covered. Each PR:
> release + fan-out (`bump-pin` rewrites pins + reconciles `check:`), then confirm
> LIVE (not just green CI) — orchestrator WARNS on its product code,
> `livespec-console-beads-fabro` PASSES on empty, Driver hooks covered, `just check`
> stays exit 0 fleet-wide — and an independent adversarial review of the merged
> commit before recording acceptance.
>
> **Then Phase 1** — the per-repo burndown, in parallel through the factory
> (over-ceiling refactors, other check findings, claim/exempt unclaimed files).
> `groom` the epic into one ready track per repo. NOTE: do NOT link a child to the
> epic via `depends_on` — an OPEN-epic edge perpetually blocks the child
> (`lifecycle._entry_blocks`); narrate epic membership in the description and
> reserve `depends_on` for genuine cross-item blockers.
>
> **Then Phase 2** — flip warn→fail per repo the moment it is warning-clean, after
> an independent adversarial review (companion prompt) returns NO-BLOCKERS. The
> flip is severity only — NO new escape hatch (`.ai/ci-gate-discipline.md`). The
> flip mechanism itself (env lever vs committed marker) is still-open OQ3.
>
> Do NOT archive this thread until every in-scope repo is warning-clean AND
> flipped to hard-fail, and the maintainer explicitly accepts archival.
