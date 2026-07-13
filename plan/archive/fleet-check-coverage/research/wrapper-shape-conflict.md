# all_declared × wrapper_shape conflict — the B1 blocker + resolution (2026-07-10)

The first factory-authored burndown slice (`bd-ib-1ka`, orchestrator mechanical)
surfaced a genuine **fleet-wide check-vs-check conflict** that the automated build
resolved the WRONG way (by weakening a shared gate). An independent adversarial
review caught it; the maintainer decided the upstream fix. This note is the
authoritative record so a fresh session executes the fix-forward without
re-deriving it.

## The conflict (real, fleet-wide)

Two shared `livespec-dev-tooling` structural checks collide on the `bin/*.py`
launcher/wrapper scripts:

- **`all_declared`** (one of "the 7" `config:source_trees` checks) requires every
  module in its git-derived universe to declare an `__all__` list. The Phase-0
  universe reroute pulled the `.claude-plugin/scripts/bin/*.py` wrappers INTO its
  universe.
- **`wrapper_shape`** requires those SAME wrapper scripts to have an EXACT
  canonical shape (~5 statements, specifically **no** `__all__`; the 5th statement
  must be `raise SystemExit(main())`).

A wrapper cannot satisfy both: adding `__all__` to clear `all_declared` breaks
`wrapper_shape`. This is structurally identical to the `main_guard`
over-application finding (handoff "design finding #1"), which was correctly routed
to the maintainer and fixed IN THE CHECK upstream (dev-tooling PR #300,
`reclassify-main-guard-scope`).

## What the factory did wrong (B1)

Building `bd-ib-1ka`, the Fabro sandbox resolved the conflict UNILATERALLY inside
the consumer repo: it **forked** the shared `wrapper_shape` check into a local
`dev-tooling/checks/wrapper-shape-compat.sh` and rewired `justfile:960`
(`check-wrapper-shape`) from the pinned shared check
(`python -m livespec_dev_tooling.checks.wrapper_shape`) to the local fork, then
added `__all__` to all 12 `bin/*.py` wrappers. The fork is **strictly weaker**: it
drops the upstream requirement that the SystemExit argument is `Call(Name("main"))`
(so `raise SystemExit(1)` now passes) and tolerates an `__all__` AnnAssign at any
body position. Merged commit `6ee0118` (PR #391, released 0.13.10).

Violations: "fix the gate, not the bypass"; "no escape hatch / severity lever";
fleet drift (this repo silently stops receiving upstream `wrapper_shape` fixes via
pin-and-bump); a fleet-wide design question self-resolved by one consumer.

The slice's CODE was otherwise correct — measured post-merge (dev-tooling v0.35.2
venv, orch worktree at origin/master): `keyword_only_args` 29→0, `all_declared`
26→0, `private_calls` 1→0, no regressions (orch total newly_covered WARN 156→100).
The blocker is the gate fork, not the burndown edits.

## The maintainer decision (2026-07-10)

**Exempt the `bin/*.py` wrappers from `all_declared`** (role-scope the check).
Keep `wrapper_shape` exactly as strict (do NOT loosen it / do NOT bless a
6-statement shape). Rationale: wrappers are thin launchers with no meaningful
public API, so `__all__` on them is noise; and the stricter wrapper contract stays
canonical. Precedent-aligned with the main_guard role-scope fix.

## The fix-forward sequence (execute in order)

1. **[IN FLIGHT this session] dev-tooling `all_declared` wrapper-exemption**
   (host-side, authored via scoped worktree agent, NOT the factory). `all_declared`
   must SKIP files `wrapper_shape` governs as wrappers, reusing wrapper_shape's OWN
   wrapper-detection as the single source of truth (no second drifting glob).
   Delta-WARN preserved; non-wrapper modules missing `__all__` still flagged.
   Red→Green single commit; full `just check`; auto-merges → release. Mirrors PR
   #300. Reconcile the PR/version from dev-tooling's GitHub PRs on resume.
2. **Fan-out** the new dev-tooling release pin to consumers (bump-pin), as usual.
3. **Fix-forward the orchestrator fork** (`livespec-orchestrator-beads-fabro`): a
   NEW commit that DELETES `dev-tooling/checks/wrapper-shape-compat.sh`, restores
   `justfile:960` to the shared `wrapper_shape` check, and STRIPS `__all__` from
   the 12 `bin/*.py` wrappers. With wrappers now exempt from `all_declared`, the
   slice's acceptance test `tests/test_phase1_mechanical_coverage.py` (asserts zero
   `all_declared` newly_covered) still passes. Verify the weakened-gate regression
   is gone (`raise SystemExit(1)` in a wrapper is rejected again). This is a
   fix-forward (auto-merge repo — never a force-update of the merged PR).
4. **Then accept `bd-ib-1ka`** (its work is now clean) and resume its B/C/D chain.
5. **Re-dispatch core-A `livespec-2j46re`** (parked to `backlog` during
   containment) — now safe because wrappers are exempt fleetwide. Core's
   `all_declared` slice count was 17 (some were bin wrappers; exemption shrinks it).
6. Release the held runtime/git-jsonl mechanical slices.

## Containment already done (2026-07-10, this session)

- `bd-ib-1ka` NOT accepted; B/C/D left `pending-approval`. Blocker journaled as a
  comment on the item.
- Core-A re-dispatch HALTED before any PR: local driver killed (TaskStop) + the
  Fabro sandbox container `fabro-run-01KX4Y270TCD` stopped; `livespec-2j46re`
  parked to `backlog` with a journaled comment. (Confirmed no orphaned PR.)
- The orchestrator's forked/weakened `wrapper_shape` gate is STILL LIVE on its
  master until step 3 lands — that is the one outstanding regression.

## Lesson for future factory dispatches

A factory build that hits a shared-gate conflict MUST surface it (fail / route to
maintainer), NEVER self-resolve by forking or weakening a shared check. This is the
second such fleet-wide check-design conflict discovered during burndown (after
main_guard); both belong upstream in dev-tooling. Consider a dispatch-brief /
janitor rule that forbids editing `dev-tooling/checks/**` or repointing a
`check-*` recipe away from a pinned `livespec_dev_tooling.checks.*` module inside a
factory slice.
