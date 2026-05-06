# critique-fix v029 → v030 revision

## Origin

User-directed architectural addition (2026-04-27 → -29,
mid-Phase-5 sub-step 3). The existing PROPOSAL.md and style
doc already mandate 100% line+branch coverage as a per-commit
gate (PROPOSAL.md §"Testing approach" lines 3118-3134; style
doc §"Code coverage" lines 1317-1362). What they do NOT codify
is the **methodology** that produces that coverage:
Test-Driven Development as formulated by Kent Beck — test-first
authoring (Red-Green) for any new behavior, with refactoring as
a separate independent workflow.

The shipped rule presents 100% coverage as a measurement target,
which leaves room for an agent (or human) to write code first
and tests after, then chase coverage retroactively. That order
breeds: tests that exercise lines without asserting behavior;
implementations that overshoot what was actually needed; and
silent gaps where coverage is satisfied by code paths that no
test ever reasoned about. The remedy in Beck's canon is the
test-first authoring rhythm — write the failing test *first*,
watch it fail for the *right reason*, then write the *minimum*
code that turns it green. Refactor is a separate, independent
unit of work — it does not involve writing new failing tests;
existing tests stay green throughout and prove the refactor
preserves behavior. This revision codifies both disciplines as
the project-wide methodology and upgrades the 100% coverage
rule from "measurement target" to "hard constraint" — the
mechanical forcing function that makes the test-first discipline
auditable at every commit.

This revision also tightens two soft edges in the existing rule
that make the constraint less hard than the user-stated intent:

- The "Escape hatch: `# pragma: no cover — <reason>` capped ≤ 3
  per file" wording in style doc lines 1339-1343 invites
  case-by-case exemption pressure. v030 eliminates the line-level
  pragma exemption; the only structural exclusions (already in
  `[tool.coverage.report].exclude_also`: `if TYPE_CHECKING:`,
  `raise NotImplementedError`, `@overload`) remain.
- The activation phase of the hard-constraint pre-commit gate is
  not currently spelled out. The lefthook hook installs at
  Phase 5 sub-step 5d (promote `just bootstrap`) and the gate
  becomes hard from that commit onward; pre-Phase-5 commits are
  grandfathered (they predate the test infrastructure). v030
  states this explicitly so the activation moment is auditable.

This is Case A (PROPOSAL.md drift / extension) per the bootstrap
skill rule. Triggered by user direction rather than detected
drift; same halt-and-revise mechanism applies. v030 is the next
PROPOSAL snapshot.

## Decisions captured in v030

### D1 — Add §"Test-Driven Development discipline" section to PROPOSAL.md

**Decision.** Insert a new top-level section §"Test-Driven
Development discipline" into PROPOSAL.md immediately before
§"Testing approach" (the section that currently introduces
pytest, pytest-cov, and the 100% coverage requirement). The new
section establishes Beck-style test-first authoring (Red →
Green for new behavior) plus independent refactor (separate
unit of value, no new failing test) as the project-wide
methodology, and positions the existing 100% coverage gate
as the test-first discipline's mechanical forcing function.

**New text (insert before the existing §"Testing approach"
section, currently at PROPOSAL.md line ~3101).**

```markdown
## Test-Driven Development discipline

livespec is developed under strict Test-Driven Development per
Kent Beck's Red-Green-Refactor canon. The discipline is
non-negotiable from Phase 5 exit onward (the moment the test
infrastructure is operational and the per-commit lefthook gate
is installed). Code authored without the discipline is
identifiable post-facto by gaps the per-commit 100% coverage
gate forecloses; the discipline upstream is what produces
useful tests, not just covered tests.

### Authoring rhythm vs. commit boundaries

Red-Green-Refactor is the **authoring rhythm** — the order in
which an author works in their editor. It is NOT a commit
rhythm. Commits represent **cohesive units of user-facing
value delivered**, not phases of an internal authoring cycle.
Two distinct kinds of commit follow from this:

1. **Feature / bugfix commit** = the Red-Green pair, atomically.
   The test was Red during authoring (the author wrote it
   first, ran it, and observed it fail for the right reason);
   the implementation that follows turns it Green; the commit
   captures both together as one unit. At commit time
   everything is green and the per-commit gate passes.
   Committing a Red failing test by itself would (a) fail
   the per-commit gate (broken-tests / sub-100%-coverage
   rejects the commit), and (b) deliver no user-facing value;
   the project does not allow it.
2. **Refactor commit** = behavior-preserving restructuring,
   committed independently. A refactor does NOT involve
   writing a new failing test; the existing tests stay green
   throughout and prove the refactor preserves behavior. A
   refactor MAY backfill missing tests for code that is about
   to be restructured (characterization tests that pin down
   current behavior so the refactor is auditable); those
   tests pass against the pre-refactor implementation, then
   continue to pass against the restructured code. The
   refactor lands as its own commit because it is its own
   unit of value (improved structure with same behavior); it
   is reviewable on its own terms, separate from any feature
   work.

### The internal authoring cycle (Red → Green)

For every change to a covered code file (any `.py` file under
`.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, or `<repo-root>/dev-tooling/**`)
that introduces new behavior:

1. **Red.** Write the smallest failing test that names the
   behavior the change introduces or the bug the change fixes.
   The test MUST execute end-to-end and MUST fail for the
   *right reason* — the assertion fails because the desired
   behavior is missing, NOT because of a SyntaxError, an
   ImportError, a missing fixture, or a typo in the test
   itself. If the test fails for any other reason, fix the
   test until the failure mode is "the implementation does
   not yet do X" before proceeding. Run the test (`uv run
   pytest <test_file>::<test_name>`) and observe the failing
   output; the failure message is what justifies the
   implementation that follows. (Red lives in the editor.
   It does NOT get committed in isolation.)
2. **Green.** Write the *minimum* implementation that turns
   the failing test green. "Minimum" is taken seriously: do
   not add functionality the test does not exercise; do not
   anticipate the next test; do not pre-factor for shape that
   is not yet pressured by a failing assertion. Re-run the
   test and observe it pass. Run the full suite
   (`just check-tests`) to confirm no regression. Once the
   full suite is green and coverage is at 100%, the
   Red-Green pair commits together as the feature/bugfix
   unit of value.

### The independent refactor cycle

Refactor is a separate kind of work, not the third phase of
the Red-Green cycle. A refactor commit:

- Starts with the suite green (existing tests cover the
  pre-refactor behavior).
- MAY first backfill characterization tests if the existing
  coverage has gaps — write tests that pin down current
  behavior, run them against the pre-refactor code, observe
  them PASS (they are NOT Red — current code already does
  the thing the test asserts). The point of these tests is
  to safety-net the impending refactor, not to drive new
  behavior.
- Restructures the implementation (and possibly tests, if
  their shape benefits from cleanup) to remove duplication,
  clarify naming, align with the architectural rules in
  `python-skill-script-style-requirements.md`, or otherwise
  improve structure without changing behavior.
- Keeps tests green throughout; if a test goes red during
  the refactor, that is a signal that behavior changed
  (deliberately or accidentally) and the refactor has stopped
  being a refactor. Either back it out and reapply as a
  separate Red-Green-driven feature change, or scope the
  characterization-test backfill more carefully and try
  again.
- Commits as its own unit of value with a refactor-shaped
  commit message (e.g., "refactor: extract X helper from Y";
  "refactor: rename Z to clarify intent"). Refactor commits
  are reviewable independently of any feature work.

### Failing for the right reason

A test that fails because the assertion expectation is wrong
is a useful Red. A test that fails because of a SyntaxError
in the test, an ImportError caused by a missing module, a
missing fixture, or a typo in the test name is NOT a useful
Red — it tells the author nothing about the behavior under
test. Before writing the implementation:

- Run the failing test in isolation. Read the failure message.
- Confirm the failure message names the *missing behavior*
  (e.g., `AssertionError: expected 7, got 0` because the
  function returns a stub `0`).
- If the failure message names something else (e.g.,
  `ModuleNotFoundError`, `NameError`, `TypeError: f() missing
  1 required positional argument`), the test is not yet at
  Red. Fix the test until its failure mode reflects the
  behavior gap, then proceed to Green.

This applies recursively: a fix to a Red test that exposes a
new failure mode is itself a tiny test-first cycle on the
test authoring (the test author iterates the test until its
failure mode is the behavior gap, then proceeds to Green).

### Legitimate exceptions to test-first

The test-first discipline applies to every change that
introduces new behavior in executable code. The following
narrow categories are exempt from the test-first requirement
(but NOT from the 100% coverage gate post-commit) because
they introduce no new behavior:

- **Pure refactors** that change structure without changing
  behavior. Refactors are not "exempt" from TDD per se —
  they are a separate kind of work entirely (see §"The
  independent refactor cycle" above). The existing tests
  prove the refactor is behavior-preserving; no new failing
  test is authored as part of a refactor. If a refactor
  surfaces new behavior, that behavior is no longer a
  refactor and falls back into the test-first Red-Green
  workflow.
- **Type-only changes** (adding/removing annotations,
  introducing or renaming a `NewType` alias, switching a
  field from `str` to a more specific NewType). Type
  declarations have no runtime behavior to test directly;
  type correctness is verified by `check-types` (Phase-7
  active). The covering tests for the existing runtime
  behavior continue to pass.
- **Documentation-only changes** to `CLAUDE.md`, docstrings,
  comments, prose-only sections of `SPECIFICATION/`, or
  spec markdown files. No executable code is changed.
- **Configuration-only changes** to `pyproject.toml`,
  `justfile`, `lefthook.yml`, `.mise.toml`, `.vendor.jsonc`,
  YAML/TOML/JSON config files where the change does not
  alter Python execution semantics. (A `pyproject.toml`
  change that, e.g., adds a new ruff rule whose violations
  surface in covered code IS a behavior change in the
  enforcement surface and reapplies test-first — the
  failing-rule output is the Red signal that drives the
  follow-up fix as Green.)
- **Mechanical migrations** (renames via grep, file moves
  preserving content, mass-import-rewrites). The existing
  tests follow the rename and continue to pass; no new
  behavior is introduced.

The exception list is exhaustive. Anything outside it that
introduces new behavior follows the test-first Red-Green
workflow. "I couldn't think of a failing test smaller than
the implementation" is NOT an exception — it usually
indicates the implementation is being written too large;
the remedy is to take a smaller step, not to skip Red.

### Why this discipline (not just the coverage gate)

The 100% line+branch coverage gate at every commit (per
§"Testing approach") catches the common failure mode where
a line is added without any test exercising it. It does NOT
catch:

- Tests written *after* the implementation, which tend to
  encode whatever the implementation happens to do rather
  than what the design called for ("change-detector tests").
- Implementations that overshoot the actual requirement
  because the author was not constrained by a specific
  failing test.
- Tests whose execution covers a line but whose assertions
  do not actually verify behavior (the line-coverage tracer
  registers execution; assertion strength is invisible to
  it).

The Red-Green authoring rhythm addresses all three by
construction: the Red test names the desired behavior in
the form of an executable assertion *before* the
implementation exists; the Green implementation is bounded
by what makes the Red turn green; the test stays green from
that moment on. Refactor — committed separately as its own
unit of value — preserves the green by construction (no new
failing tests; characterization tests if needed pass against
the pre-refactor code). Mutation testing (release-gate per
v013 M3, separate from this gate) is the deeper rigor that
catches assertion-strength gaps; v1's per-commit gate stays
at line+branch for speed, with the test-first discipline as
the upstream forcing function for assertion quality.

### Test pyramid

The 100% coverage gate is satisfied by the **bottom of the
test pyramid** — pure unit tests under `tests/livespec/`,
`tests/bin/`, and `tests/dev-tooling/checks/`. These tests
are fast, isolated, and exercise the implementation directly
(no LLM-in-the-loop, no real `git`, no Claude Agent SDK).
The integration and prompt-QA layers above the unit layer
(`tests/e2e/`, `tests/prompts/`) provide additional
confidence but do NOT contribute to the 100% gate — their
test execution paths overlap the unit-layer paths but are
slower, more setup-dependent, and less suitable as a
per-commit forcing function.

`pyproject.toml`'s `[tool.coverage.run].source` enumerates
exactly the three implementation trees (`livespec/`, `bin/`,
`dev-tooling/`) so coverage measurement is anchored at the
unit-test target, not at the integration or prompt-QA
layers.
```

**Rationale.** The new section codifies what is currently
implicit. The existing rule "100% line+branch coverage" is a
necessary backstop, but without the upstream test-first
methodology it is satisfiable by tests-after-the-fact,
change-detector tests, and assertion-light tests that game
the line tracer. Beck-style test-first authoring is the
standard methodological canon for ensuring tests are
*useful*, not just *present*. The "right reason" clause is
the methodological linchpin per Beck's writing — every
practicing TDD author has watched a test fail for a
misleading reason and chased the wrong implementation; the
discipline is to fix the test until it fails for the
behavior gap, then move forward.

Decoupling refactor from the test-first cycle (vs. treating
it as the third phase of an RGR commit-cycle) is the second
methodological linchpin: refactors are a distinct kind of
value delivery — improved structure with preserved behavior.
Bundling them with feature work hides the refactor's
independent risk surface and obscures what each commit is
delivering. Reviewers can ask "is this refactor safe?"
separately from "is this feature correctly specified?"; both
are sharper questions when the commits stand alone.

The exception list is intentionally narrow and exhaustive.
"I couldn't think of a failing test smaller than the
implementation" is the prototypical anti-pattern: it
indicates the implementation step is too large, not that the
test is impossible. The exception clause names categories
where the discipline genuinely does not apply (no new
runtime behavior introduced); everything else that
introduces new behavior follows the test-first Red-Green
workflow, and structure-only changes follow the independent-
refactor workflow.

The pyramid framing makes explicit what the existing
`[tool.coverage.run].source` configuration already implies —
the 100% gate is anchored at the unit-test layer, not the
integration or prompt-QA layers. This forecloses any future
move to "satisfy the 100% via E2E coverage", which would
slow the per-commit gate to E2E speed (multi-second) and
hide unit-level gaps.

**Source-doc impact list.**

- PROPOSAL.md: insert the new §"Test-Driven Development
  discipline" section immediately before §"Testing approach"
  (currently at line ~3101). The new section is the canonical
  reference; existing §"Testing approach" gains a one-line
  back-reference to §"Test-Driven Development discipline" so
  readers landing at the testing section see the methodology
  link.
- `python-skill-script-style-requirements.md`: paired
  operational mirror at the same place (currently §"Code
  coverage" sits at line 1317). The style doc's section gains
  a §"Test-Driven Development discipline" sibling to §"Code
  coverage", with operational specifics (commit-message
  convention, test-first cycle examples in the canonical Python
  shape, exception-clause specifics).

### D2 — Eliminate the per-line `# pragma: no cover` escape hatch

**Decision.** Remove the "≤ 3 per file" line-level pragma
exemption from style doc lines 1339-1343 and remove its
PROPOSAL.md sibling at line 3131-3132. Coverage exclusions
remain available ONLY through the structural patterns already
listed in `[tool.coverage.report].exclude_also`:
`if TYPE_CHECKING:`, `raise NotImplementedError`, `@overload`.

**Old text (style doc §"Code coverage" lines 1339-1343).**

```markdown
- **Escape hatch:** `# pragma: no cover — <reason>` on a single line or
  a bounded block; cap ≤ 3 pragma-lines per file. Bare `# pragma: no cover`
  without a reason is rejected by a targeted regex check. Legitimate
  uses: `if TYPE_CHECKING:` guards; `sys.version_info` gates in
  `bin/_bootstrap.py`.
```

**New text (replacement).**

```markdown
- **No line-level pragma escape hatch.** `# pragma: no cover`
  comments are forbidden anywhere in
  `.claude-plugin/scripts/livespec/**`,
  `.claude-plugin/scripts/bin/**`, and
  `<repo-root>/dev-tooling/**`. The only coverage exclusions
  permitted are the structural patterns in
  `[tool.coverage.report].exclude_also` (`if TYPE_CHECKING:`,
  `raise NotImplementedError`, `@overload`), which are
  block-level patterns recognized by coverage.py without
  per-instance annotation. The two prior legitimate
  per-line uses are now both addressable structurally:
  - `if TYPE_CHECKING:` guards are matched by the
    `exclude_also` pattern; no pragma needed.
  - `sys.version_info` gates in `bin/_bootstrap.py` are
    covered by dedicated `tests/bin/test_bootstrap.py` tests
    that monkeypatch `sys.version_info` to exercise both
    branches (per v011 K3); no pragma needed.
- A targeted regex check (`# pragma: no cover` literal match)
  in `dev-tooling/checks/` rejects any commit that introduces
  the comment in covered code. The check is an existing
  member of the canonical target list (kept under
  `check-coverage`'s pre-flight); it now treats *any*
  occurrence as a violation rather than gating on a count.
```

**Old text (PROPOSAL.md lines 3131-3132).**

```markdown
  branch coverage rule above remains the per-commit gate.
```

**New text.**

```markdown
  branch coverage rule above remains the per-commit gate. The
  rule is a HARD constraint per §"Test-Driven Development
  discipline": no `# pragma: no cover` annotation is permitted
  in covered code; the only structural exclusions are
  `if TYPE_CHECKING:`, `raise NotImplementedError`, and
  `@overload` blocks via `exclude_also`.
```

**Rationale.** The "≤ 3 per file" cap was a v010 J8 / v011 K3
pragmatism allowance for two cases: `if TYPE_CHECKING:` and
the `_bootstrap.py` version gate. Both have since been
addressed by sturdier mechanisms — `exclude_also` for
TYPE_CHECKING (block pattern, no per-line annotation), and
the dedicated `tests/bin/test_bootstrap.py` monkeypatched
tests for the version gate (authored Phase 5 sub-step 2,
2026-04-27 commit a2b4f5d). Keeping the `≤ 3` cap as a
generic line-level escape valve was vestigial — Beck-proud
TDD does not tolerate "this line cannot be tested, skip it";
the answer is either delete the line as dead code or
restructure the code so it IS testable. Eliminating the
escape valve aligns the mechanical rule with the user-stated
"hard constraint" intent.

The targeted regex check already exists in the canonical
target list (style doc line ~1340 references it). This
revision changes its threshold from "cap ≤ 3" to "any
occurrence is a violation" — a one-character regex match-count
change in the script, no architectural shift.

**Source-doc impact list.**

- `python-skill-script-style-requirements.md` lines 1339-1343:
  replace the "Escape hatch" bullet with the "No line-level
  pragma escape hatch" bullet.
- PROPOSAL.md lines 3131-3134: append the hard-constraint
  framing sentence to the existing per-commit gate line.
- `dev-tooling/checks/`: the regex check that already gates
  pragma-without-reason now gates pragma-at-all in covered
  trees. Implementation: existing script body, threshold
  change. Phase 4 wiring already in place; no Phase-N
  re-entry required.
- `pyproject.toml` `[tool.coverage.report].exclude_also`:
  already lists the three structural patterns; no change.

### D3 — Spell out the activation phase for the hard-constraint pre-commit gate

**Decision.** Add an explicit "activates at Phase 5 exit"
clause to PROPOSAL.md §"Testing approach" so the moment the
hard constraint becomes binding is auditable. Pre-Phase-5
commits are grandfathered (they predate the test
infrastructure that the gate depends on); from Phase 5
sub-step 5d (the `just bootstrap` promotion that runs
`lefthook install`) onward, every commit is subject to the
gate.

**New text (insert in PROPOSAL.md §"Testing approach"
immediately after the coverage-rule paragraph, currently at
line ~3134).**

```markdown
**Activation.** The hard-constraint pre-commit gate
(`just check-coverage` at 100% line+branch, plus the rest
of `just check`) becomes binding at the moment lefthook is
installed into `.git/hooks/` — which is the Phase 5
sub-step that promotes `just bootstrap` from its Phase-1
placeholder echo to the real recipe (`lefthook install &&
ln -sfn ../.claude-plugin/skills .claude/skills`).
Pre-Phase-5 commits are grandfathered (they precede the
test suite). From the Phase-5 lefthook-install commit
onward, no commit lands without passing the per-commit
gate; the Phase 6 first self-application seed is the first
working commit subject to the discipline at full strength.
```

**Rationale.** The plan and PROPOSAL together imply the
activation moment but do not state it explicitly. Spelling
it out gives the reader a single source of truth for "when
does the discipline become hard"; eliminates ambiguity for
agents inspecting commit history (pre-Phase-5 commits SHOULD
NOT be retroactively held to the gate); and aligns the
PROPOSAL prose with the plan's existing Phase 5 sub-step
5d wording.

**Source-doc impact list.**

- PROPOSAL.md §"Testing approach": single insertion of the
  Activation paragraph after the coverage-rule paragraph.
- Plan §"Phase 5 — Test suite": the existing `just bootstrap`
  promotion sub-step gains a one-sentence reference to the
  activation moment ("This is the activation point of the
  hard-constraint per-commit gate per PROPOSAL.md
  §'Testing approach — Activation'"). Plan-level edit;
  rides in the same commit as the v030 snapshot per the
  established convention.

### D4 — Reframe §"Testing approach"'s coverage paragraph to point at TDD discipline

**Decision.** Add a one-sentence cross-reference at the top
of §"Testing approach"'s coverage paragraph (currently
PROPOSAL.md line ~3119) so a reader landing at the testing
section sees the methodology link. No content removal; pure
additive cross-reference.

**Old text (PROPOSAL.md line 3118).**

```markdown
- Coverage is measured by **`coverage.py`** via `pytest-cov`.
  Coverage MUST be 100% line + branch across all Python files
  under [...]
```

**New text.**

```markdown
- Coverage is measured by **`coverage.py`** via `pytest-cov`.
  The 100% line+branch gate is the mechanical forcing
  function for §"Test-Driven Development discipline" — read
  that section first; the coverage rule below is the
  per-commit verification that the discipline was followed.
  Coverage MUST be 100% line + branch across all Python files
  under [...]
```

**Rationale.** Discoverability: a reader landing at §"Testing
approach" should not have to scroll back to find the
methodology framing. The cross-reference is one sentence and
adds no new normative content.

**Source-doc impact list.**

- PROPOSAL.md line 3118-3119: insert the cross-reference
  sentence between "via `pytest-cov`." and "Coverage MUST
  be 100%...".

## Plan-level decisions paired with v030

The plan is unversioned per the v022 rule-refactor decision;
plan edits do not enter v030's overlay record but ride in the
same commit as the v030 snapshot. Paired plan edits:

- **`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` §"Version basis"**
  — bump version label to v030; add decision summary for v030
  (D1: TDD discipline section; D2: pragma escape-hatch removal;
  D3: activation-phase clause; D4: cross-reference).
- **Phase 0 step 1 byte-identity check** — bump from v029 to v030.
- **Phase 0 step 2 frozen-status header literal** — bump from
  "Frozen at v029" to "Frozen at v030".
- **Execution prompt block** — bump the "Treat PROPOSAL.md vNNN as
  authoritative" line from v029 to v030.
- **Phase 5 §"`just bootstrap` promotion" sub-step** — append a
  one-sentence note: "This is the activation point of the
  hard-constraint per-commit gate per PROPOSAL.md §'Testing
  approach — Activation'."

## Companion-doc + repo-state changes paired with v030

- `python-skill-script-style-requirements.md`:
  - New §"Test-Driven Development discipline" section paired
    with PROPOSAL.md's; operational specifics (commit-message
    conventions, test-first cycle in canonical Python shape, exception
    examples). Style-doc edits ride freely with the
    implementation per the established style-doc-drift
    convention.
  - §"Code coverage" lines 1339-1343: replace "Escape hatch"
    bullet per D2.
- `dev-tooling/checks/` (the existing pragma-rejection regex
  check): threshold change from "≤ 3 per file with reason" to
  "any occurrence in covered tree is a violation". One-line
  change in the script body. Paired test fixture update.
  Implementation work is a Phase 5 sub-step 3 follow-on
  (during which Phase 5 sub-step 3's broader test-authoring
  campaign is also producing the bottom-of-pyramid coverage
  the new rule depends on).
- `pyproject.toml`: no change — the structural exclusions in
  `[tool.coverage.report].exclude_also` already match the new
  rule.
- `lefthook.yml`: no change — the `pre-commit: just check`
  hook already runs the full suite. The activation moment is
  when `lefthook install` runs (Phase 5 sub-step 5d), which
  is independent of the v030 PROPOSAL revision.

## Open design questions resolved during drafting

The following design questions were surfaced during drafting
and resolved with the user before the v030 snapshot landed:

1. **Pre-Phase-5 grandfather scope.** Resolved: keep the
   simpler phrasing ("all pre-Phase-5 commits are
   grandfathered"). Generalizes cleanly to any livespec-using
   project; doesn't introduce a separate "out of project
   scope" concept. Already what shipped in v030.

2. **Mutation testing's place.** Resolved: `check-mutation`
   stays release-gate-only per v013 M3. Mutation is the
   deeper rigor for release confidence; weekly cadence would
   add operational noise the v030 codification doesn't need
   to introduce. Test-first discipline + 100% line+branch is
   the per-commit forcing function for assertion quality.

3. **Exception list completeness.** Resolved: the five
   categories (pure refactors, type-only, doc-only,
   config-only, mechanical migrations) are exhaustive. Edge
   cases verified: tests aren't "executable code introducing
   new behavior" so they're not in the rule's scope to
   begin with; vendored libs are coverage-excluded; stub
   bodies (`raise NotImplementedError`) are
   coverage-excluded structurally; file deletions are
   "mechanical migrations"; emergency hotfixes don't get an
   exemption (discipline applies under pressure); WIP
   commits on feature branches are forbidden by the
   per-commit gate (commits represent cohesive value).

4. **Commit-message convention (test-first cycle prefixes).**
   Resolved: NOT enforced. The user's clarification that
   commits represent cohesive units of value (not RGR cycle
   phases) made commit-message gating with
   `RED:`/`GREEN:`/`REFACTOR:` prefixes architecturally
   incoherent — committing a Red failing test by itself
   would fail the per-commit broken-tests gate anyway, and
   refactor is its own independent unit of value (separate
   commit) rather than the third phase of an RGR
   commit-cycle. Commit-message prefixes follow conventional
   `feat:` / `fix:` / `refactor:` / `chore:` / `docs:`
   shapes, not RGR phase names.
