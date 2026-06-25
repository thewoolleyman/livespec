# Hand-off: make core's release gate green (heading-coverage TODOs)

**Standing hand-off — do not delete until `check-no-todo-registry` is green
in release-gate mode.** Each session that advances this MUST refresh this
file and the beads state before stopping.

## State

core's `release-tag.yml` release gate runs `check-no-todo-registry`, which
fails while any `test: "TODO"` entry remains in `tests/heading-coverage.json`.
It does **not** block releases (the gate runs on `v*` tag push, after the
release publishes), but it leaves a red check on every release. The
maintainer **accepted the red gate** (2026-06-25) and wants it resolved ASAP.

Down from 14 → **9 remaining** (5 already mapped). There is **no exemption
sentinel** in the check — the only honest clear is a real test id. The
`red_green_replay` hook blocks adding a *unit* test for already-passing
behavior, so each remaining item is a **new check (genuine TDD)**, a **map to
an existing test**, or a **dependency**.

Tracking: **`livespec-besm`** (P1) and its children **`.1` / `.2` / `.3`**
(ready, P1). Full per-heading plan lives in the `livespec-besm` notes.

## Do (in priority order)

1. **Dispatch the 3 ready P1 children** (factory-safe — core, TDD/map):
   - `livespec-besm.1` — author a `no-renderer-vendoring` check (covers
     `## Renderer non-vendoring`).
   - `livespec-besm.2` — author a `CLI-shape-conformance` check (covers
     `## CLI shape conventions`; regroom if the rule exceeds one check).
   - `livespec-besm.3` — add `pytest.mark.integration` to the existing
     `tests/dev-tooling/checks/test_behavior_scenario_link.py` and map
     `## Behavior clause lacking a scenario link is surfaced`.
   Each child flips its heading's `TODO` → the new/mapped test.
2. **Reference discipline** (`## Reference discipline`) — resolved by
   `livespec-e58y` (author `no_cross_spec_reference` +
   `no_spec_section_citation` checks). Make e58y's acceptance include flipping
   the heading-coverage entry.
3. **e2e-dependent** (`## CLI end-to-end harness contract`,
   `## Error path 3 — version-contiguity gap in history`) — both need the
   `tests/e2e-cli/` harness wired (its source `.py` is not git-tracked, only
   stale `.pyc`). **No work-item tracks this yet — file one**, build the
   harness, then add the e2e tests and map the two headings.
4. **Groom** `## Contract + reference implementations architecture` — broad;
   identify the mechanical rule (likely a diagram-single-source check) first.
5. **Decision-gated** (`## Interactive dialogue ownership (orchestrator-side)`,
   `## Doctor per-finding disposition dialogue`) — genuinely non-core
   (orchestrator / driver-claude concerns). These can go green **only** via an
   exemption mechanism the maintainer declined, or a cross-repo test. Surface
   to the maintainer when full green is wanted; do not fabricate a core test.

## Done when

`LIVESPEC_FAIL_IF_HEADING_COVERAGE_TODOS_EXIST=true just check-no-todo-registry`
exits 0. Then close `livespec-besm` + children and delete this file.

## Discipline

Worktree → PR → rebase-merge per repo; `mise exec -- git …`; never
`--no-verify`; new checks follow Red-Green-Replay; JSON/marker-only edits use
`test:`/`chore(tests):` and skip the ritual. Never force a heading green with
a fabricated or non-exercising test id.
