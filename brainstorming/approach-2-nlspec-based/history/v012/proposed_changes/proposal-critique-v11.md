---
topic: proposal-critique-v11
author: Claude Opus 4.7 (1M context)
created_at: 2026-04-23T18:00:00Z
---

# Critique scope

This critique evaluates **v011 PROPOSAL.md** plus its companions
`python-skill-script-style-requirements.md` and `deferred-items.md`
against the embedded `livespec-nlspec-spec.md`'s
"Architecture-Level Constraints" + "Error Handling Discipline"
sections. Lens: **strongest-possible mechanical guardrails for
agent-authored Python**, with a functional-programming + type-
safety bias per user direction.

The v011 revision (`history/v011/proposed_changes/proposal-critique-
v10-revision.md`) locked in 11 dispositions (K1-K11): orphaned
`commands/doctor.py` removed; `resolve_template.py` six-invariant
contract codified; wrapper coverage via per-wrapper tests; project-
wide keyword-only-args + keyword-only-match-pattern discipline;
template-shape decoupling from `livespec-nlspec-spec.md`; three-
category doctor extensibility (`doctor_static_check_modules`,
`doctor_llm_objective_checks_prompt`,
`doctor_llm_subjective_checks_prompt`); `--run-pre-check` narration
asymmetry; full domain-term rename `reviser` → `author` with
uniform `--author` CLI; style-doc layout-tree duplication removed;
`livespec-` prefix demoted to convention; doctor-static domain-
failure-to-fail-Finding discipline; `schemas/dataclasses/` test-
tree visibility. This critique does **not** reopen any of those
dispositions, nor any earlier v001-v010 disposition.

The findings below are **not recreatability defects** in the v011
sense — a competent implementer can still produce a working v011
livespec from PROPOSAL.md + the style doc + `deferred-items.md`
alone. They are **agent-guardrail incompletenesses**: places where
v011's enforcement suite leaves room for an LLM implementer to
make a bad choice that pyright-strict + the existing checks would
not catch. The principle they exercise is the v005+
"strongest-possible guardrails for agent-authored Python" memory,
applied with a bias toward functional-programming + type-safety
patterns.

Items are labelled `L1`-`L15` (the `L` prefix continues the
historical sequence: `G`-v007, `H`-v008, `I`-v009, `J`-v010,
`K`-v011, `L`-v012). Each item carries one of the four NLSpec
failure modes:

- **ambiguity** — admits multiple incompatible interpretations.
- **malformation** — self-contradiction within or across
  documents.
- **incompleteness** — missing information needed to act
  effectively (here: missing a guardrail that would otherwise
  prevent a known LLM bad-choice pattern).
- **incorrectness** — internally consistent but specifies
  behavior that cannot work as written or contradicts an
  established external convention.

Major gaps appear first (single largest hole in the ROP
discipline), then significant gaps (each closes a wide
bad-choice space), then smaller cleanup (defense-in-depth).

A "without over-specifying" filter was applied: every item below
is mechanical (a `pyproject.toml` setting, a ruff rule code, a
small AST check, or a vendored library) — none adds prose
describing how to write code beyond a one-line constraint
statement. Items that would describe internal mechanism (e.g.,
"use `flow()` for chains of 3+ steps") were rejected before
inclusion per the v009 I0 architecture-vs-mechanism discipline.

---

## Major gap

The single biggest hole in v011's enforcement of the ROP
discipline.

---

## Proposal: L1-pyright-report-unused-call-result

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness** (pyright strict mode does not by default flag
a discarded `Result` / `IOResult` return value; the v011
enforcement suite has no other check that catches this pattern).

### Summary

The v011 style doc mandates pyright strict mode and requires
every public function to return `Result[_, _]` or `IOResult[_, _]`
(check-public-api-result-typed). But pyright strict does NOT
enable `reportUnusedCallResult`. So an LLM can write
`my_function(ctx)` instead of `result = my_function(ctx)`,
silently discarding the entire failure track. The railway derails
without a single tool complaining. For a codebase whose ENTIRE
error-handling contract rests on Result composition, this is the
single largest agent-guardrail hole.

### Motivation

The v005+ memory "strongest-possible guardrails for agent-
authored Python" calls for mechanical purity/coupling enforcement
where pyright + dry-python/returns leave agents minimal room for
bad choices. Discarding a `Result` is the canonical bad choice in
ROP code: it converts an exhaustively-typed failure path into a
silent no-op. The fix is one line in `[tool.pyright]`. No prose
about "always handle Result values" needed in the style doc;
pyright will refuse to type-check code that doesn't.

The cost is one type-checker diagnostic per legitimate fire-and-
forget pattern (none in livespec — every `Result` carries failure
information meant to be observed). The benefit is a hard guarantee
that no LLM-generated code can swallow an error-track value.

### Proposed Changes

Three options, in increasing strictness:

**Option A (recommended): Enable `reportUnusedCallResult = "error"`
in `[tool.pyright]`.** Add to the python style doc §"Type safety":

> The `[tool.pyright]` configuration MUST set
> `reportUnusedCallResult = "error"` so that any discarded
> `Result` / `IOResult` (or other non-`None`-returning call
> result) is a type error. The rule has no exceptions in
> `livespec/**`; supervisor side-effect calls (e.g.,
> `log.info(...)` returning `None`) are unaffected because
> `None` returns are not flagged.

Rationale: closes the largest ROP hole with a one-line config
change. Aligns with the v005+ guardrails memory.

**Option B: Enable only on `livespec/parse/` and `livespec/validate/`.**
Narrower scope; allows other modules to discard call results.

Rationale: limits scope but leaves `commands/` and `doctor/` —
where ROP composition matters most — uncovered.

**Option C: Don't enable; document the convention in prose.**

Rationale: matches v009 I0 "specify architecture, not mechanism" by
not over-specifying — but this is a config-level architecture
constraint, not mechanism, so the principle does not apply here.

---

## Significant gaps

Each of these closes a wide LLM bad-choice space with a small
config change or AST check.

---

## Proposal: L2-pyright-strict-plus-options

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness** (pyright strict mode does not enable several
diagnostics that meaningfully tighten LLM-authored code; v011
relies only on the strict baseline).

### Summary

v011's style doc enables `typeCheckingMode = "strict"` but does
not enable any of the strict-plus diagnostics pyright supports
above the strict baseline. Five of these are highly relevant to
LLM-authored ROP code; one is a security-relevant tightening.

The candidates:

- `reportImplicitOverride = "error"` — every method override
  must carry the `@override` decorator (from `typing` in 3.12+
  or `typing_extensions` for 3.10+). Renaming a base-class method
  silently breaks overrides without `@override`; this catches it.
- `reportUninitializedInstanceVariable = "error"` — every
  instance attribute must be initialized in `__init__` or have a
  class-level default. Pairs with the project-wide
  `@dataclass(frozen=True, kw_only=True)` rule already in K4.
- `reportUnnecessaryTypeIgnoreComment = "error"` — flags
  `# type: ignore` comments that no longer suppress any
  diagnostic. Forces LLMs to remove stale ignores rather than
  leaving them as deadweight markers.
- `reportUnnecessaryCast = "error"` — flags
  `cast(X, value)` where `value` is already typed `X`. Catches
  defensive over-casting LLMs frequently produce.
- `reportUnnecessaryIsInstance = "error"` — flags
  `isinstance(x, T)` where the type checker already knows `x: T`.
  Same defensive-bloat pattern.
- `reportImplicitStringConcatenation = "error"` — catches the
  `["foo" "bar"]` (missing comma) class of bug that LLMs hit when
  generating long string lists, especially in dataclass field
  defaults or schema enumerations.

### Motivation

Each of these closes a documented LLM-authored-code failure
pattern with a one-line config change. They also compose with
v011's K4 keyword-only-args rule: `reportUninitializedInstance
Variable` reinforces dataclass-construction completeness, and
`reportImplicitOverride` reinforces the flat-composition
direction K4 implicitly suggests by mandating keyword-only
constructors.

### Proposed Changes

**Option A (recommended): Enable all six.**

Add to the python style doc §"Type safety" `[tool.pyright]`
configuration block:

```
reportImplicitOverride = "error"
reportUninitializedInstanceVariable = "error"
reportUnnecessaryTypeIgnoreComment = "error"
reportUnnecessaryCast = "error"
reportUnnecessaryIsInstance = "error"
reportImplicitStringConcatenation = "error"
```

(`@override` requires `from typing_extensions import override`
on Python 3.10/3.11 — `typing_extensions` would need to be added
to the vendored libraries, OR `dry-python/returns`'s existing
typing_extensions transitive can be reused if vendored already.
Verify before landing.)

**Option B: Enable a subset (drop `reportImplicitOverride` if
adding `typing_extensions` to vendored libs is undesirable).**

**Option C: Enable none; document strict-plus considerations in
deferred-items for later evaluation.**

Recommendation: **A**, contingent on verifying
`typing_extensions` availability. If unavailable and the user
prefers to avoid a new vendored dep, fall back to **B**
(everything except `reportImplicitOverride`).

---

## Proposal: L3-ruff-rule-selection-expansion

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness** (v011's ruff rule selection
`E F I B UP SIM C90 N RUF PL PTH` covers style + complexity +
basic anti-patterns + path-handling but omits several rule
categories that close known LLM bad-patterns).

### Summary

v011 style doc §"Linter and formatter" enables 11 ruff rule
categories. There are ~12 additional categories that meaningfully
tighten agent-authored code. Each adds zero install cost (already
in ruff) and matches v011's discipline directions:

- `TRY` — tryceratops exception-handling discipline. **Highly
  relevant to v011's domain-vs-bugs split.** Catches: `raise X`
  inside try without `from`; redundant `raise` in `except` block;
  long error messages in raise; missing `else` block when
  try-body is too broad. Reinforces v009 I10 + K10.
- `FBT` — flake8-boolean-trap. Forbids boolean POSITIONAL
  arguments. Reinforces v011 K4's keyword-only discipline (FBT001
  catches positional bool args; K4's check-keyword-only-args
  catches all positional args, but FBT predates that and is
  battle-tested at this specific class of bug).
- `PIE` — flake8-pie anti-patterns. Catches: `pass` in non-empty
  block; `del` outside `__del__`; redundant dict comprehensions;
  multiple `startswith`/`endswith` calls that should be one.
- `SLF` — flake8-self. Forbids accessing
  `_`-prefixed attributes from outside the defining class.
  Reinforces v005+ check-private-calls semantically.
- `LOG` + `G` — flake8-logging + flake8-logging-format. Forbids
  f-strings in log calls; mandates kwargs for context. Reinforces
  v011 §"Structured logging" style rule.
- `TID` — flake8-tidy-imports. Forbids relative imports
  (livespec uses absolute imports throughout); forbids banned
  modules.
- `ERA` — eradicate. Forbids commented-out code (a frequent LLM
  artifact: the LLM keeps a previous attempt as a comment "in
  case").
- `ARG` — unused arguments. Forbids unused function/method
  arguments. Catches signature-vs-implementation drift.
- `RSE` — flake8-raise. Forbids `raise X()` when `raise X` works;
  enforces `raise ... from ...` discipline (pairs with TRY).
- `PT` — flake8-pytest-style. Pytest-specific anti-patterns:
  `pytest.raises(Exception)` too broad, `parametrize` value
  shapes, fixture decorators.
- `FURB` — Refurb refactor hints. Modern-Python idiom catchers
  (e.g., `Path.read_text()` over `with open(p) as f: f.read()`).
- `SLOT` — flake8-slots. Mandates `__slots__` on `NamedTuple` /
  `tuple`-subclass / `str`-subclass classes. Pairs with
  hypothetical L4 (`@dataclass(slots=True)`).
- `ISC` — flake8-implicit-string-concat. Catches the same
  `["foo" "bar"]` class as L2's `reportImplicitStringConcat`,
  but at lint level rather than type level. Some redundancy with
  L2 is acceptable; ISC catches additional cases L2 doesn't (in
  list/set/tuple contexts).

### Motivation

These rule categories collectively close ~50 distinct LLM-
authored anti-patterns documented in agent-coding research.
Adding them is one comma-separated list edit in `pyproject.toml`.
The cost is the upfront one-time refactoring of any existing
violations; the benefit compounds across every future LLM-
generated PR.

### Proposed Changes

**Option A (recommended): Add all 12 to the rule selection.**

Replace v011 style doc rule list:

`E F I B UP SIM C90 N RUF PL PTH`

With:

`E F I B UP SIM C90 N RUF PL PTH TRY FBT PIE SLF LOG G TID ERA ARG RSE PT FURB SLOT ISC`

Plus per-category configuration for the few that need tuning
(e.g., `[tool.ruff.lint.flake8-tidy-imports]` ban relative
imports).

**Option B: Add high-leverage subset (TRY + FBT + LOG + G + ERA
+ ARG + RSE + ISC).** Skips the more opinionated categories
(PIE, SLF, FURB, SLOT, PT).

**Option C: Add as deferred-items entry; evaluate per-category
on a follow-up pass.**

Recommendation: **A** — every category is well-established in
2026 Python tooling and aligned with v011's existing discipline
direction. None requires prose explanation in the style doc
beyond the rule-code listing.

---

## Proposal: L4-dataclass-slots-true

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness** (v011 K4 mandates
`@dataclass(frozen=True, kw_only=True)` but does not mandate
`slots=True`).

### Summary

v011's K4 disposition mandates the `frozen=True, kw_only=True`
pair on every `@dataclass`. The third member of the standard 2026
"strict dataclass" triple is `slots=True`. Effect:

- Allocates `__slots__` instead of `__dict__`. Means an attribute
  typo at construction or update site (e.g., `ctx.spec_rooot`
  instead of `ctx.spec_root`) raises `AttributeError` at the
  access site rather than silently creating a new attribute.
- Reduces per-instance memory ~30% (small, but free).
- Forbids dynamic attribute attachment — which v011's discipline
  already implicitly forbids by virtue of `frozen=True`, but
  `slots=True` makes it observable at the wrong-name case too.

The reason `slots` has tradeoffs in general Python: it breaks
`__weakref__` and prevents multiple inheritance with non-slots
classes. Neither matters in livespec (no weakref usage; no
multiple inheritance permitted).

### Motivation

LLM-authored code frequently reaches for slightly-misspelled
attribute names. `frozen=True` catches assignment after
construction; `slots=True` catches the additional case of a
typo at construction or read. The pair is strictly stronger than
either alone.

### Proposed Changes

**Option A (recommended): Mandate `slots=True` alongside K4's
existing `frozen=True, kw_only=True`.**

Update the K4 rule wording in the style doc:

> Every `@dataclass` MUST be declared with
> `@dataclass(frozen=True, kw_only=True, slots=True)`.

The existing `check-keyword-only-args` AST walker (added in K4)
already inspects `@dataclass` decorator keyword arguments to
verify `kw_only=True`. Extend it to verify `slots=True` and
`frozen=True` also. No new AST check needed.

**Option B: `slots=True` SHOULD; keep MUST only on `frozen=True,
kw_only=True`.**

**Option C: Leave for a later pass; track as deferred-items
entry.**

Recommendation: **A** — the cost is two characters in the
decorator and one extra check inside the existing K4 AST walker.

---

## Proposal: L5-final-classes-no-inheritance

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**ambiguity** (v011 does not explicitly forbid class inheritance
inside `livespec/**`; the `LivespecError` hierarchy is the only
documented inheritance chain, but the rule is implicit, not
codified).

### Summary

v011 makes heavy use of `@dataclass(frozen=True)` value classes
+ structural-pattern-matching dispatch. There is no concrete-class
inheritance anywhere in the documented design except the
`LivespecError` exception hierarchy. But the spec does not
explicitly forbid inheritance; an LLM could introduce a
`class FastDoctorContext(DoctorContext): ...` subclass at any
time without violating any current rule.

The functional-programming + type-safety idiom that v011 already
embodies is "flat composition over inheritance." Codifying this
makes the implicit explicit.

Two complementary mechanisms close the gap:

- **`@final` on every concrete class** (from `typing` in 3.11+
  or `typing_extensions` for 3.10+). Pyright then flags any
  attempt to subclass a `@final` class.
- **AST check `check-no-inheritance`**: forbids `class X(Y):`
  in `livespec/**` where `Y` is not in the allowlist
  `{Exception, BaseException, LivespecError, Protocol,
  NamedTuple, TypedDict}` (and `LivespecError` subclasses are
  permitted to extend `LivespecError` per v011's domain-error
  hierarchy).

### Motivation

The v005+ guardrails memory + the K4 keyword-only mandate both
push toward "flat composition; explicit dispatch." Class
inheritance reintroduces the implicit-override and Liskov-
violation bad-choice spaces that pyright + structural matching
were chosen to avoid. Closing this with `@final` + an AST
check makes the architectural direction enforceable rather than
conventional.

### Proposed Changes

**Option A (recommended): `@final` decorator MUST appear on
every concrete (non-`Protocol`, non-`LivespecError`) class.
Plus add `check-no-inheritance` to the canonical `just` target
list.**

Add to the style doc §"Type safety":

> Every concrete class in `livespec/**` MUST be decorated with
> `@typing.final` (Python 3.11+) or
> `@typing_extensions.final` (Python 3.10). Exempt:
> `LivespecError` and its subclasses (which form a documented
> exception hierarchy); `typing.Protocol` definitions (which
> exist to be implemented).
>
> The AST check `check-no-inheritance` rejects any class
> definition `class X(Y):` in `livespec/**` where `Y` is not
> in the allowlist `{Exception, LivespecError, Protocol,
> NamedTuple, TypedDict}` or a `LivespecError` subclass.

**Option B: Add `check-no-inheritance` only; skip the `@final`
mandate.** Cheaper but leaves cross-package subclass attempts
undetectable until the AST check runs.

**Option C: Document as a SHOULD in prose; no enforcement.**

Recommendation: **A** — both mechanisms compose.

---

## Proposal: L6-protocol-over-abc

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness** (v011 has no rule against `abc.ABC` /
`@abstractmethod`; an LLM could introduce an `ABC`-based
interface where a `typing.Protocol` is the structural-typing
idiom v011's rest of the design favors).

### Summary

Python has two interface mechanisms: `abc.ABC` + `@abstractmethod`
(nominal subclassing) and `typing.Protocol` (structural typing).
v011's design uses dataclass-based payloads + functional
composition exclusively — there are no abstract base classes in
the documented architecture. But there is no rule preventing one
from being introduced.

`Protocol` is the structural-typing idiom that fits v011's
direction:

- No subclassing required to "implement" a Protocol — any class
  with the right shape satisfies it.
- Pyright statically checks Protocol conformance at the call
  site, not at the class-definition site.
- Composes with `@final` (L5) — concrete classes are final;
  interfaces are Protocols.

### Motivation

Same direction as L5 (flat composition; structural rather than
nominal typing). Closes a known LLM bad-choice: when asked for
"an interface for X," LLMs default to `class X(ABC): ...` with
`@abstractmethod` because that's what most training-set Python
does. The v011 design wants Protocol; an explicit rule + check
keeps LLMs on the structural-typing rail.

### Proposed Changes

**Option A (recommended): Forbid `abc.ABC` / `@abstractmethod`
inside `livespec/**`; mandate `typing.Protocol` for structural
interfaces.**

Add to the style doc §"Type safety":

> Structural interfaces in `livespec/**` MUST be declared via
> `typing.Protocol`. `abc.ABC`, `abc.ABCMeta`, and
> `@abstractmethod` MUST NOT be used. Enforced by AST check
> `check-no-abc` (rejects imports of `abc.ABC`, `abc.ABCMeta`,
> and uses of `@abstractmethod`).

**Option B: SHOULD use Protocol; no AST check.**

**Option C: No rule; trust the rest of the design to make ABCs
unidiomatic.**

Recommendation: **A** — pairs naturally with L5 and is one tiny
AST check. The whole rule fits in one ruff `flake8-builtins`-
style import-banned configuration; a custom AST check is barely
needed.

---

## Proposal: L7-assert-never-exhaustiveness

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness** (v011 uses structural pattern-matching
extensively — supervisors pattern-match on `IOResult` /
`HelpRequested` / `LivespecError`-subclass — but the spec does
not require an exhaustiveness terminator on `match` statements,
so adding a new variant fails silently at runtime rather than at
type-check time).

### Summary

Python's `typing.assert_never(x)` (3.11+ stdlib;
`typing_extensions` for 3.10+) is the canonical exhaustiveness-
check mechanism. Pattern:

```python
match err:
    case ValidationError():
        return 4
    case PreconditionError():
        return 3
    case _:
        assert_never(err)
```

If a new `LivespecError` subclass is added later but no `case`
arm handles it, pyright errors at the `assert_never(err)` line
because the unhandled subclass narrows the residual type to
something non-`Never`. Without the `assert_never` terminator,
the `case _:` arm catches the new variant silently and the
supervisor returns the wrong exit code.

This is exactly the pattern v011's K10 supervisor + K5 doctor-
extensibility design depends on: new check categories, new
LivespecError subclasses, new `IOResult` variants must propagate
into every dispatch site or the type checker must catch the
gap.

### Motivation

The v011 design is "pattern-match on tagged unions everywhere";
the design falls apart silently when a new variant is added
without updating every dispatch site. `assert_never` makes the
"silently" into "type-check error." One-line discipline; huge
behavioral guarantee.

### Proposed Changes

**Option A (recommended): Mandate `assert_never` terminator on
every `match` statement over an Enum, `Literal`-union, or
discriminated-class union.**

Add to the style doc §"Type safety":

> Every `match` statement in `livespec/**` whose subject type is
> an Enum, `Literal`-union, or a discriminated union of dataclass
> / Exception / Protocol classes MUST terminate with
> `case _: assert_never(<subject>)`. Enforced by AST check
> `check-assert-never-exhaustiveness`.

The check walks each `ast.Match` node in `livespec/**`,
inspects the inferred subject type (deferred to pyright via a
separate dump pass, OR conservatively requires the terminator
on every `match` statement and accepts a small over-strictness
cost), and verifies the final `case _:` body is exactly
`assert_never(<subject-name>)`.

**Option B: SHOULD use `assert_never`; rely on pyright's own
exhaustiveness diagnostic without the AST check.**

The downside: pyright's exhaustiveness inference fails on many
non-trivial Match patterns (documented mypy/pyright limitation).
The explicit terminator is more reliable than implicit
exhaustiveness inference.

**Option C: Document as a convention; no enforcement.**

Recommendation: **A** — the AST check is small (one walk over
`ast.Match` nodes) and catches the highest-impact regression
class for v011's pattern-match-everywhere design.

---

## Proposal: L8-newtype-domain-primitives

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**ambiguity** (v011 dataclass field declarations use raw `str`
/ `int` / `Path` for fields with strong domain meaning —
`check_id`, `run_id`, `spec_root`, `template_name`, `topic`,
schema `$id`, `author`, `slug` — so two fields of the same raw
type can be cross-wired without any type error).

### Summary

`typing.NewType` creates zero-runtime-cost type aliases that
the type checker treats as distinct types. Pattern:

```python
from typing import NewType

CheckId = NewType("CheckId", str)
RunId = NewType("RunId", str)
TopicSlug = NewType("TopicSlug", str)
SpecRoot = NewType("SpecRoot", Path)
SchemaId = NewType("SchemaId", str)
TemplateName = NewType("TemplateName", str)
Author = NewType("Author", str)

# Construction:
check_id: CheckId = CheckId("doctor-out-of-band-edits")

# Cross-wiring caught:
def run_check(check_id: CheckId) -> ...: ...
run_check(RunId("..."))  # pyright error
```

v011 has many places where these distinct concepts share a raw
`str`. Examples from PROPOSAL.md: `Finding.check_id` (slug),
`DoctorContext.run_id` (UUID), `LivespecConfig.template`
(template name), front-matter `author`, schema `$id`, history
version `vNNN` strings.

### Motivation

The classic LLM bad-choice in raw-string codebases: passing the
right shape but the wrong meaning. NewType eliminates the entire
class with one declaration each. Combined with K4 keyword-only
arguments (which prevent positional cross-wiring), NewType
prevents nominal cross-wiring.

### Proposed Changes

**Option A (recommended): Define a NewType per domain primitive;
mandate at the dataclass-field-declaration layer.**

Add to the style doc §"Type safety":

> Domain identifiers in `livespec/**` MUST use a `typing.NewType`
> alias. The canonical aliases live in
> `livespec/types.py`:
>
> - `CheckId = NewType("CheckId", str)` — doctor-static check
>   slug.
> - `RunId = NewType("RunId", str)` — per-invocation UUID.
> - `TopicSlug = NewType("TopicSlug", str)` — proposed-change
>   topic.
> - `SpecRoot = NewType("SpecRoot", Path)` — resolved spec
>   root path.
> - `SchemaId = NewType("SchemaId", str)` — JSON Schema `$id`.
> - `TemplateName = NewType("TemplateName", str)` —
>   `.livespec.jsonc` template field.
> - `Author = NewType("Author", str)` — author identifier
>   (per K7 rename; covers human + LLM authors).
> - `VersionTag = NewType("VersionTag", str)` — `vNNN` version
>   identifier.
>
> Dataclass fields and function signatures handling these
> concepts MUST use the NewType, not the underlying primitive.
> Enforced by AST check `check-newtype-domain-primitives`
> (walks `schemas/dataclasses/*.py`, verifies field annotations
> for the listed roles use the corresponding NewType).

**Option B: Define the NewTypes; document as a SHOULD; no AST
check.** Lower enforcement guarantee.

**Option C: Document as deferred-items entry; let post-seed
`livespec propose-change` handle the per-field NewType
introduction.**

Recommendation: **A** is strongest but requires defining the
canonical NewType list now. **C** defers the work; **B** is the
middle path. User-choice question.

---

## Smaller cleanup

Defense-in-depth additions; each closes a narrow but real bad-
choice.

---

## Proposal: L9-explicit-all-per-module

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness** (no rule requires every `livespec/**` module
to declare `__all__`, so what counts as "public API" is
implicit).

### Summary

v011's `check-public-api-result-typed` AST check enforces a
return-type constraint on every "public" function — but it
infers public-vs-private from the leading-underscore convention,
not from `__all__`. Adding a per-module `__all__: list[str]`
declaration makes the public API surface explicit and machine-
inspectable.

### Motivation

LLM bad-choice: forgetting to mark a helper private with `_`,
exposing it as public API. `__all__` flips the discipline:
nothing is public unless explicitly exported. Pairs cleanly
with `check-public-api-result-typed` and `check-private-calls`.

### Proposed Changes

**Option A (recommended): Mandate `__all__` declared at
module-top in every `livespec/**` module.** New AST check
`check-all-declared`. Public-API checks scope to names in
`__all__` rather than to non-`_`-prefixed names.

**Option B: SHOULD declare `__all__`; no AST check; existing
underscore convention continues.**

**Option C: Skip; trust the underscore convention.**

Recommendation: **A**.

---

## Proposal: L10-no-print-stdout-discipline

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness** (v011 reserves stdout for the structured-
findings contract and reserves stderr for structlog JSON, but no
mechanical check forbids `print()` / `sys.stdout.write` /
`sys.stderr.write` outside the narrow allowed surfaces).

### Summary

v011's structlog discipline says "stdout is reserved for the
structured-findings contract" and structlog handles all other
output. But an LLM can introduce a `print("debug:", x)` anywhere
and v011 has no AST check that catches it — only manual code
review.

### Motivation

The single most common LLM debugging artifact. Closes a real,
narrow bad-choice. Particularly important for
`bin/doctor_static.py` whose stdout is the JSON contract — a
stray `print("ok")` corrupts the wire format.

### Proposed Changes

**Option A (recommended): Add `check-no-print` AST check.**
Forbids `print()`, `sys.stdout.write()`, `sys.stderr.write()`
in `livespec/**` and `dev-tooling/**`. The single allowed
surface is `bin/_bootstrap.py`'s version-check `sys.stderr.write`
(per the v011 `_bootstrap.py` body). One narrow exception
recorded in the check's exemption list.

**Option B: ruff `T20` (flake8-print) selection — built-in
ruff rule for the same purpose.** Lighter than a custom AST
check; covers `print()` and `pprint()`.

**Option C: No rule; rely on code review.**

Recommendation: **B** — `T20` is one rule-code addition in the
ruff selection list (a candidate for L3 even).

---

## Proposal: L11-forbidden-imports-list

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness** (v011 has no rule banning specific stdlib
modules whose use would represent a clear regression in security
or determinism).

### Summary

A handful of stdlib modules have no business appearing in
livespec given its threat model + determinism requirements:

- `pickle` / `marshal` / `shelve` — arbitrary code execution on
  load; livespec has no need for them (JSON / JSONC covers all
  serialization).
- `eval` / `exec` / `__import__` — dynamic code execution;
  v005+ "static enumeration over dynamic discovery" memory
  forbids this style.
- `subprocess.Popen(shell=True)` / `os.system` — shell
  injection surface; livespec uses `subprocess.run` with list
  args only.

Ruff's `S` (flake8-bandit) category covers most of this
already; explicit listing in the style doc + `TID`'s
`banned-module-level-imports` configuration makes the boundary
explicit.

### Motivation

LLM bad-choice: reaching for `pickle` to "cache results" or
`eval` to "make this dynamic." The threat-model boundary is
narrow; codify it.

### Proposed Changes

**Option A (recommended): Enable ruff `S` category +
`TID.banned-module-level-imports` configuration for the
specific list above.**

**Option B: AST check `check-forbidden-imports` with the same
list.**

**Option C: Document as prose; rely on review.**

Recommendation: **A** — `S` is the ruff bandit category and
covers the security-relevant subset. Bundling with L3.

---

## Proposal: L12-property-based-testing-for-pure-modules

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md
- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**incompleteness** (v011 mandates 100% line+branch coverage and
example-based pytest tests, but does not require property-based
testing for pure Result-returning modules — the modules where
PBT delivers the most value).

### Summary

`livespec/parse/` and `livespec/validate/` are pure, Result-
returning, input-shape-rich modules. They are textbook PBT
targets: many input shapes, well-defined invariants (parse-then-
serialize round-trip; validate-then-construct dataclass round-
trip). LLM-written tests for these modules typically miss the
edge cases PBT finds reliably.

The mainstream Python PBT library is `hypothesis`
(HypothesisWorks/hypothesis, MPL-2.0); its companion
`hypothesis-jsonschema` (MIT) auto-generates strategies from JSON
Schema definitions — a perfect fit for v011's schema-driven
validators.

Both libraries are pure-Python and meet v011's vendoring
discipline (pure Python; permissive license; actively
maintained; small surface). Hypothesis is BSD-2 / MPL-2.0 —
verify license compatibility with v011's vendored-lib policy
(currently MIT / BSD / Apache-2.0); MPL-2.0 may need explicit
discussion.

### Motivation

The single highest-leverage testing addition for LLM-authored
pure code. Catches what unit tests miss by definition. Recent
research (arxiv 2510.09907, "Agentic Property-Based Testing")
documents that LLM-generated PBT finds bugs in 56% of analyzed
Python modules.

### Proposed Changes

**Option A (recommended): Vendor `hypothesis` +
`hypothesis-jsonschema`; mandate `@given(...)` usage in every
`tests/livespec/parse/test_*.py` and `tests/livespec/validate/
test_*.py`.**

Add to the style doc §"Testing" + new entry to PROPOSAL.md
§"Vendored third-party libraries":

> Property-based testing via `hypothesis`
> (HypothesisWorks/hypothesis) is mandatory for tests of modules
> in `livespec/parse/` and `livespec/validate/`. Each test
> module under `tests/livespec/parse/` and
> `tests/livespec/validate/` MUST declare at least one
> `@given(...)`-decorated test function. Enforced by AST check
> `check-pbt-coverage-pure-modules`.
>
> For schema-driven validators, `hypothesis-jsonschema` provides
> auto-generated strategies from the schema's `$id`-keyed JSON
> Schema definition; tests SHOULD use this instead of hand-
> authoring `@composite` strategies.

**Option B: Vendor `hypothesis` + `hypothesis-jsonschema`;
SHOULD use; no AST check.**

**Option C: Track as deferred-items entry; defer vendoring +
discipline decision to a later pass.**

Recommendation: **A** is the strongest; **C** is the
"minimize new dependencies" path (per the v009/v010 vendoring-
discipline memory). User-choice question; license verification
is a hard gate.

---

## Proposal: L13-mutation-testing-non-blocking-gate

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness** (v011's coverage-100% rule confirms every
line + branch is executed by tests, but does not confirm the
tests would actually fail if the code were broken — the
canonical "shallow tests" failure mode of LLM-generated code).

### Summary

Mutation testing systematically modifies the code (changes `+`
to `-`, removes a `not`, swaps `<` for `<=`) and runs the test
suite against each mutant. A "killed mutant" is one the tests
catch; a "surviving mutant" is one the tests don't catch — i.e.,
a place where the tests pass even when the code is wrong.

100% line+branch coverage with 0% mutation kill rate is a real
and common failure mode. LLM-authored tests fall into it
routinely.

Python tools: `mutmut` (boxed/mutmut, MIT) and `cosmic-ray`
(sixty-north/cosmic-ray, MIT). Both are mature.

### Motivation

The single best safety net against shallow LLM-authored tests.
Mutation testing is slow (full mutation runs take hours), so it
should be a non-blocking gate (run periodically or release-
gated), not per-commit.

### Proposed Changes

**Option A (recommended): Vendor `mutmut`; add
`just check-mutation` as a non-blocking gate; threshold ≥ 80%
mutation kill rate on `livespec/parse/` and
`livespec/validate/`.**

Add to the style doc §"Testing" + canonical `just` target list:

> `just check-mutation` runs `mutmut` against
> `livespec/parse/` and `livespec/validate/` (the pure modules
> where mutation testing is most informative). Threshold:
> ≥ 80% mutation kill rate. Run on a release-gate schedule
> (CI release branch only; not per-commit).

**Option B: Add as a `just` target but no enforced threshold;
diagnostic only.**

**Option C: Track as deferred-items; defer adoption.**

Recommendation: **B** — value-additive without making CI slow.
Threshold can be added once the pure modules exist and have a
real mutation surface.

---

## Proposal: L14-basedpyright-evaluation

### Target specification files

- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**ambiguity** (v011 mandates pyright but does not consider
`basedpyright` as a drop-in replacement; basedpyright bundles
~30 strict-plus diagnostics that L1 + L2 above re-derive
manually).

### Summary

`basedpyright` (DetachHead/basedpyright) is a community fork of
pyright that adds ~30 stricter diagnostics by default,
including most of L1 + L2's recommended additions
(`reportUnusedCallResult`, `reportImplicitOverride`,
`reportUninitializedInstanceVariable`,
`reportUnnecessaryTypeIgnoreComment`, etc.) plus its own
`baselining` system for incremental adoption.

Tradeoffs:

- **+** Drop-in replacement for pyright; same CLI; same config;
  same engine.
- **+** Many of L1's + L2's manual flag selections become
  defaults.
- **+** Has a "baselining" system that accepts current
  diagnostics as a baseline and only fails on regressions —
  helpful for migration.
- **−** Smaller maintainer pool than pyright (a community fork).
- **−** Diagnostic semantics drift from upstream over time.
- **−** mise pinning works but the version recipe needs updating.

### Motivation

If basedpyright is acceptable, L1 + L2 collapse into "switch
type checker; remove manual flag selection." That's a smaller,
simpler config change than the per-flag selection in L1 + L2.

### Proposed Changes

**Option A: Switch from pyright to basedpyright.** L1 + L2
become "use basedpyright defaults; document expected diagnostics
list."

**Option B: Stay on pyright; track basedpyright as deferred-
items entry for re-evaluation.**

**Option C (recommended): Track as deferred-items entry; resolve
together with L1 / L2 / `returns-pyright-plugin-disposition`
(the existing v007 deferred entry).**

Recommendation: **C** — basedpyright is a candidate but a tool-
selection change deserves its own evaluation pass. Bundling into
the existing pyright-plugin disposition entry is the lowest-cost
path.

---

## Proposal: L15-import-linter-consolidation

### Target specification files

- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**ambiguity** (v011 hand-rolls multiple AST checks
(`check-purity`, `check-import-graph`, parts of
`check-no-raise-outside-io`) that `import-linter`
(seddonym/import-linter, BSD-2) declaratively expresses; it is
unclear whether v011 prefers hand-written AST checks over a
mature library at this volume).

### Summary

`import-linter` is a mature Python tool that declaratively
expresses architecture rules:

- `forbidden` contracts: package A may not import from package
  B (replaces `check-purity`'s `parse/` + `validate/` import
  bans).
- `layers` contracts: ordered packages where higher layers may
  import lower but not vice-versa (replaces
  `check-import-graph`).
- `independence` contracts: a set of packages may not import
  from each other (useful for command-module isolation).

Configuration lives in `pyproject.toml` (same place as ruff +
pyright); enforcement is `lint-imports`.

Tradeoffs:

- **+** ~3 hand-written AST checks collapse into one
  declarative configuration.
- **+** Mature library; well-maintained.
- **+** Easier to read + audit than custom AST walkers.
- **−** New vendored dependency (per v010's `minimize-new-
  dependencies` memory).
- **−** Replaces working hand-written code with library code
  that has its own version-pin maintenance burden.
- **−** Consolidation into one tool means losing fine-grained
  per-check exit codes.

### Motivation

The v005+ "prefer standardized libraries" memory leans toward
this; the v009/v010 "minimize new dependencies" memory leans
against. Genuinely a user-judgment call.

### Proposed Changes

**Option A: Adopt import-linter; collapse `check-purity`,
`check-import-graph`, parts of `check-no-raise-outside-io` into
declarative `pyproject.toml` contracts.**

**Option B: Stay on hand-written AST checks; document import-
linter as a future consolidation candidate in deferred-items.**

**Option C (recommended): Track as deferred-items entry;
re-evaluate after the hand-written checks have shipped and
their maintenance burden is observable.**

Recommendation: **C** — the hand-written checks aren't yet a
maintenance pain point because they don't yet exist. Adoption
decision deserves data.

---

## Summary table

| Item | Failure mode | Impact | Recommendation |
|---|---|---|---|
| L1 | incompleteness | major | A — enable `reportUnusedCallResult` |
| L2 | incompleteness | significant | A — enable strict-plus options |
| L3 | incompleteness | significant | A — expanded ruff rule selection |
| L4 | incompleteness | significant | A — `slots=True` on dataclasses |
| L5 | ambiguity | significant | A — `@final` + no inheritance |
| L6 | incompleteness | significant | A — Protocol over ABC |
| L7 | incompleteness | significant | A — assert_never exhaustiveness |
| L8 | ambiguity | significant | A — NewType domain primitives |
| L9 | incompleteness | smaller | A — `__all__` per module |
| L10 | incompleteness | smaller | B — ruff T20 (flake8-print) |
| L11 | incompleteness | smaller | A — ruff S + TID banned imports |
| L12 | incompleteness | smaller | A — Hypothesis PBT for pure modules |
| L13 | incompleteness | smaller | B — mutmut as diagnostic |
| L14 | ambiguity | smaller | C — defer to deferred-items |
| L15 | ambiguity | smaller | C — defer to deferred-items |

End of critique.
