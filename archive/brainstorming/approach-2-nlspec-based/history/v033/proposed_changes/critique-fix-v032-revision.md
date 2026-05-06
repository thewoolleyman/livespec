# critique-fix v032 → v033 revision

## Origin

The v032 retroactive TDD redo (cycles 1-56 + the Phase-4 scaffold
commit at 49212c9) reached its declared exit signal — "Phase 3 +
Phase 4 parity" with 90 tests passing — but produced **zero unit
tests under `tests/livespec/**`**. Every authored test landed
under `tests/bin/` (wrapper-coverage + a Phase-3 integration
round-trip) or `tests/dev-tooling/checks/` (paired tests for the
enforcement scripts). The `livespec.commands.*`,
`livespec.validate.*`, `livespec.io.*`, `livespec.parse.*`, and
`livespec.schemas.*` packages were exercised only indirectly via
the integration round-trip, with no behavior-pinning unit tests
at the module level.

Fixing the `--cov-branch` flag bug in the `check-coverage` recipe
(c601885) revealed total coverage at 64.81% against the
post-redo tree — concrete proof that the redo's "parity reached"
declaration described integration-test-green parity, not
unit-test-coverage parity. Five mechanisms compounded to produce
this gap:

1. **The coverage signal was broken.** `pytest --cov` without
   `--cov-branch` set `COV_CORE_BRANCH=enabled` only in the
   parent process; subprocess-invoked checks (the standard
   `tests/dev-tooling/checks/test_*.py` pattern) generated
   line-only data that `cov.combine()` rejected as
   incompatible with the parent's branch data. The
   sub-agents had no quantitative coverage feedback during
   the redo.
2. **No test-file mirror-pairing enforcement script.** The
   dev-tooling suite has `schema_dataclass_pairing.py` and
   `claude_md_coverage.py` but nothing equivalent for
   "every `livespec/foo/bar.py` has a paired
   `tests/livespec/foo/test_bar.py` with at least one
   `def test_*` function." The 1:1 mirror rule from Plan
   §"Phase 5 — Test suite" (line 1759-1761) and PROPOSAL.md
   §"Test pyramid" was author-discipline-only.
3. **Outside-in TDD without a forced inside-out drop-down.**
   `tmp/bootstrap/tdd-redo-briefing.md:113-125` named the
   "drop into a unit test when integration is too coarse"
   pattern as a *guideline*, not a *constraint*. Sub-agents
   advanced the outermost rail (the Phase-3 integration
   round-trip) cycle after cycle without dropping into
   layer-specific unit tests.
4. **Halt condition conflated parity with completeness.**
   The briefing's halt condition #5 (Phase 3 parity) and #6
   (Phase 4 parity) read "integration test green; halt" —
   nothing required "AND `tests/livespec/**` mirror is
   populated for every authored module."
5. **Parent agent did not spot-check the mirror tree
   before accepting the parity declaration.** When the
   sub-agent reported "Phase 3 parity, 28 tests passing"
   the parent updated STATUS without verifying the mirror
   was populated. The mirror rule was a stated convention,
   not a verified pre-condition.

The remedy is a hard mechanical enforcement layer — one
enforcement script per gap, each wired into the canonical
`just check` target list, with `lefthook install` activated
**immediately** (not deferred to Phase 5 exit) so every commit
from the v033-codification commit forward gates on the new
checks. Then the v032 redo is itself redone (a second
retroactive redo) under the new guardrails. The current
post-redo tree is stashed as a binary blob (matching the
`pre-redo.zip` discipline established at v032 D2) for audit
trail; the working tree is reset to the commit immediately
before cycle 1 of the first redo; the second redo proceeds
with mechanical enforcement of mirror-pairing,
per-file-100%-coverage, source-test-commit-pairing, and the
hard `## Red output` gate at every commit boundary.

## Decisions captured in v033

### D1 — Add `dev-tooling/checks/tests_mirror_pairing.py` enforcement script

**Decision.** Add a new dev-tooling check that walks the source
tree under `.claude-plugin/scripts/livespec/`,
`.claude-plugin/scripts/bin/`, and `<repo-root>/dev-tooling/`,
and verifies that every covered `.py` file has a paired test
file at the mirror path under `tests/`, AND that the paired
file contains at least one `def test_*` function definition (or
class-bound test method).

**Coverage rule.** A source file at
`.claude-plugin/scripts/livespec/foo/bar.py` requires a paired
file at `tests/livespec/foo/test_bar.py`. A source file at
`.claude-plugin/scripts/bin/seed.py` requires a paired file at
`tests/bin/test_seed.py`. A source file at
`dev-tooling/checks/all_declared.py` requires a paired file at
`tests/dev-tooling/checks/test_all_declared.py`.

**Exemption set (closed list).**

- `.claude-plugin/scripts/_vendor/**` — vendored libraries,
  out-of-scope per existing convention.
- `.claude-plugin/scripts/bin/_bootstrap.py` — already covered by
  the preserved `tests/bin/test_bootstrap.py` per the v032 D2
  preservation rule.
- `__init__.py` files that contain ONLY `from __future__ import
  annotations` + `__all__: list[str] = []` (or the same plus a
  re-export list with no executable logic) — the AST walker
  recognizes the empty-init pattern and skips it. Any
  `__init__.py` containing executable logic (e.g.,
  `livespec/__init__.py` which configures structlog) requires a
  paired test.
- `tests/**` itself — test files don't need tests-of-tests; the
  mirror rule applies in one direction (source → test).
- The enforcement script's own paired-test exemption: the check
  authors at `dev-tooling/checks/tests_mirror_pairing.py` itself
  pairs with `tests/dev-tooling/checks/test_tests_mirror_pairing.py`
  per the same rule (no special-case for the meta-check).

**Pair-presence requirement.** The paired test file MUST exist
at the mirror path AND MUST contain at least one
`ast.FunctionDef` whose name starts with `test_` (or one
`ast.ClassDef` whose body contains such a function). Empty test
files or test files with only fixtures/helpers fail the check.

**Just target.** `just check-tests-mirror-pairing` (added to the
canonical target list and to the `check` aggregate target's
sequential list).

**Companion-doc impact.**
- `python-skill-script-style-requirements.md` §"Canonical target
  list" — add the row.
- `python-skill-script-style-requirements.md` §"Testing" — note
  the mirror rule is mechanically enforced.
- PROPOSAL.md §"Test pyramid" line 3475-3490 — note the
  enforcement.
- PROPOSAL.md §"Definition of Done (v1)" — add to the
  static-discipline checklist.

### D2 — Add `dev-tooling/checks/per_file_coverage.py` enforcement script

**Decision.** Add a new dev-tooling check that, after a
`pytest --cov --cov-branch` run, parses the `.coverage` data
file (via `coverage.CoverageData` API) and verifies that EVERY
covered file independently hits 100% line and 100% branch
coverage. Differs from `[tool.coverage.report].fail_under = 100`
which is a TOTAL threshold — `per_file_coverage.py` is per-file
and reports the first failing file with offending line numbers.

**Replaces the totalize-only behavior.** The existing
`pyproject.toml` `[tool.coverage.report].fail_under = 100`
setting is preserved (so the report itself fails if total
coverage <100%), but the per-file check is the authoritative
gate — it produces a structured failure list naming each file
and its missing lines/branches, suitable for diff-driven
debugging during a Red→Green cycle.

**Sources covered (closed list).** Same as the existing
`[tool.coverage.run].source` setting:
`.claude-plugin/scripts/livespec`,
`.claude-plugin/scripts/bin`, `dev-tooling`. Excludes
`_vendor/**` per the existing config.

**Exemption set.** None at the per-file level — every file in
the source list must hit 100%. The existing `[tool.coverage.
report].exclude_also` patterns (`if TYPE_CHECKING:`, `raise
NotImplementedError`, `@overload`, `case _:` per v031 D1) still
apply at the line level via coverage's standard exclusion
mechanism. `pragma: no cover` directives remain banned per v030
D2; the per-file check is orthogonal to that ban.

**Just target.** `just check-coverage` is rewritten to: (a) run
`uv run pytest --cov --cov-branch`, (b) invoke
`dev-tooling/checks/per_file_coverage.py` against the
`.coverage` data file, (c) emit the per-file pass/fail summary
+ structured failures. The existing `--cov-report=term-missing`
output is preserved for context.

**Companion-doc impact.**
- `python-skill-script-style-requirements.md` §"Canonical target
  list" — modify the `check-coverage` row.
- `python-skill-script-style-requirements.md` §"Code coverage" —
  add a paragraph clarifying per-file vs total threshold.
- PROPOSAL.md §"Testing approach" line 3393 — clarify the 100%
  gate is per-file.

### D3 — Add `dev-tooling/checks/commit_pairs_source_and_test.py` enforcement script

**Decision.** Add a new dev-tooling check that walks `git
diff --name-only HEAD~1 HEAD` (or against a configurable base)
and verifies: every commit that modifies any file under
`.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, or
`<repo-root>/dev-tooling/checks/**` ALSO modifies a file under
`tests/**`. The reverse is permitted (test-only commits are
fine — characterization-prep, fixture-only changes, etc.).

**Carve-outs (closed list).**

- Commits that DELETE files only — pure-removal commits don't
  require test-pairing.
- Commits whose source-side change is documentation-only (e.g.,
  a `__doc__` rewrite). Detected via AST diff: no executable
  AST changes. Implementation note: this carve-out is narrow;
  the check defaults to requiring the pair, and the carve-out
  is opt-in via a `## Type: docs-only` line in the commit body.
- Refactor commits per PROPOSAL.md §"The independent refactor
  cycle" — declared via a `refactor:` commit-message prefix or
  a `## Type: refactor` line. Refactors don't add new failing
  tests (per PROPOSAL.md line 3181-3211); the existing test
  suite IS the regression net. The check skips test-pairing
  for these commits but still requires the existing tests to
  pass (`check-tests`).
- Configuration-only commits (e.g., `pyproject.toml` linter
  config tweak, `justfile` recipe edit) — declared via a
  `## Type: config` line in the commit body, OR via filename
  (the check recognizes `pyproject.toml`, `justfile`,
  `lefthook.yml`, `.mise.toml`, `.vendor.jsonc`, `.gitignore`
  as config-only by default).
- Phase 1-4 grandfather: commits before the v033-codification
  commit are not retroactively gated. The check's git-walk
  start point is the v033-codification commit's parent.

**Just target.** `just check-commit-pairs-source-and-test`
(added to canonical target list, run by `lefthook` on
pre-commit, NOT in the `check` aggregate target — the aggregate
target runs once per `just check` invocation; commit-pairing is
intrinsically per-commit and lives in lefthook directly).

**Companion-doc impact.**
- `python-skill-script-style-requirements.md` §"Canonical target
  list" — add the row.
- PROPOSAL.md §"Test-Driven Development discipline" §"The
  independent refactor cycle" — note the `refactor:` /
  `## Type: refactor` declaration is mechanically recognized.
- `lefthook.yml` — wire the check into pre-commit.

### D4 — Upgrade `red_output_in_commit.py` from informational warning to hard gate

**Decision.** The existing `dev-tooling/checks/red_output_in_commit.py`
authored at v032 cycle 56 currently runs as Phase-4-informational
(warns on missing `## Red output` block, exit 0). v033 promotes
this to a hard gate immediately: missing `## Red output` block
on a feature/bugfix commit produces exit non-zero and the
commit is rejected at the lefthook pre-commit step.

**Carve-outs.** Same as D3's exemption set — refactor commits,
config-only commits, docs-only commits are exempt. Test-only
commits (test fixture additions, characterization-style adds
at the spec/sub-spec layer) are also exempt — `## Red output`
applies to feature/bugfix commits that change `livespec/**`,
`bin/**`, or `dev-tooling/checks/**` source.

**Phase grandfather.** Pre-v033-codification-commit commits are
not retroactively gated. The check's start point is the
v033-codification commit's parent, identical to D3.

**Companion-doc impact.**
- `python-skill-script-style-requirements.md` §"Canonical target
  list" — modify the existing `check-red-output-in-commit` row
  (drop the "informational" annotation; promote to hard gate).
- PROPOSAL.md §"Test-Driven Development discipline" — note the
  hard-gate promotion at v033 (closes the v032 D4 deferral).

### D5 — Activate `lefthook install` immediately; authorize a second retroactive redo

**Decision (D5a — lefthook-install promotion).** Move the
`lefthook install` step from its currently-deferred Phase-5-exit
position to **immediately after the v033-codification commit
lands and the four new enforcement scripts (D1-D4) are
authored**. Concrete sequence:

1. v033 codification commit lands (PROPOSAL.md + plan-text edits
   + revision file snapshot under `history/v033/`).
2. The four new enforcement scripts (`tests_mirror_pairing.py`,
   `per_file_coverage.py`, `commit_pairs_source_and_test.py`)
   are authored under TDD discipline plus the existing
   `red_output_in_commit.py` is upgraded. Each gets a paired
   test under `tests/dev-tooling/checks/test_<name>.py` with
   pass + fail fixtures, per the established Phase-4 pattern.
3. `justfile` is updated: `bootstrap` recipe is rewritten to
   `lefthook install && ln -sfn ../.claude-plugin/skills
   .claude/skills`. New `check-tests-mirror-pairing`,
   `check-commit-pairs-source-and-test` recipes added; the
   `check-coverage` recipe is rewritten per D2; `check` aggregate
   updated.
4. `lefthook.yml` is updated to reference the new pre-commit
   step running `just check-commit-pairs-source-and-test` AND
   the existing `just check`. (lefthook semantics: pre-commit
   runs the wired commands; pre-commit hook delegation pattern
   per v013 M3 unchanged otherwise.)
5. `just bootstrap` is run by the executor — installs the
   lefthook git-hooks into `.git/hooks/`. From this commit
   onward, every commit is gated.

**Decision (D5b — second retroactive redo authorization).**
After D5a's lefthook activation lands, authorize a SECOND
retroactive redo of all v032-redo work. Procedure mirrors v032
D2's mechanics with one difference (the audit-trail blob name):

1. **Stash the current post-redo tree as `bootstrap/scratch/pre-second-redo.zip`.**
   Archive every `.py` file under
   `.claude-plugin/scripts/livespec/` (excluding `_vendor/**`
   and `__init__.py` files), every `.py` under
   `.claude-plugin/scripts/bin/` (excluding `_bootstrap.py`),
   every `.py` under `dev-tooling/checks/`, every `.py` under
   `tests/livespec/` (currently empty of `.py` files but
   future-proofing), every `.py` under `tests/bin/`
   (excluding `tests/bin/test_bootstrap.py` and
   `tests/bin/conftest.py`), and every `.py` under
   `tests/dev-tooling/checks/` (excluding the four new
   enforcement-script tests authored in D5a step 2 — those
   stay in-tree because they are the guardrails enforcing the
   second redo). The zip is committed to the repo as a binary
   blob (no-source-readable, no-`unzip`-during-authoring; same
   discipline as `pre-redo.zip`). Both zips persist until Phase
   11 cleanup, which removes them via `git rm`.
2. **`git reset --hard <pre-second-redo-baseline-sha>`** —
   the baseline sha is the commit immediately preceding cycle
   1 of the v032-first-redo (the commit that landed
   `pre-redo.zip` itself plus the pre-cycle-1 working-tree
   state). The reset rewinds the working tree to "Phase 3
   redo not yet started" with the v033-codification +
   D5a-guardrail commits restored on top via cherry-pick.
   Specifically:
   a. Identify the pre-cycle-1 baseline sha via `git log` on
      `bootstrap/scratch/pre-redo.zip` — the first commit
      that introduced the file.
   b. Identify the v033-codification commit + D5a-guardrail
      commits as a contiguous range.
   c. `git reset --hard <pre-cycle-1-baseline-sha>`.
   d. `git cherry-pick <v033-codification-commit>..<last-D5a-guardrail-commit>`
      to bring the new guardrails forward onto the reset
      working tree.
   e. Add the `pre-second-redo.zip` to the working tree and
      commit it with message `phase-5: stash failed v032 redo
      tree as pre-second-redo.zip; reset to pre-cycle-1
      baseline; second redo authorized per v033 D5`.
3. **Restart the redo** under the new guardrails. Each cycle
   from this commit forward is gated by lefthook running:
   `check-tests`, `check-coverage` (per-file 100%),
   `check-tests-mirror-pairing`,
   `check-commit-pairs-source-and-test`,
   `check-red-output-in-commit`, plus the existing
   Phase-4-active enforcement scripts. The mechanical failure
   modes that produced the v032 gap are blocked at commit-time
   from the very first cycle.
4. **Exit condition.** Same as v032 D2 step 6 — all Phase 3 /
   Phase 4 / Phase 5 exit criteria pass against the
   second-redo tree, AND the v032 D3 quality-comparison report
   (now reframed as the v033 D5b quality-comparison report)
   passes its acceptance criteria.

**Decision (D5c — quality-comparison report scope).** The v032
D3 quality-comparison report mechanism is preserved with a
scope expansion: the report measures the second-redo tree
against BOTH `pre-redo.zip` (the original impl-first
characterization-mode tree) AND `pre-second-redo.zip` (the
failed-first-redo tree). The four dimensions (architecture,
coupling, cohesion, unnecessary-code-elimination) are reported
for both deltas. Acceptance criteria: the second-redo tree
shows concrete improvement on at least three of the four
dimensions vs `pre-redo.zip` AND vs `pre-second-redo.zip`.

**Companion-doc impact.**
- PROPOSAL.md §"Testing approach — Activation" line 3394 —
  add a v033 paragraph clarifying that lefthook activation
  moves from Phase 5 exit to v033-codification.
- Plan §"Phase 5 — Test suite" — add the
  "Retroactive TDD redo of Phase 3 + Phase 4 work — second
  attempt" sub-section paralleling the v032 D2 sub-section.
- Plan §"Phase 5 §exit criterion" — note the second-redo
  audit-trail blob.
- `bootstrap/decisions.md` — log D5b's authorization
  (audit trail).

### D6 — Plan housekeeping

Standard pattern (per v028, v029, v031 precedent):

1. **Version basis preamble.** Bump version label `v032` →
   `v033`; add the v033 decision summary block.
2. **Phase 0 step 1 byte-identity reference.** `history/v032/`
   → `history/v033/`.
3. **Phase 0 step 2 frozen-status header.** `Frozen at v032` →
   `Frozen at v033`.
4. **Execution-prompt block authoritative-version line.**
   Bump v032 → v033.
5. **Phase 5 §"Retroactive TDD redo" sub-section preserved as
   a record of the first attempt; new "Retroactive TDD redo —
   second attempt (v033 D5b)" sub-section added per D5
   companion-doc impact.**

## Out of scope

The following are deliberately NOT codified in v033:

- **Stricter "unit-test-only coverage" via coverage contexts.**
  An alternate framing of the user's "100% unit test level
  coverage" directive uses `--cov-context=test` to verify each
  source line is covered by its paired unit test specifically
  (not by an incidental integration test). v033 instead relies
  on the combination of D1 (mirror-pairing — every source has
  a paired test that exists with at least one `def test_*`)
  and D2 (per-file 100% coverage). In practice, the paired
  unit test is the primary covering test for each source, and
  the structural rule + the per-file gate together produce the
  intended discipline. If quality-report dimensions reveal the
  combination is insufficient, a follow-up revision can add
  context-based enforcement.

- **Mutation-testing activation moved earlier.** v013 M3
  positions `check-mutation` as a release-gate; v033 leaves
  that positioning unchanged. Mutation testing is orthogonal
  to the unit-test-presence gap v033 is addressing.

- **A `conftest.py` at the repo root or `tests/`.** No new
  conftest is required; the `--cov-branch` flag fix at
  c601885 is sufficient to make subprocess coverage data
  compatible with parent branch data.
