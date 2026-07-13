# Phase-1 WARN inventory — final accurate measurement 2026-07-09

The per-repo Phase-0 `newly_covered` WARN inventory that scopes the Phase-1
burndown. Every repo measured with ONE consistent, trustworthy method:

    DTPY=/data/projects/livespec-dev-tooling/.venv/bin/python   # v0.35.1
    cd /data/projects/<repo>
    for c in <14 git-derived checks>; do
      "$DTPY" -m livespec_dev_tooling.checks.$c 2>&1 | grep -c '"newly_covered": true'
    done

Running dev-tooling's OWN venv python (pinned v0.35.1) with cwd = the target repo
sidesteps the stale-local-venv trap (see caveat) — the check resolves its
universe from cwd's git index while executing current check code.

## Measurement caveat — DO NOT trust a repo's own local venv

Every fleet repo's local `.venv` was stale at measurement time (behind the
v0.35.1 pin — `uv sync` had not run since the fan-out). Measuring a repo with its
OWN venv gave WRONG numbers, and a wrong number here already produced one wrong
conclusion mid-session:

- The orchestrator's own venv sat between v0.34.2 and v0.34.5 — file_lloc
  rerouted (correct 16), but no_write_direct NOT yet rerouted and
  partition_completeness absent. Measured with its own venv, no_write_direct read
  **0** and I briefly concluded the handoff's "69" was stale. Re-measured with the
  v0.35.1 dev-tooling venv, no_write_direct is **69** — the handoff was right.
- runtime's own venv was v0.33.5 (predates ALL newly_covered machinery) → false
  all-zero.
- both drivers' own venvs were v0.33.5 → false all-zero.

**Lesson:** for Phase-1 measurement and for each dispatched sandbox, measure
against the pinned v0.35.1 dev-tooling code, never a possibly-stale local venv.
The factory sandbox does this by construction (fresh clone + `uv sync`).

## The fleet Phase-1 table (all counts = newly_covered WARN, v0.35.1)

| Repo | file_lloc | partition | all_declared | main_guard | kw_only | no_write | soft_warn | global | no_inh | priv | **TOTAL** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **livespec (core)** | 0 | **120** | 17 | 10 | 8 | 10 | 10 | 1 | 0 | 0 | **176** |
| **orchestrator-beads-fabro** | 16 | 6 | 26 | 10 | 29 | **69** | 3 | 0 | 4 | 1 | **164** |
| **dev-tooling** | 17 | 1 | 1 | **64** | 6 | 8 | 7 | 0 | 0 | 0 | **104** |
| **runtime** | 1 | 27 | 2 | 3 | 19 | 0 | 0 | 0 | 3 | 0 | **55** |
| **orchestrator-git-jsonl** | 3 | 12 | 11 | 4 | 7 | 2 | 0 | 0 | 0 | 0 | **39** |
| **driver-codex** | 1 | 0 | 2 | 2 | 8 | 2 | 0 | 0 | 0 | 0 | **15** |
| **driver-claude** | 0 | 0 | 2 | 1 | 6 | 1 | 0 | 0 | 0 | 0 | **10** |
| **console-beads-fabro** | — | — | — | — | — | — | — | — | — | — | **0** (empty) |

Checks with zero WARN fleetwide: assert_never_exhaustiveness, comment_line_anchors,
match_keyword_only. Grand total ≈ **563** newly_covered WARN across the fleet.

## Per-check character (what the burndown work IS)

- **partition_completeness** (config, mechanical): a file is "claimed" by
  declaring it in a role key (`source_trees`/`io_trees`/`commands_trees`/
  `pure_trees`/`covered_trees`/`source_tree_prefixes`…) in
  `[tool.livespec_dev_tooling]`. Core (120), runtime (27), git-jsonl (12),
  orchestrator (6) omit or under-declare the role keys → files unclaimed. The
  drivers declare `source_tree_prefixes` for their hooks → 0. FIX: restate the
  repo's role layout in pyproject. One edit per repo, unblocks the largest bucket.
- **main_guard** (per-file, but SEE DESIGN FLAG): dev-tooling shows **64** —
  nearly every library module. ⚠️ This is the load-bearing design question: does
  main_guard correctly apply to pure library modules (which legitimately have no
  `if __name__ == "__main__"`), or does routing it through the whole git-derived
  universe OVER-apply it? If over-applied, the fix is in the CHECK
  (dev-tooling), and it shrinks Phase-1 scope fleetwide. Resolve this BEFORE
  burning down 64 dev-tooling main_guard "violations" by adding pointless guards.
- **keyword_only_args** (per-file): concentrated in `livespec_footgun_guard.py`,
  a hook COPIED into core / both drivers / dev-tooling — same violations in each.
  Fix the canonical copy once and propagate, rather than 4 independent fixes.
- **no_write_direct** (per-file): orchestrator **69** (route stdout/stderr writes
  through the io/ exemption surface), core 10, dev-tooling 8, others small.
- **all_declared** (per-file): add `__all__`. Spread across repos.
- **file_lloc** (refactor, design-laden): orchestrator 16 (dispatcher.py **1586**,
  _dispatcher_plan.py 730, _dispatcher_reflector_oob.py 719, + 13 more),
  dev-tooling 17, git-jsonl 3, driver-codex 1 (footgun_guard 263). Each
  over-ceiling file is a split-vs-**exempt-with-justification** judgment (the
  check permits a named, visible, justified exclusion — design.md).

## Factory-safety of each track (dispatch routing)

- **dev-tooling (104)** and its check-design questions are **host-side
  maintainer-driven**, NOT factory-dispatched — same rule as the Phase-0
  mechanism: dev-tooling is the shared enforcement package that fans out to
  everyone, not factory-safe app work.
- **livespec core (176)** — dogfood repo; its self-machinery + spec CLIs. Mostly
  factory-safe burndown, but the partition-config restate touches core's own
  role definition (the layout others mirror) → maintainer-reviewed.
- **orchestrator-beads-fabro (164), git-jsonl (39), runtime (55), drivers
  (10/15)** — factory-safe app/library burndown; dispatch through the janitor
  gate. The orchestrator's big-module splits are the one design-laden slice.
- **console (0)** — nothing to do; Phase-2 flip is a no-op.

## Two findings to resolve before/at dispatch (surfaced to maintainer)

1. **main_guard over-application (design).** 64 dev-tooling library modules
   flagged. Decide: tighten the main_guard newly-covered universe to entry-point
   scripts only, OR accept that library modules must carry a guard/exemption.
   Fleet-wide scope impact.
2. **Shared-hook single-source.** `livespec_footgun_guard.py` (keyword_only_args
   + others) is copied into ≥4 repos with identical violations. Decide: fix once
   at the canonical source and propagate, vs. per-repo burndown.
