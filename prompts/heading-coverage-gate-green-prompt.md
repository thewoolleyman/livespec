# Hand-off: make core's release gate green (heading-coverage TODOs)

**Standing hand-off — do not delete until `check-no-todo-registry` is green
in release-gate mode.** Each session that advances this MUST refresh this
file and the beads state before stopping.

## State (2026-06-26)

core's `release-tag.yml` release gate runs `check-no-todo-registry`, which
fails while any `test: "TODO"` entry remains in `tests/heading-coverage.json`.
It does **not** block releases (the gate runs on `v*` tag push, after the
release publishes), but it leaves a red check on every release. The
maintainer **accepted the red gate** (2026-06-25) and wants it resolved ASAP.

Down from 14 → 5 → **2 remaining**. Both remaining TODOs are the
sibling-owned headings handled by **`livespec-besm.6`** (see below).

Resolved since the 5-remaining mark (all merged):
- **besm.4** — `## Error path 3 — version-contiguity gap`: implemented the
  `version_contiguity._evaluate` fail arm (a real latent always-pass bug) +
  unit fail-arm + integration-tier e2e `tests.e2e.test_doctor_version_contiguity`
  (PR #604).
- **besm.5** — `## Workflow planes and the Planning Lane`: terminology-guard
  test (console ≠ Driver) on core's own spec.md (PR #605).
- **e58y** — `## Reference discipline`: authored + registered the two
  doctor-static checks `doctor-no-cross-spec-reference` +
  `doctor-no-spec-section-citation-in-code` (PR #620). This required a
  large prerequisite **retroactive sweep**: ~385 in-comment/docstring
  `§"…"` citations removed across the package (#608/#610/#611) and
  tests/+dev-tooling (#615), because `check-doctor-static` runs the checks
  against core itself in `just check` + CI. The new cross-spec-reference
  check **surfaced a real stale citation** in `spec.md` (a renamed
  `contracts.md` heading), fixed via the governed **revise → v145** (#617).
  Side fix in #615: repaired a CI-masked stale `test_git_hook_wrapper.py`
  left by the concurrent M2 wrapper rewrite (`4c7849a`); also flagged that
  `check-coverage`'s `.coverage`-reuse can mask a deterministic test
  failure from the gate.

**Maintainer directives still in force.** NO coverage escape hatch — each
heading is tested HERE or its real test is added in the sibling repo that
owns it (relocate). NO exemption sentinel. Never force a heading green with
a fabricated or non-exercising test id.

## Remaining 2 — `livespec-besm.6` (P2 epic, RELOCATE decided 2026-06-26)

Both remaining headings are in core's `SPECIFICATION/contracts.md` and are
genuinely sibling-owned. **Maintainer decision (2026-06-26): RELOCATE the
contract text ENTIRELY into the owning sibling repo — NO one-line core
pointer.** Sequence each as: (a) add the section to the owner's spec via
its own propose-change/revise loop + co-edit its `tests/heading-coverage.json`;
(b) add the real test there; (c) on CORE, one `/livespec:revise` removing
the heading from `contracts.md` + dropping its heading-coverage entry.

1. **`## Interactive dialogue ownership (orchestrator-side)`** (contracts.md)
   → OWNER **`livespec-orchestrator-beads-fabro`** (`/data/projects/livespec-orchestrator-beads-fabro`,
   livespec-governed: own `SPECIFICATION/` + `tests/heading-coverage.json`).
   The load-bearing invariant: orchestrator front-ends are
   orchestrator-internal, the Driver does NOT depend on them, and they MUST
   NOT call back into the Driver. Real test = a **zero-dependency test**
   (the consent-dialogue front-end skills import/call no Driver). Tractable.
2. **`## CLI end-to-end harness contract`** (contracts.md, a 6-point contract)
   → OWNER **`livespec-driver-claude`** (the contract is on the Claude Driver
   surface). The **real test is the full claude-CLI e2e harness** — the
   deferred `li-e2ecli` epic (harness ships from `livespec-dev-tooling`), so
   relocating MOVES that obligation to driver-claude (its heading-coverage
   entry rides as TODO pending the harness epic — owned where it belongs).

**CORE-side sequencing caveat:** the core `/livespec:revise` that removes
both headings co-edits `tests/heading-coverage.json` (drops both entries).
Run it after the sibling relocations are filed; it takes core's gate to
**0 TODOs**. A direct spec edit is NOT allowed — spec changes go through
revise so the active tree matches its `history/vNNN/` snapshot (else
`doctor-out-of-band-edits` fails; see the e58y v145 fix above).

Beads: file besm.6 children in the sibling beads stores at pickup with
cross-repo `depends_on` links. The relocate decision + per-repo plan are
recorded as a comment on `livespec-besm.6`.

## Validated recipes (for reference)

- **New private dev-tooling check**: `check + test + justfile (recipe +
  `check:` private-block alphabetical) + ci.yml `check-metadata` matrix +
  heading flip + commit`.
- **New doctor-static check**: module under
  `.claude-plugin/scripts/livespec/doctor/static/<name>.py` (railway/`returns`,
  pyright HKT pragma if bind chains, `__all__`, `SLUG`, `run(*, ctx)`);
  register in `static/__init__.py` `STATIC_CHECKS` + `APPLICABILITY_BY_TREE_KIND`;
  paired in-process test at `tests/livespec/doctor/static/test_<name>.py`
  (100% coverage); these run against core itself via `check-doctor-static`,
  so core must already conform.
- **Commit legs** (red-green-replay hook): a new product `.py` may land via
  the **suite-green leg** (stage impl + its full-coverage tests together, any
  prefix → the hook runs the entire suite as verifier and records
  `TDD-Suite-Green-*`), OR via the Red→Green stub ritual. Prose/JSON/test-only
  edits use a non-red-intent subject and take the suite-green leg directly.
- **Governed spec edit**: drive `propose_change.py` then `revise.py` (JSON
  payloads; `resulting_files: [{path, content}]` with the FULL corrected
  file) so a `history/v(N+1)/` snapshot lands paired with the active edit.

## Done when

`LIVESPEC_FAIL_IF_HEADING_COVERAGE_TODOS_EXIST=true just check-no-todo-registry`
exits 0. Then close `livespec-besm` + `livespec-besm.6` (+ sibling children)
and delete this file.

## Discipline

Worktree → PR → rebase-merge per repo; `mise exec -- git …`; never
`--no-verify`. Do NOT dispatch the citation/relocation work to autonomous
sub-agents that may auto-merge — a prior fan-out committed + auto-merged 3
PRs against an explicit "no git" brief; keep git in-hand for governed-spec
work. Never force a heading green with a fabricated test id, and never add a
coverage exemption hatch.
