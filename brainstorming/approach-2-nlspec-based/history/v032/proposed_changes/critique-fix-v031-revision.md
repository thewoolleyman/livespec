# critique-fix v031 → v032 revision

## Origin

Phase 5 sub-step 3 has been authoring `tests/livespec/**` under
the "characterization-style backfill" framing — write tests
against pre-existing Phase 3 / Phase 4 impl, observe them PASS
(not Red), then commit. The carve-out cited at
PROPOSAL.md §"The independent refactor cycle" line 3182 covers
this practice for *refactor-prep* work, but Phase 5's bulk-
tests-against-pre-existing-impl is not refactor work; it is
test-suite construction after the fact. Two consequences fall
out:

1. **The Red signal never fires for the right reason.** TDD's
   load-bearing benefit is not coverage; it is the design
   pressure created when a small failing test names exactly
   one behavior and the implementation is bounded by what
   makes that test pass. Tests authored against existing
   impl encode whatever the impl happens to do
   ("change-detector tests" per PROPOSAL.md line 3287) and
   exert no design pressure on coupling, cohesion, or dead
   code.
2. **PROPOSAL.md text creates a temporal carve-out for this
   exact failure mode.** Line 3105 says TDD discipline is
   "non-negotiable from Phase 5 exit onward". The pre-Phase-
   5-exit period is therefore treated as an exemption window
   in which Phase 3 and Phase 4 impl can be authored without
   a failing test driving each behavior, and the 100%
   coverage gate at Phase 5 backfills the safety net. v032
   strikes this carve-out: there was never supposed to be an
   exemption window — only an *enforcement* window. Authoring
   discipline is upstream of gate activation.

The user's framing: "can't have Red for the right reason if
you don't see them fail one by one." The value of TDD is
forcing loose coupling and high cohesion, eliminating any
unnecessary code, and driving good architecture by letting
each module's shape emerge under the pressure of a specific
failing test. Characterization-backfill against pre-existing
impl delivers covered code, not designed code.

The remedy is a one-time retroactive redo: delete every Phase
3 / Phase 4 / Phase 5 Python artifact (impl + test) and
re-author each module under strict Red→Green→Refactor with
the failing-test output observed and recorded per commit. The
PROPOSAL-prescribed outer architecture (which modules exist
and what they own) stays — that is set by PROPOSAL.md and is
not negotiable here. What changes is the *authoring rhythm*:
each behavior within each module is pulled into existence by a
specific failing test, not authored speculatively and tested
afterward.

A final closure step (D3) demands an explicit quality-
comparison report at Phase 5 exit: the executor must measure
the post-redo codebase against the pre-redo state on
architecture, coupling, cohesion, and unnecessary-code
elimination, and demonstrate concrete improvement. If the redo
produces materially the same code, the redo failed and the
discipline lapsed back into characterization mode; the report
is the auditable forcing function.

## Decisions captured in v032

### D1 — Strike the "Phase 5 exit onward" temporal carve-out from PROPOSAL.md §"Test-Driven Development discipline"

**Decision.** The PROPOSAL.md §"Test-Driven Development
discipline" opening paragraph at lines 3103-3110 implies that
TDD discipline can be deferred to Phase 5 exit. v032 rewrites
this paragraph to clarify the distinction between *authoring
discipline* (applies from the moment any covered code is
authored, including Phase 3) and *gate enforcement* (activates
at Phase 5 exit when the lefthook per-commit gate is wired).
The carve-out language gets explicitly closed; the v032 redo
of Phase 3-5 work is referenced as the one-time mechanism that
brings the pre-Phase-5-exit codebase under the discipline.

**Old text (PROPOSAL.md lines 3103-3110).**

```
livespec is developed under strict Test-Driven Development per
Kent Beck's Red-Green-Refactor canon. The discipline is
non-negotiable from Phase 5 exit onward (the moment the test
infrastructure is operational and the per-commit lefthook gate
is installed). Code authored without the discipline is
identifiable post-facto by gaps the per-commit 100% coverage
gate forecloses; the discipline upstream is what produces
useful tests, not just covered tests.
```

**New text.**

```
livespec is developed under strict Test-Driven Development per
Kent Beck's Red-Green-Refactor canon. The discipline applies
to every covered-code change from the first Python module
onward; what activates at Phase 5 exit is the *mechanical
enforcement gate* (lefthook + 100% coverage), NOT the
discipline itself. Authoring rhythm is upstream of gate
activation: a module authored without a failing test driving
each behavior produces covered code, not designed code, and
the coverage gate cannot detect the difference. v032 closes
the prior temporal carve-out that read this section as
permitting pre-Phase-5-exit characterization-style authoring;
see Plan Phase 5 §"Retroactive TDD redo of Phase 3 + Phase 4
work" for the one-time mechanism that brings the
pre-v032 codebase under the discipline.
```

**Source-doc impact.**

- PROPOSAL.md lines 3103-3110: replace per the old/new text
  above.
- PROPOSAL.md §"Activation" paragraph (lines 3386-3397):
  unchanged. The activation paragraph already correctly
  scopes itself to *gate enforcement*; D1 just makes the
  upstream §"Test-Driven Development discipline" opening
  consistent with that scope.
- Companion `python-skill-script-style-requirements.md`
  §"Test-Driven Development" (added at v030 D5): no change
  required; the companion-doc text frames the discipline
  as authoring rhythm without a temporal carve-out.

### D2 — Plan reshape: Phase 3 / Phase 4 / Phase 5 redo procedure

**Decision.** The plan's Phase 3, Phase 4, and Phase 5
sections are amended in place to:

1. Preserve the PROPOSAL-prescribed module enumeration and
   exit criteria — these are architectural constraints, not
   authoring-rhythm constraints.
2. Replace the authoring-rhythm wording in each phase with
   explicit Red→Green-per-behavior discipline.
3. Add a new Phase 5 sub-step ("Retroactive TDD redo")
   bracketing the redo as a single-shot operation: delete
   all current Phase 3 / Phase 4 / Phase 5 Python artifacts
   into a stash, then walk module-by-module through
   Red→Green cycles authoring tests *and* impl together
   until every PROPOSAL-prescribed module is back in place
   under the discipline.

**Plan-text edits.**

#### D2.a — Phase 3 §"Phase 3 — Minimum viable …" (line 1249)

Add a one-paragraph **Authoring discipline** preamble
immediately after the introductory paragraph (after line
1258, before "Required implementation surface…"):

```markdown
**Authoring discipline (v032 D1).** Every module enumerated
below is authored under strict Red→Green-per-behavior. The
enumeration fixes WHICH modules exist and WHAT each owns; it
does NOT prescribe the order or granularity of the internal
authoring cycles. For each module: identify a behavior the
module owes (driven by a specific consumer or invariant);
write the smallest failing test that names that behavior;
observe the failure mode is the behavior gap, not a SyntaxError
/ ImportError / fixture issue; write the minimum
implementation that turns it Green; commit the Red-Green pair
atomically with the failing-test output captured in the commit
body per Plan Phase 5 §"Per-commit Red-output discipline".
Repeat per behavior until the module satisfies its
PROPOSAL-prescribed contract. No bulk authoring of an entire
module followed by tests-after; no characterization-style
backfill; no speculative defensive code.
```

The exit criterion at Phase 3 lines 1516-1540 is unchanged:
the seed round-trip and the propose-change/revise smoke
cycle remain the gate. The discipline preamble does not
enlarge the exit criterion; it constrains the authoring path
to it.

#### D2.b — Phase 4 §"Phase 4 — Developer tooling enforcement scripts" (line 1576)

Add a one-paragraph **Authoring discipline** preamble
immediately after the introductory paragraph (after line
1581, before "Scripts:"):

```markdown
**Authoring discipline (v032 D1).** Every check below is
authored test-first per the same Red→Green-per-behavior
discipline that applies to `livespec/**`. For each check:
write the failing test in `tests/dev-tooling/checks/` that
names ONE failure mode the check exists to catch (a specific
violation pattern, with input that should be rejected); observe
the test fail because the check has not yet been written; write
the minimum check logic that turns it Green; commit the
Red-Green pair. Repeat per failure mode until the check covers
every pattern PROPOSAL.md §"Canonical target list" / the style
doc names for that target. No characterization-style
backfilling of tests against pre-existing checks; the existing
Phase 4 check implementations are deleted and re-derived under
this discipline as part of Plan Phase 5 §"Retroactive TDD redo
of Phase 3 + Phase 4 work".
```

The Phase 4 exit criterion at lines 1619-1624 is unchanged.

#### D2.c — Phase 5 §"Phase 5 — Test suite" (line 1656)

Phase 5's existing scope (skeleton dirs for `tests/e2e/` +
`tests/prompts/`, meta-tests, lefthook activation, exit
criterion) is preserved. v032 adds a **new top-level Phase 5
sub-section** between the existing introductory bullet list
(line 1716) and the `just check-coverage` exit-criterion
paragraph (line 1718):

```markdown
#### Retroactive TDD redo of Phase 3 + Phase 4 work (v032 D2)

Phase 3 and Phase 4 produced impl-first code with tests
authored afterward. v032 D1 closes the temporal carve-out
that permitted that mode; this sub-section bridges the gap
by deleting every Phase 3 / Phase 4 / Phase 5-so-far Python
artifact and re-authoring each module under strict
Red→Green-per-behavior. Procedure:

1. **Stash the pre-redo tree as a committed zip archive.**
   Archive every `.py` file under
   `.claude-plugin/scripts/livespec/` (excluding
   `_vendor/**` and `__init__.py` files), every `.py` under
   `.claude-plugin/scripts/bin/` (excluding `_bootstrap.py`,
   which has its own meta-test contract and is preserved as
   the version-gate), every `.py` under
   `dev-tooling/checks/`, every `.py` under
   `tests/livespec/`, every `.py` under `tests/bin/`
   (excluding `tests/bin/test_bootstrap.py` and
   `tests/bin/conftest.py`), and every `.py` under
   `tests/dev-tooling/checks/` into
   `bootstrap/scratch/pre-redo.zip`. The zip is committed to
   the repo (binary blob, under SCM but not source-readable —
   `git grep` skips it, `Read` on it returns binary garbage,
   the only access path is deliberate `unzip`). Then delete
   the originals. The pre-redo zip preserves the audit trail
   for the v032 D3 quality-comparison report and survives
   until Phase 11 cleanup, which removes it via `git rm`. The
   zip MUST NOT be `unzip`-ed during authoring of the redone
   modules; the only legitimate `unzip` is the
   measurement-time extraction at v032 D3 report authoring,
   which extracts to a `tmp/bootstrap/pre-redo-extracted/`
   scratch dir, runs the metrics, and deletes the extraction
   when done.
2. **Verify clean state.** `just check-tests` against the
   stripped tree errors with import failures (intended); the
   tree is genuinely empty of Phase 3-5 Python.
3. **Walk the PROPOSAL-prescribed module enumeration in
   dependency order**, re-authoring each module under
   Red→Green-per-behavior. Recommended order, derived from
   import dependencies: (a) `livespec/types.py`,
   `livespec/errors.py`, `livespec/context.py`,
   `livespec/__init__.py`; (b) `livespec/schemas/dataclasses/`
   (10 modules); (c) `livespec/parse/` (jsonc, front_matter);
   (d) `livespec/validate/` (10 modules); (e)
   `livespec/io/` (cli, fs, git,
   fastjsonschema_facade, returns_facade, structlog_facade);
   (f) `livespec/commands/` (resolve_template, seed,
   propose_change, critique, revise, prune_history, plus
   `_seed_helpers`, `_revise_helpers`); (g)
   `livespec/doctor/` (run_static plus the 12 static checks
   per PROPOSAL.md §"Static-phase structure"); (h)
   `dev-tooling/checks/` (26 checks); (i)
   `.claude-plugin/scripts/bin/` wrappers (8 modules; meta-
   tested via `tests/bin/test_wrappers.py` per the existing
   wrapper-shape contract). The order is a recommendation,
   not a contract — Red→Green discipline determines the next
   module by which test the executor wants to write next.
4. **Per-module discipline.** Each Red→Green pair lands as
   one commit. The commit message starts with `phase-5: ...`
   (since this is Phase 5 execution work) and the commit
   body MUST include the captured Red output per Plan Phase
   5 §"Per-commit Red-output discipline" (v032 D4). Refactor
   commits are separate per PROPOSAL.md §"The independent
   refactor cycle" — they do NOT include a new failing test
   and have a `refactor: ...` message prefix.
5. **No re-derivation by inspection.** The committed
   `bootstrap/scratch/pre-redo.zip` MUST NOT be `unzip`-ed
   during redo authoring. The zip is binary-blob committed
   so the audit trail is solid, but extracting it during
   module authoring would defeat the discipline. The
   architecture is PROPOSAL-prescribed; the implementation
   must emerge from the failing tests, not be transcribed
   from the prior version. The only legitimate extraction is
   at D3 quality-comparison report authoring time.
6. **Exit condition.** All Phase 3 / Phase 4 / Phase 5 exit
   criteria pass against the redone tree (in particular:
   `just check-tests`, `just check-coverage` at 100%
   line+branch across `livespec/**`, `bin/**`,
   `dev-tooling/**`, the seed round-trip, and the propose-
   change/revise smoke cycle). The v032 D3 quality-
   comparison report passes its acceptance criteria.

The redo is bracketed within Phase 5 because Phase 5 is when
the test infrastructure becomes operational; the pre-redo
test infrastructure existed but the discipline did not. The
redo is a one-time event; once complete, normal Phase
5-onward work resumes from the (new) sub-step that was
in-progress at v032 commit time.
```

#### D2.d — Phase 5 §"Phase 5 — Test suite" exit criterion (line 1731)

Add a one-line addition to the exit criterion paragraph: the
v032 D3 quality-comparison report MUST pass. Concrete edit:

**Old text (line 1744).**

```
`just bootstrap` has been run and lefthook is installed.
```

**New text.**

```
`just bootstrap` has been run and lefthook is installed. The
v032 D3 retroactive-TDD quality-comparison report (Plan Phase
5 §"Quality-comparison report") has been authored and its
acceptance criteria pass — the redone tree demonstrates
concrete improvement on architecture, coupling, cohesion,
and unnecessary-code elimination relative to the
`bootstrap/scratch/pre-redo/` stash.
```

### D3 — Quality-comparison report sub-step at Phase 5 exit

**Decision.** Add a new Phase 5 sub-section §"Quality-
comparison report" that the executor MUST author and the
user MUST gate before Phase 5 advance. The report contrasts
the post-redo codebase against the pre-redo stash on four
dimensions named by the user: **architecture**, **coupling**,
**cohesion**, and **unnecessary-code elimination**. The
report is the auditable forcing function: if the redo
produced materially the same code, the report makes that
visible and the user can either accept ("redo gave us no
benefit; the discipline lapsed") or reject ("redo lapsed,
roll back the stash and try again").

**Plan-text edit (insert as new sub-section after the
"Retroactive TDD redo" sub-section authored in D2.c).**

```markdown
#### Quality-comparison report (v032 D3)

After the retroactive redo completes and all Phase 3 / Phase
4 / Phase 5 exit gates pass, the executor authors
`bootstrap/v032-quality-report.md` (committed alongside the
zip stash; both removed at Phase 11 via `git rm`). The report
MUST cover all four dimensions below with concrete
measurements drawn from a one-time extraction of
`bootstrap/scratch/pre-redo.zip` (pre) versus the live tree
(post). Extraction procedure: `unzip
bootstrap/scratch/pre-redo.zip -d
tmp/bootstrap/pre-redo-extracted/`; run all metrics against
the extracted tree; delete `tmp/bootstrap/pre-redo-extracted/`
when the report is authored. The extraction is the ONLY
legitimate `unzip` of the stash; it happens once, after the
redo is complete, with the explicit purpose of measurement.
Subjective claims are not sufficient — every dimension below
carries at least one quantitative metric.

**Dimension 1 — Architecture.**

- Module count delta per top-level package
  (`livespec/commands/`, `livespec/io/`, `livespec/doctor/`,
  `livespec/validate/`, `livespec/parse/`, `livespec/schemas/`,
  `dev-tooling/checks/`, `tests/**`). Pre and post counts;
  delta with sign.
- Architectural-rule compliance: count of distinct
  PROPOSAL.md / style-doc rule citations the post-tree
  implementation satisfies that the pre-tree did not (e.g.,
  ROP pipeline shape, `@impure_safe` boundaries,
  `@rop_pipeline` single-public-method, supervisor
  discipline) — the executor MUST identify any rule the
  pre-tree was violating that the redo brought into
  compliance, OR explicitly state "no rule-compliance
  delta" and explain why the rules were already satisfied.
- Public-API surface: union of all `__all__` entries across
  `livespec/**`. Pre count, post count, delta with sign.
  Reductions are improvements (smaller surface ⇒ tighter
  contract); growth requires justification per added entry.

**Dimension 2 — Coupling.**

- Per-module import count: for each module under
  `livespec/**`, count of distinct module-level `import` /
  `from … import` statements (excluding `_vendor/**`).
  Report mean and max pre vs post; delta with sign.
  Reductions are improvements.
- Cross-package edges: count of import edges that cross
  package boundaries (`commands/` → `io/`, `doctor/` →
  `validate/`, etc.). Pre vs post; delta with sign.
- Cyclic-import / fan-out hotspots: any module with
  fan-out > 8 in either tree gets called out by name. The
  report MUST identify whether each hotspot survived the
  redo (and why) or was eliminated.

**Dimension 3 — Cohesion.**

- LOC per module (logical lines, per
  `dev-tooling/checks/file_lloc.py`). Pre mean / max / count
  > 100 LLOC; post mean / max / count > 100 LLOC. Each
  dimension delta with sign.
- Public-method count per public class: report mean and max
  pre vs post. The `@rop_pipeline` single-public-method rule
  (v029 D1) means classes carrying that decorator have
  exactly one public method; the report MUST confirm
  compliance for both trees and surface any
  multi-public-method classes that survived the redo.
- Public-function-per-module count: pre vs post mean and
  max; delta. Higher cohesion typically presents as fewer
  public functions per module with more focused
  responsibilities.

**Dimension 4 — Unnecessary-code elimination.**

- Total LOC delta (impl + test, separately): pre LLOC,
  post LLOC, delta with sign. Pure reductions are the
  expected primary signal of TDD's "minimum implementation"
  rule.
- Defensive / unreachable code count: count of `pragma: no
  cover` directives (must be zero in both trees per v030
  D2), count of `raise NotImplementedError` exclusions, count
  of `case _:` arms (the structurally-unreachable
  assert-never sentinels — these are expected to survive the
  redo wherever exhaustive `match` statements remain). Pre
  vs post; delta with sign.
- Helper-function reuse: count of helper functions in
  `_*.py` private-helper modules pre vs post. The redo is
  expected to *reduce* helper count if Phase 3-4 introduced
  speculative helpers that no specific test demanded.
- Behavioral-equivalence audit: the executor MUST run the
  Phase 3 exit-criterion smoke (seed round-trip + propose-
  change/revise) against both the pre-redo stash (after
  temporary restoration to a scratch venv if needed) and
  the post-redo tree, and confirm output equivalence. Any
  behavior that changed during the redo is a defect of the
  redo (TDD redo is supposed to be behavior-preserving at
  the contract level), not a feature.

**Acceptance criteria.** The report is acceptable iff:

1. Every dimension above is covered with the named
   quantitative metrics.
2. At least three of the four dimensions show concrete
   improvement (negative delta on LOC, fan-out, public
   surface, etc., or positive delta on rule compliance).
   Materially-equivalent measurements across all four
   dimensions ("the redo produced the same code") indicate
   the discipline lapsed and the redo failed; the user MAY
   reject the report and demand a re-redo, OR MAY accept
   it as evidence that the original Phase 3-4 code was
   already at the design quality TDD would have produced
   (which is a possible-but-rare outcome the report
   captures honestly rather than overclaiming).
3. The behavioral-equivalence audit passes (Phase 3
   smoke produces equivalent output against both trees).

The report is gated by AskUserQuestion before Phase 5
advance: the user reads the report, accepts or rejects, and
on rejection the redo is re-attempted (or the stash is
restored if the user concludes the redo cannot improve on
the original).
```

### D4 — Stash + per-commit Red-output discipline

**Decision.** Two execution-discipline conventions paired
with the redo, codified in the plan and gitignore.

**D4.a — Stash convention (committed zip).** The pre-redo
Python artifacts are archived into
`bootstrap/scratch/pre-redo.zip` and **committed to the
repo** rather than being deleted outright or stashed in a
gitignored directory. The zip is a binary blob: under SCM
(real audit trail, `git log` can show its addition and
removal, `git show <sha>:bootstrap/scratch/pre-redo.zip`
retrieves the exact bytes archived), but not source-readable
(`git grep` skips it; `Read` on it returns binary garbage;
`grep -r` skips binary files by default; the only access
path is deliberate `unzip`). Purposes: (i) the v032 D3
report measures against it via a one-time extraction to
`tmp/bootstrap/pre-redo-extracted/`; (ii) the audit trail is
preserved across branches, sessions, and reviewers; (iii)
Phase 11 cleanup removes the zip via `git rm` rather than
deleting gitignored content. The zip MUST NOT be `unzip`-ed
during authoring of the redo modules — that would defeat the
discipline. The bootstrap skill (and any future executor)
MUST treat extraction during authoring as a discipline
violation equivalent to opening the deleted Phase 3-4
implementation files directly.

**D4.b — Per-commit Red-output discipline.** Every Red→Green
commit during the redo MUST include the captured failing-test
output in the commit body. Format: a fenced code block under
a `## Red output` heading inside the commit message,
containing the literal `pytest` output observed when the test
was first run before any implementation existed. This serves
two purposes: (i) audit trail confirming the test was
genuinely Red for the right reason (assertion failure naming
the missing behavior, not SyntaxError / ImportError / fixture
issue); (ii) post-facto inspection by the executor (or a
future reviewer) can verify the discipline was followed by
spot-checking commits.

**Plan-text edit (insert as new sub-section in Phase 5
between the "Quality-comparison report" sub-section and the
existing exit-criterion paragraph).**

```markdown
#### Per-commit Red-output discipline (v032 D4)

Every Red→Green commit authored under v032 D2's retroactive
redo (and every subsequent feature/bugfix commit from this
phase onward, per the universal §"Test-Driven Development
discipline") MUST include the captured failing-test output
in the commit body. Format: a `## Red output` heading
followed by a fenced code block containing the literal
`pytest` output the executor observed when the test was
first run prior to any implementation. The block confirms
the failure was at the assertion site (the behavior gap),
not at parse/import/fixture time.

`tests/dev-tooling/checks/test_red_output_in_commit.py`
(authored as part of the dev-tooling checks redo) walks
`git log --grep` against the redo's commit range and rejects
any feature/bugfix commit that lacks a `## Red output`
section. The check is informational pre-Phase-5-exit; it
becomes a hard `just check` gate at Phase 5 exit (lefthook
+ post-Phase-5-exit commits).
```

**Source-doc impact.**

- `bootstrap/scratch/pre-redo.zip` (new, committed binary
  blob): authored at the start of the redo per D2.c step 1.
  No `.gitignore` edit needed — the zip is intentionally
  tracked.
- New plan §"Per-commit Red-output discipline" sub-section
  per the text above.
- New dev-tooling check enumerated in Phase 4's check list:
  add `red_output_in_commit.py` to the canonical target
  list and to the Phase 4 enumeration at line 1583+. Its
  paired test
  (`tests/dev-tooling/checks/test_red_output_in_commit.py`)
  is part of the Phase 4 redo. Add a brief annotation:
  "(activates as a hard gate at Phase 5 exit; informational
  pre-Phase-5-exit)".

### D5 — Plan housekeeping (Version basis + Phase 0 byte-identity + Execution prompt)

**Decision.** Standard plan-level v032-bump edits.

- Plan §"Version basis" preamble adds a v032 decision block
  capturing D1 + D2 + D3 + D4 + D5 plus the redo-as-Phase-5-
  sub-step framing.
- Plan Phase 0 step 1 byte-identity reference bumps to
  `history/v032/PROPOSAL.md`.
- Plan Phase 0 step 2 frozen-status header literal bumps to
  "Frozen at v032".
- Plan Execution-prompt block authoritative-version line
  bumps to v032.

## Companion-doc + repo-state changes paired with v032

- `bootstrap/scratch/pre-redo.zip`: NEW committed binary
  blob (D4.a). Authored as the first step of the redo
  procedure (D2.c step 1), committed to the repo so the
  audit trail is solid. Removed at Phase 11 cleanup via
  `git rm`. The bootstrap skill MUST treat extracting the
  zip during authoring as a discipline violation.
- `python-skill-script-style-requirements.md` §"Test-Driven
  Development": no change required; the section already
  frames TDD as authoring rhythm without a temporal carve-
  out (verified by literal grep for "Phase 5 exit" — zero
  matches).

## Origin commit (none — v032 is the redo authorization, not
the redo execution)

The v032 commit lands the PROPOSAL + plan + .gitignore edits
and creates `history/v032/`. The actual deletion +
re-authoring + report happens as a series of Phase 5
sub-step commits *following* v032's commit. The
`bootstrap/open-issues.md` file gets a NEW entry at v032 commit
time tracking the retroactive-redo work as in-progress, which
gets `Status: resolved` when the v032 D3 quality-comparison
report passes its acceptance criteria and the user gates Phase
5 advance.
