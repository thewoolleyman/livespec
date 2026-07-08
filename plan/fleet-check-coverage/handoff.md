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
  These are a PURE ADDITION — **not yet wired into any check**. Rerouting is the
  next action.
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
`iter_first_party_py_files` (v0.34.1), verified 2026-07-08 — authoritative over
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
    thread's branch; leave it for that session/maintainer to reap.

## The next action

> **Phase 0 — REROUTE increment (WARN-only), the next PR(s) in `livespec-dev-tooling`.**
> The foundation primitive is landed (v0.34.1); now wire it in. MAINTAINER-DRIVEN
> host-side; expect auto-merge on green CI. Read `research/check-inventory.md` §2
> for the exact per-check classification. Deliverables:
> - Reroute the **13 applies-to-all checks** to derive their universe from
>   `iter_first_party_py_files` instead of hardcoded trees / `config.covered_trees`
>   / `config.source_trees`: `file_lloc` (drop `_COVERED_TREES`),
>   `no_lloc_soft_warnings`, `all_declared`, `assert_never_exhaustiveness`,
>   `global_writes`, `keyword_only_args`, `match_keyword_only`, `no_inheritance`,
>   `private_calls`, `comment_line_anchors`, `main_guard`, `rop_pipeline_shape`,
>   and `no_write_direct` (HYBRID — git-derived universe, keep
>   `commands_trees`/`supervisor_entry_files` as write-permitted exemptions). Six
>   of these currently raw-`rglob` hardcoded trees and bypass `load_config` —
>   reroute them through the shared choke point.
> - Add the **empty-walk guard**: a check whose resolved universe is empty in a
>   repo with a NON-empty first-party set is an error; a genuinely-empty repo
>   (`livespec-console-beads-fabro`) PASSES. Use `has_first_party_py`.
> - Add the **partition-completeness meta-check** (new `checks/` module). NOTE:
>   adding a new `checks/<name>.py` auto-joins `canonical_check_slugs()`, so it
>   requires wiring `check-<slug>` into EVERY consumer justfile (the fan-out
>   `bump-pin` reconciles the `check:` block — precedent
>   `livespec-dev-tooling-adqmnm`, "the fan-out writes the wiring").
> - **⚠ Release-lever TRAP (why this is staged, WARN-only):**
>   `checks/no_lloc_soft_warnings.py` reads `LIVESPEC_FAIL_IF_LLOC_SOFT_WARNINGS_EXIST`,
>   which **CI/release sets to `true`**. Rerouting it (and any check gaining a
>   fail-lever) to the full 88-file universe would make dev-tooling's OWN release
>   gate FAIL on newly-covered soft-band files — blocking the release the fan-out
>   needs. In Phase 0, ALL new/changed diagnostics from the rerouted universe MUST
>   emit at WARN (exit 0) regardless of the release context. Decide deliberately
>   how the lever behaves for the newly-covered set (the Phase-2 per-repo flip is
>   OQ3, still open).
> - Exemptions unchanged: `_vendor/` + test tree (+conftest) + `@generated`-marked
>   + `templates/**`; each repo's OWN hooks ARE covered.
> - Release + fan-out: cut a `livespec-dev-tooling` release; `bump-pin` rewrites
>   every consumer's pin AND reconciles each consumer's `check:` canonical block.
> - Confirm LIVE (not just green CI): `livespec-orchestrator-beads-fabro` WARNS on
>   `dispatcher.py` + siblings; `livespec-console-beads-fabro` PASSES on empty; the
>   Driver hooks are covered; `just check` stays exit 0 fleet-wide.
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
