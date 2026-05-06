---
topic: proposal-critique-v12
author: Claude Opus 4.7 (1M context)
created_at: 2026-04-23T22:00:00Z
---

# Critique scope

This critique evaluates **v012 PROPOSAL.md** plus its companions
`python-skill-script-style-requirements.md` and `deferred-items.md`
against the embedded `livespec-nlspec-spec.md` (Architecture-Level
Constraints + Error Handling Discipline + recreatability test +
conceptual fidelity + spec economy + intentional-vs-accidental
ambiguity discipline).

The v012 revision (`history/v012/proposed_changes/proposal-critique-
v11-revision.md`) locked in 15 dispositions (L1-L15) plus one new
governing principle (user-provided extensions get minimal
requirements). v012's four careful-review passes caught 27
inconsistencies (10 + 6 + 6 + 5) across PROPOSAL.md, the style
doc, deferred-items.md, and the revision file itself. This
critique does **not** reopen any v001-v012 disposition.

The findings below are a mix of:

- **recreatability defects** — places where a competent implementer
  building from PROPOSAL.md + style doc + `deferred-items.md` alone
  would be blocked or forced to guess (M1, M2, M6, M7).
- **workflow / discipline gaps** — ambiguities in operational
  contracts that would produce divergent implementations (M3, M4).
- **cross-doc self-consistency residue** that the v012 careful-
  review passes missed (M5, C1-C6).

Items are labelled `M1`-`M7` (major + significant gaps) and `C1`-
`C6` (smaller cleanup). The `M` prefix continues the historical
letter sequence (G-v007, H-v008, I-v009, J-v010, K-v011, L-v012;
`M` for v013). Each item carries one of the four NLSpec failure
modes:

- **ambiguity** — admits multiple incompatible interpretations.
- **malformation** — self-contradiction within or across
  documents.
- **incompleteness** — missing information needed to act
  effectively.
- **incorrectness** — internally consistent but specifies
  behavior that cannot work as written or contradicts an
  established external convention.

Major gap appears first (single largest recreatability blocker),
then significant gaps, then smaller cleanup items.

A "without over-specifying" filter was applied per the v009 I0
architecture-vs-mechanism discipline: every item below names a
constraint, a missing cross-doc reference, or a load-bearing
disambiguation — none prescribes internal mechanism. Items that
would only reshape ROP composition or illustrate "correct" code
shape were rejected before inclusion.

---

## Major gap

The single biggest recreatability blocker.

---

## Proposal: M1-typing-extensions-disposition

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md
- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**incompleteness** (L2 + L7 mandate Python 3.10-only primitives
that require `typing_extensions` on Python 3.10, but v012 explicitly
defers the resolution; a competent implementer cannot run pyright
strict-plus or satisfy `check-assert-never-exhaustiveness` on the
3.10 floor without a disposition).

### Summary

v012 mandates `reportImplicitOverride = "error"` (L2) — which
requires every method override to carry `@override` — and
`case _: assert_never(<subject>)` on every `match` statement (L7).
Both `@override` and `assert_never` live in `typing` from Python
3.11+; on Python 3.10 they are only available via
`typing_extensions`. The python-skill-script-style-requirements.md
records the concern as an "Open dependency follow-up" (line 597-602
of the style doc) but does not codify a disposition. The
`task-runner-and-ci-config` deferred-items entry tracks the
open follow-up with three options (verify transitive vendoring
via dry-python/returns; add direct mise-pinned dev dep; bump
Python floor to 3.11) — but all three options remain unresolved.

The gap is recreatability-blocking for any agent starting
implementation today, because:

1. The 3.10 floor is codified in PROPOSAL.md §Runtime dependencies
   and in `.mise.toml` discipline.
2. Running `@override` on Python 3.10 without `typing_extensions`
   raises `ImportError`.
3. Running `assert_never` on Python 3.10 without
   `typing_extensions` raises `ImportError`.
4. Neither PROPOSAL.md nor the style doc says where to import
   `@override` / `assert_never` from in `livespec/**` code. The
   example at style doc line 1068 shows `from typing import
   assert_never` with a comment "Python 3.11+; on 3.10 use
   typing_extensions" but no rule codifies which one livespec
   actually uses.
5. `check-imports-architecture` (Import-Linter) doesn't know
   about `typing_extensions` as a preferred source.

### Motivation

The v012 revision accepted 5 guardrails that depend on these
two symbols (`@override`, `assert_never`). Without a concrete
disposition, every LLM implementer starting on v013 hits the
same decision point and may resolve it differently, creating
divergent implementations. The recreatability test fails here
today: the spec is silent on a detail an implementer cannot
proceed past without guessing.

The option space is well-characterized by v012's own follow-up
notes. The right move is to pick one and codify it so the
deferred entry can close.

### Proposed Changes

Three options, in order of implementation effort:

**Option A (recommended): Add `typing_extensions` as a direct
mise-pinned dev-only dep; import `@override` and `assert_never`
from `typing_extensions` everywhere in `livespec/**`.** Codify
in the style doc §"Type safety" and deferred-items
`task-runner-and-ci-config`:

> `typing_extensions` (PSF-2.0 via CPython-license compatibility,
> vendored pure-Python on PyPI) is mise-pinned in `.mise.toml` as
> a test-time / dev-tool dep. `@override` and `assert_never` in
> `livespec/**` MUST be imported from `typing_extensions`, not
> from `typing`. The import-source rule applies uniformly
> regardless of Python version; on 3.11+ `typing_extensions`
> re-exports the stdlib symbols transparently.

Rationale: smallest-behavior-change option; maintains 3.10 floor;
keeps a single codepath. `typing_extensions` is already a
transitive dep of `dry-python/returns` (confirm at vendor time;
if not transitive, the direct mise-pin is the fallback). No need
for a per-version `try/except ImportError` block.

Tradeoff: one more mise-pinned dep (~5 mins to add).

**Option B: Bump the Python floor to 3.11 in `.mise.toml` and
PROPOSAL.md §Runtime dependencies; import `@override` and
`assert_never` from stdlib `typing`.** Codify:

> Python 3.11+ is the sole runtime dependency. Features from
> `typing` 3.11+ (`@override`, `assert_never`, `Self`) are
> expected idioms. `typing_extensions` is NOT used.

Rationale: zero additional deps; matches the latest stable
Python; cleaner. Note: Debian 12 ships Python 3.11; Ubuntu 22.04
ships Python 3.10 (3.11 available via deadsnakes); Ubuntu 24.04
ships Python 3.12; macOS via Homebrew installs 3.12+. All major
targets covered.

Tradeoff: widens the "too-old Python" gap for end users on
older-distribution default Pythons (e.g., Ubuntu 22.04). The
`_bootstrap.py` already exits 127 with an actionable install
instruction on too-old Python; the instruction cost is low.

**Option C: Verify transitive availability via
`dry-python/returns`; use whatever works.** At vendor time,
check whether `typing_extensions` is imported by the vendored
`returns` library; if yes, import from `typing_extensions`;
if no, fall back to option A (direct mise-pin).

Rationale: smallest cognitive load today (verify once; proceed).

Tradeoff: the verification is a manual step that must happen
before any code is written; easy to forget; opens a gap if
`dry-python/returns` drops its `typing_extensions` dep
upstream.

My recommendation: **Option A**. The cost is tiny, the disposition
is explicit, and it survives upstream changes. Option B is more
aggressive but reasonable — if you're OK tightening the floor.
Option C preserves optionality but leaves a guessable outcome.

### Resolution

Close the `typing_extensions` follow-up under
`task-runner-and-ci-config` by codifying the chosen option
in the style doc §"Type safety" and PROPOSAL.md §"Runtime
dependencies — Developer-time dependencies." The `.mise.toml`
section in `task-runner-and-ci-config` records the pinned
version (for Option A) or the updated Python floor (for
Option B).

---

## Significant gaps

Each closes a load-bearing gap in the spec.

---

## Proposal: M2-heading-coverage-json-schema

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**incompleteness** (the `heading-coverage.json` example at
PROPOSAL.md line 2107-2110 shows only `heading` and `test`
fields; multiple specification files can have the same `##`
heading text, so the registry cannot disambiguate).

### Summary

PROPOSAL.md §"Testing approach" specifies the
`tests/heading-coverage.json` meta-test registry for rule-
coverage tracking. The registry format example:

```json
[
  { "heading": "Proposed-change file format", "test": "test_propose_change.py::test_multi_proposal_write" }
]
```

The registry is keyed by heading text but has no `spec_file`
field. The template-declared spec files (`spec.md`,
`contracts.md`, `constraints.md`, `scenarios.md`, plus the
spec-root `README.md`) can each have their own `##` headings
and the same heading text CAN legitimately appear in multiple
files. The meta-test verifies "every top-level (`##`) heading
in each specification file has at least one corresponding
per-spec-file test case" (line 2101-2103), but without a
`spec_file` key, the registry cannot distinguish a `"##
Overview"` heading in `spec.md` from a `"## Overview"`
heading in `contracts.md`.

### Motivation

The recreatability test fails: a competent implementer can see
the example format but cannot tell how to handle collisions.
Two reasonable implementers might:

1. Reject duplicate headings across spec files (forcing unique
   heading text across all files).
2. Make the test ID (`test_propose_change.py::test_...`) serve
   as the disambiguator (but tests aren't filed per-spec-file
   — one test could cover a heading in any spec file; the test
   ID isn't self-evident about spec_file).
3. Add a `spec_file` key that implementers have to invent.

Each produces different implementations. This is accidental
ambiguity — the spec could have specified the shape and
didn't.

Separately, the registry shape doesn't clearly state whether
a heading like `"## Scenario: <name>"` in `scenarios.md`
requires a registry entry. Per `livespec` template discipline,
scenario-block headings use `## Scenario: <short-name>`, which
is a `##` heading. Per the meta-test's scope, every `##`
heading needs a test. But per the Gherkin-blank-line format
discipline, each scenario block is a single scenario — the
test coverage would explode. The spec needs to clarify whether
scenario-level `##` headings are in the meta-test's scope or
only "structural" `##` headings.

### Proposed Changes

**Option A (recommended): Extend the registry shape with an
explicit `spec_file` field; exclude scenario blocks from the
meta-test.** Update PROPOSAL.md §"Testing approach" registry
section:

> **Coverage registry**: `tests/heading-coverage.json` maps
> (spec file, heading) pairs to test identifiers:
>
> ```json
> [
>   { "spec_file": "spec.md", "heading": "Proposed-change file format", "test": "test_propose_change.py::test_multi_proposal_write" }
> ]
> ```
>
> The `spec_file` field is the repo-root-relative path to the
> specification file containing the heading. The `heading` field
> is the exact `##` heading text (without the `## ` prefix).
> The `test` field is a pytest node identifier
> (`<path>::<function>`).
>
> **Scope exclusion.** The meta-test skips `##` headings
> whose text begins with a literal `Scenario:` prefix in
> `scenarios.md` (or any other scenario-carrying spec file
> under the template's convention). Scenario blocks are
> exercised by the per-spec-file test for that file's
> `Gherkin` rule; per-scenario registry entries are not
> required.

Rationale: explicit shape with a named field resolves the
ambiguity by construction. Scenario-exclusion prevents the
registry from exploding as scenarios are added.

**Option B: Require unique heading text across all spec files;
enforce uniqueness in the `test_meta_section_drift_prevention`
meta-test.** Codify that heading collisions across files are
a lint error and the registry can stay heading-only.

Rationale: simpler registry shape; adds a cross-file
uniqueness constraint.

Tradeoff: restricts authoring freedom (e.g., "## Overview" is
a common and reasonable heading in multiple files); pushes the
naming discipline into the spec author's workload.

**Option C: Leave the format unspecified; let the implementer
choose.** Intentional-ambiguity disposition.

Rationale: v011 / v012 pushed on recreatability rigor, but
the registry is a testing-internal format — a competent
implementer can work this out.

Tradeoff: the example in PROPOSAL.md doesn't illustrate the
collision handling, so the implementer has to invent; two
independent implementations would diverge.

My recommendation: **Option A**. The meta-test's scope needs to
be unambiguous to a first-contact implementer, and the scenario
exclusion is a practical necessity for the `livespec` template.

### Resolution

Update PROPOSAL.md §"Testing approach" to extend the registry
shape per Option A; add the scenario-heading scope exclusion
to the meta-test description. The `skill-md-prose-authoring`
and `static-check-semantics` deferred-items entries don't need
changes — the format lives in PROPOSAL.md.

---

## Proposal: M3-mutation-testing-bootstrap-workflow

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md
- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**incompleteness** (v012 L13 sets the mutation-testing threshold
at "≥80%, tunable on first real measurement via a new propose-
change cycle"; but the first real measurement may be well below
80%, and the spec is silent on whether this blocks the release-
gate workflow in the meantime).

### Summary

L13 added mutation testing as a release-gate check via `just
check-mutation`. The style doc §"Mutation testing as release-
gate" reads:

> **Threshold:** ≥80% mutation kill rate on `livespec/parse/`
> and `livespec/validate/`. The 80% figure is initial guidance;
> first real measurement against shipping code may surface a
> different appropriate value, in which case the threshold is
> adjusted via a new propose-change cycle.

This leaves an operational gap: the release-tag CI workflow
runs `just check-mutation` with the 80% threshold; on first
measurement at say 45% kill rate, CI blocks the release; the
propose-change cycle to adjust the threshold requires
livespec's own `revise` flow; during that time, either (a)
the threshold has to be relaxed manually in CI (violating
the "just is single source of truth" invariant), (b) the
release is blocked indefinitely, or (c) the threshold block
is disabled entirely.

### Motivation

The recreatability test reveals this: a competent implementer
reading the release-gate contract sees "≥80% or CI fails" but
has no guidance on bootstrapping from an implementation that
hasn't yet been measured. The propose-change-cycle reference
is circular — livespec needs to use its own tooling to adjust
the threshold, but that tooling depends on a working
dev-tooling gate.

Separately, L13 doesn't say HOW `just check-mutation` fails
under-threshold: does it exit non-zero? Does it emit a report?
Does it identify which mutants survived? A CI job failing on
a percentage without mutant identification forces trial-and-
error remediation.

### Proposed Changes

**Option A (recommended): Add a bootstrap-threshold pragma;
require threshold measurement capture.** Extend the style doc:

> **Bootstrap discipline.** Before first release-tag run,
> `pyproject.toml`'s `[tool.mutmut]` threshold is set to a
> wrapping value `75%` (not 80%) and a `.mutmut-baseline.json`
> file records the mutation-kill-rate measurement at initial
> adoption. Subsequent release-tag runs compare against the
> lower of `baseline - 5%` and the `[tool.mutmut]` threshold.
> Once the measured rate exceeds 80% sustainably, the pragma
> collapses to the 80% threshold alone.
>
> **Failure output.** `just check-mutation` MUST emit a
> structured JSON summary to stderr listing each surviving
> mutant's file + line + mutation kind. Implementation detail
> inside the task runner.

Rationale: provides a documented ramp that doesn't require
livespec's own `revise` cycle to bootstrap. The baseline file
is git-tracked; per-release comparison is deterministic and
CI-local.

**Option B: Split `check-mutation` into an advisory (never
blocks) mode initially; promote to blocking after first
stable measurement.** Codify:

> `just check-mutation` runs advisory (exits 0 regardless of
> threshold) until a deferred-items entry's resolution
> promotes it to blocking mode.

Rationale: zero-lift initial adoption; defers the threshold
question entirely.

Tradeoff: advisory mode for indefinite periods defeats the
point of the gate; implementers may forget to promote.

**Option C: Leave the gap; the first-measurement workflow
is implementer discretion.** Intentional-ambiguity.

Tradeoff: implementers have to reinvent a bootstrap discipline
(and may pick inconsistent ones across runs).

My recommendation: **Option A**. The `baseline.json` pattern
matches the `check-types` + pyright baseline pattern mentioned
in the L14 basedpyright disposition; it's a common and well-
understood discipline.

### Resolution

Update the style doc §"Mutation testing as release-gate" with
the bootstrap pragma and failure-output requirement. Extend
`task-runner-and-ci-config` deferred-items entry to list
`.mutmut-baseline.json` as a new tracked file.

---

## Proposal: M4-retry-count-discipline-ambiguity

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**ambiguity** (PROPOSAL.md's Retry-on-exit-4 prose says "up to
3 retries" but it's unclear whether the count includes the
initial invocation, producing either 3 total or 4 total
invocations per retry-exhaustion).

### Summary

PROPOSAL.md §"Per-sub-command SKILL.md body structure" step 4
describes the LLM-driven retry flow on wrapper exit 4:

> **Retry-on-exit-4:** on wrapper exit code `4` (schema
> validation failed; LLM-provided JSON payload did not conform
> to the wrapper's input schema), re-invoke the relevant
> template prompt with the structured error context from stderr
> and re-assemble the JSON payload. Up to 3 retries per
> PROPOSAL.md §"Templates — Skill↔template communication layer";
> abort on repeated failure with a visible user message.

The same §"Templates — Skill↔template communication layer"
(line 1066-1071) says:

> After a configured number of retries (3), the skill aborts
> the sub-command with an error and preserves partial state
> for investigation.

Both refer to "3 retries" or "3 retries total". An implementer
reading "up to 3 retries" reasonably reads:

- **Reading A**: 1 initial invocation + 3 retries = 4 wrapper
  invocations total on the worst case.
- **Reading B**: 3 invocations total (the initial + 2 retries);
  "retries" is synonymous with "attempts".

Two reasonable implementations diverge by one wrapper
invocation, which is observable via timing and LLM prompt count.

### Motivation

Two independent implementers would produce non-interchangeable
retry behavior. This is accidental ambiguity per NLSpec
discipline: the spec could have specified and didn't.

The mapping to the exit-code contract also matters: the
implementation's retry limit affects how quickly the SKILL.md
prose gives up and reports to the user. At 3-total it's 3
schema-validation attempts; at 4-total (1 initial + 3 retries)
it's 4.

### Proposed Changes

**Option A (recommended): Codify "3 retries" as "3 wrapper
invocations following the initial failing invocation, for 4
total invocations maximum."** Update PROPOSAL.md §"Per-sub-
command SKILL.md body structure" and §"Templates — Skill↔
template communication layer":

> **Retry semantics.** On wrapper exit 4, the SKILL.md prose
> re-invokes the relevant template prompt up to 3 times, for
> a worst-case total of 4 wrapper invocations (1 initial + 3
> retries). The initial invocation counts as "attempt 0"; each
> retry increments the count; after "attempt 3" exits 4, the
> skill aborts and reports to the user.

Rationale: matches the plain-English reading of "3 retries";
explicit worst-case count; identifies the edge.

**Option B: Codify "3 total invocations" (initial + 2 retries
maximum).** Change the prose to explicitly say "3 invocations
total."

Rationale: matches the second reading; shorter total time
before user-visible abort.

Tradeoff: renames the existing "retries" language in two
sections (§"Per-sub-command SKILL.md body structure" and
§"Templates — Skill↔template communication layer"); existing
deferred-items entries reference "retries", which may need
updating.

**Option C: Leave the ambiguity; any reasonable retry count
is acceptable.** Intentional-ambiguity disposition.

Tradeoff: two implementations diverge by one invocation; the
user-facing time-to-abort changes.

My recommendation: **Option A**. It minimizes rename churn,
preserves "3 retries" semantically, and captures the edge case
explicitly.

### Resolution

One-line clarification in both sections of PROPOSAL.md. No
companion-doc changes.

---

## Proposal: M5-check-no-inheritance-leaf-intent-vs-semantics

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md
- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**malformation** (v012 L5 revision-file intent statement "multi-
level subclassing of any leaf domain error is forbidden"
contradicts the codified AST-check semantics in `static-check-
semantics` deferred entry, which accept `LivespecError
subclass (transitively; check examines the base's MRO)").

### Summary

The v012 revision file at `history/v012/proposed_changes/
proposal-critique-v11-revision.md` line 346 states:

> - Concrete effect on the LivespecError hierarchy: NO change
>   in declared shape. `LivespecError` is the open base; each
>   subclass (`UsageError`, `ValidationError`, etc.) remains
>   a concrete leaf. Multi-level subclassing of any leaf
>   domain error is forbidden by the rule (the leaf is not
>   in the allowlist).

But the codified AST-check semantics in `deferred-items.md`
line 514-518 (under `static-check-semantics`'s
`check-no-inheritance` subsection) state:

> For every `ast.ClassDef` with non-empty `bases`, inspect
> each base; reject unless base name resolves (by AST-level
> name resolution; imports walked) to one of
> `{Exception, BaseException, LivespecError, Protocol,
> NamedTuple, TypedDict}` OR to a `LivespecError` subclass
> (transitively; check examines the base's MRO).

The phrase "transitively; check examines the base's MRO"
directly contradicts the revision's "leaf is not in the
allowlist" intent. If an LLM implementer writes
`class RateLimitError(UsageError):`, the AST check's
transitive-LivespecError-subclass rule accepts it (UsageError's
MRO contains LivespecError); the revision's leaf-is-closed
intent rejects it. The two readings diverge for every
second-level subclass.

Similarly, the PROPOSAL.md DoD + style doc §"Inheritance and
structural typing" at line 699-707 repeats the allowlist
`{Exception, BaseException, LivespecError, Protocol,
NamedTuple, TypedDict}` or "a `LivespecError` subclass";
"LivespecError subclass" is consistent with the AST check but
inconsistent with the revision's intent.

### Motivation

This is a self-contradiction within v012's record — the
revision file's Disposition-by-item section asserts leaf-is-
closed, and the codified semantics assert open-subclass. An
implementer reading the revision file forms one mental model;
an implementer reading deferred-items.md forms another. NLSpec
discipline says self-contradiction is never intentional.

The right resolution depends on design intent. The open-
subclass reading makes the rule permissive: any future domain
error can inherit from an existing one (e.g., `RateLimitError
(UsageError)` to pick up `UsageError`'s `exit_code = 2`). The
closed-leaf reading makes the hierarchy flat: every new
domain error MUST inherit directly from `LivespecError` and
explicitly set its own `exit_code`.

### Proposed Changes

**Option A (recommended): Accept the codified AST-check
semantics as authoritative; update the revision-file intent
to match.** The permissive "transitive subclass" reading is
what's actually enforced; the revision-file's leaf-closed
phrasing was a retrospective clarification that overshot.

Resolution: note the v012 revision-file intent clarification
in the v013 revision file; update `static-check-semantics`
deferred entry's wording to make the MRO rule explicit (no
change to the AST check):

> **LivespecError-subclass detection semantics.** The rule
> accepts any base whose MRO contains `LivespecError`. A new
> domain error class MAY inherit either directly from
> `LivespecError` or from an existing LivespecError subclass.
> The latter inherits the parent's `exit_code` class attribute
> unless overridden; authors SHOULD explicitly set `exit_code`
> on concrete leaves for readability.

Rationale: matches what an AST walker actually does; matches
how Python exception hierarchies conventionally work (stdlib's
`OSError` → `FileNotFoundError` / `PermissionError` / etc.
hierarchy); preserves `exit_code` override flexibility.

**Option B: Accept the leaf-closed intent; tighten the AST
check.** Change `static-check-semantics` to specify "direct
parent in allowlist only; transitive subclass not accepted";
update the AST check rule.

Rationale: matches the revision file's Disposition-by-item
intent; forces every new domain error to inherit directly from
LivespecError and set its own `exit_code`; simpler mental
model for agent authors.

Tradeoff: rejects otherwise-reasonable patterns like
`RateLimitError(UsageError)` that borrow semantic meaning and
exit-code from a parent. An agent adding a new variant of an
existing error has to reflect on this.

**Option C: Leave the contradiction; let implementer
interpret.** Intentional-ambiguity.

Tradeoff: self-contradiction in a spec is never intentional
per the NLSpec discipline. This is the worst option.

My recommendation: **Option A**. The permissive reading
matches the AST check and Python conventions; the revision-
file phrasing was over-constrained.

### Resolution

Update `static-check-semantics` deferred-items entry's
`check-no-inheritance` subsection to explicitly codify the
MRO-based acceptance rule; the v013 revision file explicitly
notes this supersedes the v012 revision file's leaf-closed
phrasing. PROPOSAL.md and style doc wording is already
consistent with Option A.

---

## Proposal: M6-validate-directory-per-schema-pairing

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness** (PROPOSAL.md's package layout lists
`validate/` as "pure validators (Result-returning, factory
shape)" but enumerates no modules under it; `check-schema-
dataclass-pairing` walks schema ↔ dataclass but doesn't ensure
a validator exists per schema; a competent implementer can't
tell which validators to create).

### Summary

PROPOSAL.md §"Skill layout inside the plugin" lines 133-134
show:

> │   ├── validate/                        # pure validators (Result-returning, factory shape)

No modules are enumerated. Compare this to the other sibling
subdirectories (`parse/`, `io/`, `doctor/static/`, `schemas/`,
`schemas/dataclasses/`), which enumerate specific .py files.
The style doc §"Per sub-package conventions" line 230-237
describes the validator shape:

> **`validate/`** — pure validators using the **factory
> shape**: each validator takes `(payload: dict, schema: dict)`
> and returns `Result[T, ValidationError]`. Callers in
> `commands/` or `doctor/` read schemas from disk via `io/`
> wrappers and pass the parsed dict.

But it doesn't enumerate WHICH validators exist. The schema
registry under `schemas/*.schema.json` (lines 144-150 of
PROPOSAL.md) lists:
- `doctor_findings.schema.json`
- `proposal_findings.schema.json`
- `seed_input.schema.json`
- `revise_input.schema.json`
- `livespec_config.schema.json`
- `proposed_change_front_matter.schema.json`
- `revision_front_matter.schema.json`

Each needs a paired validator at `validate/<name>.py` per the
factory shape — but the rule isn't codified. An implementer
can work out the mapping, but the `check-schema-dataclass-
pairing` rule (line 1471 of the style doc) walks only schema
↔ dataclass, not schema ↔ validator.

### Motivation

Per the recreatability test, an implementer reading PROPOSAL.md
and the style doc can produce the `schemas/dataclasses/*.py`
one-to-one with schemas (enforced by AST). They can work out
that each schema needs a validator too (because the style doc
describes validators). But nothing enforces per-schema validator
existence — if the implementer forgets `validate_revise_input.py`,
the gap is discovered at first use (import-time error or
missing-module error), not at check-time.

Since `check-schema-dataclass-pairing` exists and pairs two
sides, extending it to three sides (schema ↔ dataclass ↔
validator) would close the gap symmetrically.

### Proposed Changes

**Option A (recommended): Codify a 1:1 schema ↔ validator
pairing with a parallel rule in `check-schema-dataclass-
pairing` (or a sibling check).** Update the style doc
§"Per sub-package conventions" and PROPOSAL.md §"Skill
layout inside the plugin":

> Every schema at `schemas/*.schema.json` MUST have a paired
> validator at `validate/<name>.py` (filename matching the
> `$id`-derived snake_case name). The validator exports a
> function `validate_<name>(payload: dict, schema: dict) ->
> Result[<Dataclass>, ValidationError]` where `<Dataclass>`
> is the paired dataclass from `schemas/dataclasses/<name>.py`.
> Paired-triple drift (schema ↔ dataclass ↔ validator) is
> caught by `check-schema-dataclass-pairing`.

And enumerate the v1 validators in PROPOSAL.md's `validate/`
layout:

```
├── validate/                        # pure validators (Result-returning, factory shape)
│   ├── doctor_findings.py
│   ├── proposal_findings.py
│   ├── seed_input.py
│   ├── revise_input.py
│   ├── livespec_config.py
│   ├── template_config.py               (v011 K5)
│   ├── proposed_change_front_matter.py  (deferred: front-matter-parser)
│   └── revision_front_matter.py         (deferred: front-matter-parser)
```

Rationale: extends an existing check to cover a symmetric
enforcement direction; catches implementer omissions at
check-time rather than first-use; matches the existing one-to-
one discipline of schemas ↔ dataclasses.

**Option B: Enumerate `validate/` modules in PROPOSAL.md
without extending the check.** Update the layout tree;
leave the pairing check unchanged.

Rationale: closes the recreatability gap (implementer knows
what to create); avoids AST-check scope widening.

Tradeoff: a forgotten validator is still discovered only at
first use; the symmetry is documented but not enforced.

**Option C: Leave the gap; validators are implementer-worked-
out per-use.** Intentional-ambiguity.

Tradeoff: compromises recreatability.

My recommendation: **Option A**. The existing
`check-schema-dataclass-pairing` already walks both sides;
adding a third walker over `validate/*.py` is additive and
preserves the check's role as drift-catcher. The enumeration
in PROPOSAL.md closes the recreatability gap.

### Resolution

Update PROPOSAL.md §"Skill layout inside the plugin" to
enumerate the v1 validators; update the style doc §"Per
sub-package conventions" and §"Enforcement suite —
`check-schema-dataclass-pairing`" row to include the
three-way pairing; widen `static-check-semantics` deferred-
items entry's `check-schema-dataclass-pairing` subsection
to describe the three-way walk.

---

## Proposal: M7-import-linter-minimum-contract-example

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md
- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**incompleteness** (v012 L15a adopts Import-Linter at the
dev-tooling layer with three declarative contracts replacing
three hand-written AST checks; contract CONFIGURATION is
"implementer choice"; but the contract outcomes are load-
bearing for purity, layering, and raise-discipline enforcement,
and two independent implementers can produce materially
different layer orderings that yield incompatible architectures).

### Summary

The v012 style doc §"Purity and I/O isolation" (line 555-557)
says:

> Enforced by `check-imports-architecture` (Import-Linter
> `forbidden` contract over `parse/` and `validate/` imports;
> see §"Enforcement suite" for the full target list and the
> v012 L15a Import-Linter adoption that replaces v011's
> planned hand-written `check-purity`).

And the deferred-items `static-check-semantics` entry (line
618-642) says:

> Configuration tuning (root packages, includes/excludes,
> contract names) is implementer choice during the
> `enforcement-check-scripts` deferred entry's resolution.

But an implementer reading those prose descriptions doesn't
know:

1. **What the layer ordering is.** "Higher layers may import
   lower but not vice-versa" — which packages are layers? Is
   `commands/` above `doctor/`? Does `doctor/` have its own
   sub-layering (`doctor/` → `doctor/static/` → individual
   check modules)? Two valid readings:
   - `parse/` < `validate/` < `io/` < `doctor/` < `commands/`.
   - `parse/` < `validate/` < `io/` < `commands/` + `doctor/`
     (peers at the same layer, no arrow between them).
2. **What specific modules are in the forbidden contract
   for purity.** The style doc's §"Purity and I/O isolation"
   (line 528-535) enumerates five categories of forbidden
   imports (`io.*`, `subprocess`, filesystem APIs,
   `returns.io.*`, `socket`/`http`/`urllib`) — but Import-
   Linter's `forbidden` contract accepts explicit module
   names, not filesystem-API heuristics. An implementer has
   to translate "filesystem APIs" into a concrete list.
3. **Whether the raise-discipline contract can actually
   detect runtime `raise` statements.** Import-Linter is an
   IMPORT-surface tool; it detects imports, not raise sites.
   The deferred-items description acknowledges this
   ("raise-site AST discipline ... remains the responsibility
   of hand-written `check-no-raise-outside-io`"), but the
   style doc §"Enforcement suite" line 1468 describes
   `check-no-raise-outside-io` as "AST (raise-site portion
   only)"—so the import-surface portion is the Import-Linter
   contract. Concrete form: a `forbidden` contract saying
   "no module outside `io/**` and `errors.py` may import
   `from livespec.errors import LivespecError | <subclass>`."

A competent implementer can produce an Import-Linter config
that passes the test matrix, but three independent
implementers would likely produce three different layer
orderings and three different forbidden-module enumerations.

### Motivation

The v009 I0 architecture-vs-mechanism discipline is the
tension here. Import-Linter CONFIG is genuinely mechanism-
level (specific contract shapes, exclusion globs). But the
OUTCOME (what the suite enforces) is architectural — it
affects which `from X import Y` statements compile. An
under-specified contract surface leaves the architectural
outcome to chance.

A minimum concrete example in the style doc would anchor the
configuration to a specific canonical shape — a Right-Level-
of-Detail example, not a full config — and let the deferred
entry's "implementer choice" cover only the peripheral tuning.

### Proposed Changes

**Option A (recommended): Add a minimum concrete Import-Linter
contract example to the style doc.** Extend §"Enforcement
suite" or §"Purity and I/O isolation":

> ```toml
> [tool.importlinter]
> root_packages = ["livespec"]
>
> [[tool.importlinter.contracts]]
> name = "parse-and-validate-are-pure"
> type = "forbidden"
> source_modules = ["livespec.parse", "livespec.validate"]
> forbidden_modules = [
>   "livespec.io",
>   "subprocess",
>   "returns.io",
>   "socket",
>   "http",
>   "urllib",
>   "pathlib",  # use via io/ wrappers only
> ]
>
> [[tool.importlinter.contracts]]
> name = "layered-architecture"
> type = "layers"
> layers = [
>   "livespec.commands | livespec.doctor",
>   "livespec.io",
>   "livespec.validate",
>   "livespec.parse",
> ]
>
> [[tool.importlinter.contracts]]
> name = "livespec-errors-raise-discipline-imports"
> type = "forbidden"
> source_modules = ["livespec"]
> forbidden_modules = ["livespec.errors"]
> ignore_imports = [
>   "livespec.io.* -> livespec.errors",
>   "livespec.errors.* -> livespec.errors",
> ]
> ```

Caveat in the style doc: "The contract names, layer names,
and ignore-import globs above are illustrative; the
authoritative rules are the three English-language statements
below. Implementers MAY restructure the contracts so long as
(a) imports from `parse/` / `validate/` to effectful modules
are rejected, (b) higher layers do not import lower layers
are rejected, and (c) `LivespecError` subclass imports
outside `io/**` / `errors.py` are rejected."

Rationale: provides a concrete anchor that resolves layer
ordering and forbidden-module enumeration; preserves the
architecture-vs-mechanism principle via the illustrative
caveat; the deferred entry's "configuration tuning is
implementer choice" covers peripheral details.

**Option B: Codify the three rules in prose without a
concrete contract; let the implementer construct the TOML.**
Just describe what each contract enforces; no TOML syntax.

Rationale: architecture-vs-mechanism; the rule is the
outcome, not the syntax.

Tradeoff: three independent implementations can produce
incompatible `[tool.importlinter]` blocks that pass their own
test but miss cases the other rules catch.

**Option C: Leave the deferred entry's "implementer choice"
phrasing intact.** Intentional-ambiguity.

Tradeoff: compromises recreatability at the dev-tooling level.

My recommendation: **Option A**. Import-Linter contracts are
load-bearing for architectural enforcement; the cost of a 20-
line illustrative TOML is low; the illustrative caveat
preserves mechanism freedom.

### Resolution

Add the concrete contract example to the style doc §"Purity
and I/O isolation" or a new §"Import-Linter contracts"
subsection; the deferred entries reference it rather than
re-describe it.

---

## Smaller cleanup items

Typographical, cross-doc, and economy fixes.

---

## Proposal: C1-typo-python-skill-script-script

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**incorrectness** (a section reference contains a double
"script" typo; the reference target in the style doc is
spelled correctly, so the broken reference doesn't resolve).

### Summary

PROPOSAL.md line 392 references:

> See `python-skill-script-script-style-requirements.md`
> §"Property-based testing for pure modules".

The correct filename (and the correct reference used elsewhere
in PROPOSAL.md — see lines 302, 308, 332, 402, 409, 584, 843,
1532, 1602, 1767, 2013, 2095, 2122, 2207, 2213) is
`python-skill-script-style-requirements.md` (single "script").

The four v012 careful-review passes didn't flag this typo.

### Motivation

Simple incorrectness — fix-and-forget.

### Proposed Changes

**Option A (recommended): Replace the typo at line 393.**
Single `replace_all`-safe fix:

> ...(`livespec/parse/`, `livespec/validate/`). See
> `python-skill-script-style-requirements.md` §"Property-
> based testing for pure modules"...

Rationale: one-character fix.

### Resolution

Single edit in PROPOSAL.md.

---

## Proposal: C2-dev-dependency-list-drift

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**malformation** (PROPOSAL.md §"Runtime dependencies —
Developer-time dependencies" enumerates the full v012 dev
tool set but the style doc's §"Dev tooling and task runner"
summary line repeats only the v011 subset).

### Summary

PROPOSAL.md lines 378-386 list the complete v012 dev deps:

> Every tool the enforcement suite requires — `python3`
> (pinned 3.10+ exact), `just`, `lefthook`, `ruff`, `pyright`,
> `pytest`, `pytest-cov`, `pytest-icdiff`, `hypothesis`,
> `hypothesis-jsonschema`, `mutmut`, `import-linter` — is
> managed via `mise` ([github.com/jdx/mise](https://github.com/jdx/mise))
> in a committed `.mise.toml` at the livespec repository root.

But style doc line 1423-1424 says:

> - `.mise.toml` pins tool versions (Python, just, lefthook,
>   pyright, ruff, pytest, pytest-cov, pytest-icdiff).

The style doc's listing is stale — it omits `hypothesis`,
`hypothesis-jsonschema`, `mutmut`, and `import-linter` (all
added in v012 L12, L13, L15a). The v012 careful-review passes
focused on other sections but missed this summary line.

### Motivation

Recreatability: implementer reading the style doc sees an
incomplete tool list; implementer reading PROPOSAL.md sees
the complete list. The style doc claims `.mise.toml` "pins
tool versions" followed by an incomplete enumeration.

### Proposed Changes

**Option A (recommended): Update the style doc's summary line
to match PROPOSAL.md.** Change line 1424:

> - `.mise.toml` pins tool versions (Python, just, lefthook,
>   pyright, ruff, pytest, pytest-cov, pytest-icdiff,
>   hypothesis, hypothesis-jsonschema, mutmut, import-linter;
>   plus `typing_extensions` if M1 Option A is accepted).

Rationale: single-edit fix brings style doc into sync with
PROPOSAL.md.

**Option B: Delete the enumeration; point at PROPOSAL.md as
the authoritative source.** Change to:

> - `.mise.toml` pins every dev tool listed in PROPOSAL.md
>   §"Runtime dependencies — Developer-time dependencies."

Rationale: single source of truth — matches the K8 style-doc-
tree-duplication-removal decision.

My recommendation: **Option B**. Aligns with K8's
single-source-of-truth discipline.

### Resolution

One edit in the style doc §"Dev tooling and task runner."

---

## Proposal: C3-test-bootstrap-naming-convention

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**ambiguity** (PROPOSAL.md's test tree mirrors `scripts/bin/`
but the test filename for `_bootstrap.py` is `test_bootstrap.py`
— drop leading underscore — without codifying the convention;
implementers mapping the rule to other `_`-prefixed modules
can't derive a consistent naming).

### Summary

PROPOSAL.md line 2028 lists `tests/bin/test_bootstrap.py`
(note: single-underscore `test_bootstrap.py`) as the test
covering `bin/_bootstrap.py` (double-underscore-after-slash).
The mirror rule in PROPOSAL.md §"Testing approach" says:

> `tests/livespec/` mirrors `.claude-plugin/scripts/livespec/`
> one-to-one, preserving subdirectory structure.

The mirror rule is described as file-to-file, but pytest's
`test_` prefix convention and Python's import conventions
around leading-underscore-prefixed modules create an edge:

- Mechanical mirror: `_bootstrap.py` → `test__bootstrap.py`
  (double-underscore for the leading-underscore source).
- Pytest-idiomatic: `_bootstrap.py` → `test_bootstrap.py`
  (single underscore; leading underscore stripped).

PROPOSAL.md uses the second convention implicitly. But the
rule isn't codified, so an implementer adding a future
`_internal_helpers.py` has to guess whether the test is
`test__internal_helpers.py` or `test_internal_helpers.py`.

### Motivation

Minor recreatability ambiguity; one-sentence codification
closes it.

### Proposed Changes

**Option A (recommended): Codify the convention in the mirror
rule.** Update PROPOSAL.md §"Testing approach" "Test
organization rules":

> **Leading-underscore handling.** Source modules whose
> filename begins with `_` (e.g., `_bootstrap.py`) use a test
> filename that strips the leading underscore: `test_<name>.py`
> (not `test__<name>.py`). This matches pytest's idiomatic
> `test_` prefix convention and avoids double-underscore
> visual noise.

Rationale: documents the existing choice; future-proofs.

**Option B: Rename the source module to drop the leading
underscore (e.g., `bootstrap.py`).** The leading underscore
is by-convention for "private to the package"; `bin/` isn't
a package in the traditional sense (wrappers aren't imported
by other code — they're shebang executables).

Rationale: eliminates the underscore entirely; no mirror
ambiguity.

Tradeoff: changes an existing module name; the wrapper
shape's `from _bootstrap import bootstrap` line would become
`from bootstrap import bootstrap`; minor cascade.

My recommendation: **Option A**. One-sentence rule; no
cascading changes.

### Resolution

One addition to PROPOSAL.md §"Testing approach — Test
organization rules."

---

## Proposal: C4-types-module-name-stdlib-shadow

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**ambiguity** (v012 L8 names the canonical NewType-aliases
module `livespec/types.py` — shadowing Python's stdlib
`types` module name. The shadow is a minor code-smell under
typical Python convention; nothing breaks, but the choice
isn't acknowledged.)

### Summary

L8 added `livespec/types.py` as the canonical NewType-aliases
location. Style doc and PROPOSAL.md references use
`livespec.types.<NewTypeName>` for the import — absolute-path
resolution, so no stdlib-shadowing runtime conflict.

Inside any module in `livespec/**`, a `from types import
ModuleType` would still resolve to stdlib `types` (absolute
import), not to `livespec/types.py`. A future relative import
`from .types import ModuleType` would resolve to the wrong
one (livespec's, which doesn't have `ModuleType`). But
livespec's style doc bans relative imports via TID
`ban-relative-imports = "all"` — so the scenario is already
precluded.

Still, the shadow is an authoring smell. An IDE's
auto-complete may surface both. An unfamiliar reader seeing
`from livespec.types import Author` may momentarily wonder
why the word `types` is reused.

### Motivation

Low-stakes. But codifying the choice (or renaming) would
avoid a future challenge from a reviewer who doesn't know
the L8 history.

### Proposed Changes

**Option A (recommended): Keep `livespec/types.py`; add a
one-sentence note acknowledging the shadow and why it's OK.**
Update the style doc §"Type safety — Domain primitives via
`NewType`":

> The module name `livespec.types` intentionally echoes the
> stdlib `types` module name. Livespec's banned relative
> imports (TID `ban-relative-imports = "all"`) mean the
> shadow cannot cause import-resolution bugs; absolute
> imports (`from livespec.types import Author` and
> `from types import ModuleType`) disambiguate by package
> root.

Rationale: documents the chosen direction; answers the future
reviewer's question; no code changes.

**Option B: Rename to `livespec/primitives.py` or
`livespec/domain_types.py`.** Single module rename; cascading
updates to every import site (schema dataclasses, context
dataclasses, etc.).

Rationale: eliminates the shadow.

Tradeoff: churn across the package; the `types.py` name is
conventional in many Python projects (e.g., `pandas/core/
arrays/_mixins.py` has `types` in various places) — the rename
removes value only for readers who'd be confused.

**Option C: Leave the gap; the shadow is self-evident.**
Intentional-ambiguity.

Tradeoff: minor; doesn't break anything.

My recommendation: **Option A**. One-line note; zero
cascading changes.

### Resolution

One-sentence addition to the style doc §"Type safety — Domain
primitives via `NewType`."

---

## Proposal: C5-scope-wording-consistency

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**ambiguity** (multiple rules in the style doc use
inconsistent path-scope wording: `.claude-plugin/scripts/
livespec/**`, `scripts/livespec/**`, and `livespec/**` appear
in different places for what is semantically the same scope).

### Summary

The style doc's path-scope wording varies across sections:

- §"Scope" (line 46): `.claude-plugin/scripts/livespec/**`.
- §"Package layout — Per sub-package conventions" (line 204,
  etc.): implicitly `scripts/livespec/<subpath>/`.
- §"Keyword-only arguments" (line 983-984): `scripts/livespec/
  **`, `scripts/bin/**`, `<repo-root>/dev-tooling/**`.
- §"Structural pattern matching" (line 1047-1048): same as
  above.
- §"Code coverage" (line 944-945): `scripts/livespec/**`,
  `scripts/bin/**`, `<repo-root>/dev-tooling/**`.
- §"Type safety" (lines 640, 659, 699, 726): `livespec/**`,
  `bin/**`, `dev-tooling/**` (no prefix).
- Canonical target list (line 1472, 1476, 1479, 1480): `livespec/**`.
- §"Supervisor discipline" (line 376-377): `livespec/**`.

These all refer to the SAME set of files but three different
wording styles. A competent implementer produces a consistent
mental model eventually, but initial reads create unnecessary
cognitive load. Spec-economy concern.

### Motivation

This is the NLSpec §"Spec Economy" discipline: define-once and
reference-by-name. The three wordings mean the same thing;
one of them should be canonical.

### Proposed Changes

**Option A (recommended): Canonicalize on `livespec/**`,
`bin/**`, `dev-tooling/**` (shortest; matches canonical
target list).** Add a one-line note at the top of §"Scope":

> **Scope path conventions.** Throughout this document, the
> shorthand `livespec/**` refers to
> `.claude-plugin/scripts/livespec/**`, `bin/**` refers to
> `.claude-plugin/scripts/bin/**`, and `dev-tooling/**`
> refers to `<repo-root>/dev-tooling/**`. Full paths appear
> only where a distinct location (e.g., the vendored-lib tree
> at `_vendor/**`) requires disambiguation.

Then sweep the style doc to replace `scripts/livespec/**`
→ `livespec/**`, etc.

Rationale: shortest wording; matches the canonical target
list; one consistent reading.

**Option B: Canonicalize on the full-path form
`.claude-plugin/scripts/livespec/**`.** Long wording but
maximally explicit.

Tradeoff: verbose; repeats the prefix many times.

**Option C: Leave the inconsistency; reader infers from
context.** Intentional-ambiguity / style preference.

Tradeoff: mild cognitive tax on the reader.

My recommendation: **Option A**. Short form matches canonical-
list wording; one-line note codifies the shortcut.

### Resolution

One-sentence addition at the top of §"Scope"; global
replace-all to canonicalize existing wording.

---

## Proposal: C6-livespec-author-llm-env-var-precedence-wording

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**ambiguity** (PROPOSAL.md §"Environment variables" says
`LIVESPEC_AUTHOR_LLM` "unconditionally" sets the author field
— the word "unconditionally" creates an apparent conflict
with the later-documented CLI-wins precedence).

### Summary

PROPOSAL.md line 886-894 describes the env var:

> - **`LIVESPEC_AUTHOR_LLM`** (default unset). When set and
>   non-empty, the `propose-change`, `critique`, and `revise`
>   wrappers use this value for the `author` payload/file-
>   front-matter field unconditionally (and for the `author_llm`
>   field on revision-file front-matter, where applicable),
>   overriding any LLM self-declaration in the JSON payload
>   and the `"unknown-llm"` fallback.

"Unconditionally" is the problematic word. The author-
identifier resolution rules in three places (§"propose-change",
§"critique", §"revise", §"Revision file format") all say:

1. CLI `--author <id>` (if non-empty).
2. Env var `LIVESPEC_AUTHOR_LLM` (if non-empty).
3. LLM self-declared `author` field in payload.
4. Literal `"unknown-llm"`.

So CLI wins over env var; env var doesn't "unconditionally"
win. A reasonable reading of the env var section alone would
be "even if `--author` is also on the CLI, the env var wins"
— which is wrong per the other sections.

### Motivation

Malformation-adjacent: two sections describe the same
precedence but one uses a misleading qualifier. Reader must
cross-reference to disambiguate.

### Proposed Changes

**Option A (recommended): Replace "unconditionally" with a
phrasing that matches the documented precedence.** Update
§"Environment variables" to say:

> - **`LIVESPEC_AUTHOR_LLM`** (default unset). When set and
>   non-empty, the `propose-change`, `critique`, and `revise`
>   wrappers use this value for the `author` payload/file-
>   front-matter field (and for the `author_llm` field on
>   revision-file front-matter, where applicable), overriding
>   the LLM-self-declared `author` in the JSON payload and the
>   `"unknown-llm"` fallback. A `--author <id>` CLI flag on
>   the invocation still wins over the env var per the unified
>   precedence rules (see §"propose-change → Author identifier
>   resolution", §"critique", §"revise", and §"Revision file
>   format").

Rationale: removes the misleading qualifier; explicitly notes
CLI-wins; cross-references the authoritative precedence rules.

**Option B: Leave "unconditionally" and add a parenthetical
exception for CLI.** Minor edit:

> ...use this value for the `author` payload/file-front-
> matter field unconditionally (except when `--author` is
> passed on the CLI — see unified precedence below)...

Rationale: shortest change.

Tradeoff: still leads with the "unconditionally" framing,
which confuses the reader's initial scan.

**Option C: Leave the gap; readers cross-reference.**
Intentional-ambiguity.

Tradeoff: the spec economy principle (define-once and name-
the-definition) is mildly violated; readers do extra work.

My recommendation: **Option A**. Clear up-front precedence;
explicit cross-reference.

### Resolution

One-paragraph edit in PROPOSAL.md §"Environment variables."

---

## Summary

Thirteen items total:

| Item | Failure mode | Severity | Doc(s) touched |
|---|---|---|---|
| M1 | incompleteness | major | PROPOSAL.md + style doc + deferred-items |
| M2 | incompleteness | significant | PROPOSAL.md |
| M3 | incompleteness | significant | style doc + deferred-items |
| M4 | ambiguity | significant | PROPOSAL.md |
| M5 | malformation | significant | style doc + deferred-items |
| M6 | incompleteness | significant | PROPOSAL.md + style doc |
| M7 | incompleteness | significant | style doc + deferred-items |
| C1 | incorrectness | small | PROPOSAL.md |
| C2 | malformation | small | style doc |
| C3 | ambiguity | small | PROPOSAL.md + style doc |
| C4 | ambiguity | small | PROPOSAL.md + style doc |
| C5 | ambiguity | small | style doc |
| C6 | ambiguity | small | PROPOSAL.md |

None of the items reopens a v001-v012 disposition. M1 is
the load-bearing item — without it, agents starting on v013
hit a blocking decision point. M2 and M6 are the two largest
residual recreatability gaps. M3 and M4 are operational-
semantics ambiguities. M5 is a self-contradiction the v012
review passes missed. M7 is the outcome-load-bearing side of
L15a's "implementer choice" wording. C1-C6 are cross-doc
consistency cleanups.
