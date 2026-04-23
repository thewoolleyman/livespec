---
proposal: proposal-critique-v11.md
decision: modify
revised_at: 2026-04-23T20:00:00Z
author_human: thewoolleyman
author_llm: Claude Opus 4.7 (1M context)
---

# Revision: proposal-critique-v11

## Provenance

- **Proposed change:** `proposal-critique-v11.md` (in this directory) —
  an agent-guardrail-focused critique surfacing 15 incompletenesses
  (L1–L15) left in v011 PROPOSAL.md,
  `python-skill-script-style-requirements.md`, and
  `deferred-items.md` after the K1–K11 landings. The critique was
  driven by the v005+ "strongest-possible guardrails for agent-
  authored Python" memory and informed by 2026 Python tooling
  research (pyright strict-plus options, ruff rule-set expansion,
  Hypothesis property-based testing, mutmut mutation testing,
  Import-Linter declarative architecture enforcement, basedpyright).
- **Revised by:** thewoolleyman (human) in dialogue with Claude Opus
  4.7 (1M context).
- **Revised at:** 2026-04-23 (UTC).
- **Scope:** v011 PROPOSAL.md + python style doc + `deferred-items.md`
  → v012 equivalents. `livespec-nlspec-spec.md` unchanged by this
  pass (its Architecture-Level Constraints + Error Handling
  Discipline sections continue to be normative authority for
  livespec's own implementation). Focus areas: closing the largest
  ROP-discipline hole (L1: silently-discarded `Result`/`IOResult`);
  expanding pyright's strict-plus diagnostic surface (L2);
  expanding ruff's rule-category selection (L3 + L10 + L11);
  completing the strict-dataclass triple with `slots=True` (L4);
  codifying the implicit "flat composition; no inheritance"
  direction via `check-no-inheritance` (L5); banning `abc.ABC` /
  `abc.ABCMeta` / `abc.abstractmethod` via the existing TID
  banned-imports infrastructure (L6); making `match`-statement
  exhaustiveness a type-check-time error via `assert_never` (L7);
  introducing `NewType` aliases for 8 domain primitives with
  AST enforcement at the dataclass-field layer (L8); mandating
  per-module `__all__` declarations (L9); banning `print` /
  `sys.stdout.write` / `sys.stderr.write` outside designated
  surfaces (L10); banning dangerous stdlib modules via ruff `S` +
  TID extensions (L11); mandating Hypothesis property-based
  testing for pure modules (L12); adding mutation testing as a
  release-gate (L13); deferring basedpyright + Import-Linter-
  bundle-vendoring decisions (L14, L15b); adopting Import-Linter
  at the dev-tooling layer to express purity / import-graph /
  raise-discipline contracts declaratively (L15a); and
  establishing a project-wide governing principle that user-
  provided extensions (custom doctor checks, custom templates)
  carry MINIMAL requirements — only the calling-API contract —
  with livespec imposing no library-usage, architecture, or
  pattern expectations beyond that.

## Pass framing

This pass was an **agent-guardrail-focused incompleteness
critique** producing 15 items (L1-L15). Each L item carried one of
four NLSpec failure modes (ambiguity / malformation /
incompleteness / incorrectness) and was grouped by impact: major
gap (L1, the largest single ROP hole), significant gaps (L2-L8,
each closing a wide LLM bad-choice space), smaller cleanup
(L9-L15, defense-in-depth + tool-selection deferrals).

Two items expanded mid-interview into broader principles:

- **L5** (`@final` mandate) was REVISED from the originally
  recommended "both `@final` + AST check" to user-chosen
  "AST check only." User asked whether `@final` was redundant
  with the AST check; honest analysis confirmed the AST check is
  strictly stronger as a single mechanism, and `@final` adds
  only documentation-by-decorator value.
- **L6** (Protocol over ABC) was REVISED from the originally
  recommended "dedicated `check-no-abc` AST check" to user-
  chosen "extend L3's TID banned-imports config with `abc.ABC` /
  `abc.ABCMeta` / `abc.abstractmethod`." The TID approach reuses
  L3's already-enabled rule infrastructure and is one config diff
  rather than a new check.

One item split into two during the interview:

- **L15** (Import-Linter consolidation) split into **L15a**
  (dev-tooling: should livespec's own architecture rules be
  enforced via Import-Linter declarative config or hand-written
  AST walkers?) and **L15b** (bundle: should Import-Linter be
  vendored in `_vendor/` for custom-template doctor checks
  targeting user Python code?). User flagged that the original
  L15 conflated two different concerns. **L15a** landed as
  "adopt Import-Linter at the dev-tooling layer now" (mise-
  pinned, NOT vendored in bundle, replaces the planned hand-
  written `check-purity` + `check-import-graph` + parts of
  `check-no-raise-outside-io`). **L15b** landed as "don't
  vendor; user-provided extensions get minimal requirements" —
  which generalized into a **new project-wide governing
  principle** (see "Governing principles" below).

One item received a packaging correction:

- **L12** (Hypothesis property-based testing) was accepted as
  "vendor + mandate + AST check" but during revision drafting
  was corrected to **"mise-pin (not vendor) + mandate + AST
  check."** Hypothesis is a TEST-only dependency and follows
  the v011 pattern for test deps (pytest, pytest-cov, pytest-
  icdiff are all mise-pinned, not vendored). The "vendor"
  packaging assumption was wrong; the correction sidesteps the
  MPL-2.0 license-policy expansion entirely (vendoring policy
  doesn't apply to mise-pinned dev-time deps). hypothesis-
  jsonschema (MIT) similarly mise-pinned. Same packaging
  correction applied to L13 (mutmut, MIT) and L15a (Import-
  Linter, BSD-2). This correction is recorded here rather than
  re-asked because the user's L12-A intent ("include Hypothesis;
  mandate PBT; AST check") is preserved unchanged; only the
  packaging mechanism (mise-pin vs. vendor) was wrong in the
  critique. If the user prefers vendoring after seeing this
  revision, the deferred entry tracking the choice can reopen.

No item reopened any v005-v011 decision about what livespec does.

## Summary of dispositions

| Item | Failure mode | Disposition |
|---|---|---|
| L1 | incompleteness | A — pyright `reportUnusedCallResult = "error"` |
| L2 | incompleteness | A — six pyright strict-plus diagnostics enabled (with `typing_extensions` follow-up for `@override`) |
| L3 | incompleteness | A — 14 ruff categories added (TRY FBT PIE SLF LOG G TID ERA ARG RSE PT FURB SLOT ISC) |
| L4 | incompleteness | A — `@dataclass(frozen=True, kw_only=True, slots=True)` triple mandated |
| L5 | ambiguity | (revised) B — `check-no-inheritance` AST check only; no `@final` mandate |
| L6 | incompleteness | (revised) A — `abc.ABC` / `abc.ABCMeta` / `abc.abstractmethod` added to TID banned-imports |
| L7 | incompleteness | A — `case _: assert_never(x)` mandated on every `match`; conservative AST check |
| L8 | ambiguity | A — 8 NewType aliases at `livespec/types.py`; AST check at dataclass-field layer |
| L9 | incompleteness | A — `__all__` mandated per module; AST check |
| L10 | incompleteness | A — ruff `T20` + custom `check-no-write-direct` (with three documented exemptions: `bin/_bootstrap.py` pre-import stderr; supervisor `main()` in `commands/**.py` for any documented stdout contract — HelpRequested per K7, resolve_template path per K2; `doctor/run_static.py::main()` findings JSON stdout) |
| L11 | incompleteness | A — ruff `S` enabled; TID banned-imports extended (`pickle`, `marshal`, `shelve`) |
| L12 | incompleteness | A (corrected) — Hypothesis + hypothesis-jsonschema mise-pinned (NOT vendored); `@given(...)` mandated in `tests/livespec/parse/**` and `tests/livespec/validate/**`; AST check |
| L13 | incompleteness | A — `mutmut` mise-pinned; `just check-mutation` release-gate; ≥80% kill threshold on `parse/` + `validate/` (threshold tunable on first real measurement) |
| L14 | ambiguity | B — stay on pyright; basedpyright tracked as standalone deferred-items entry |
| L15a | ambiguity | A — Import-Linter mise-pinned at dev-tooling layer; replaces planned `check-purity` + `check-import-graph` + parts of `check-no-raise-outside-io` |
| L15b | ambiguity | B (by principle) — don't vendor Import-Linter in bundle; user-provided extensions get minimal requirements |

## Governing principles established or reinforced

- **NEW: User-provided extensions get minimal requirements.**
  Established at L15b. For livespec extension points (custom
  doctor checks loaded via K5's `doctor_static_check_modules`,
  custom templates, future hooks), livespec imposes ZERO
  requirements beyond the calling-API contract (the data
  structures and type-safe contracts that flow ACROSS the
  extension boundary). livespec is NOT responsible for linting,
  vendoring for, or prescribing architecture / library usage /
  patterns to extension authors. This principle resolved L15b
  directly (no Import-Linter vendoring "in case extension
  authors want it") and reshapes the scope statement for every
  v012-accepted constraint (L1-L13 apply to livespec-authored
  code only: `livespec/**`, `bin/**`, `dev-tooling/**`).
  Recorded as a feedback memory at
  `feedback_user_extensions_minimal_requirements.md`.
- **Strongest-possible guardrails for livespec-authored
  Python.** Reinforced by L1 (closing the discarded-`Result`
  hole), L2 (six pyright strict-plus diagnostics), L3 (14
  additional ruff categories), L4 (`slots=True` completing the
  strict-dataclass triple), L5 (`check-no-inheritance` AST
  check), L7 (`assert_never` exhaustiveness), L8 (`NewType`
  domain primitives), L9 (`__all__` per module), L10
  (`check-no-write-direct`), L11 (ruff `S` + banned-imports
  expansion). Net effect: ~15 additional mechanical guardrails
  layered on top of v011's existing enforcement suite.
- **Architecture-vs-mechanism** (v009 I0). Reconfirmed
  throughout: each L item names a property code MUST have or
  MUST NOT have, not how to write internal mechanism. The new
  enforcement checks are the discipline; the style doc does
  not illustrate "correct" code shape beyond one-line
  decorator/import examples.
- **Domain-vs-bugs** (v009 I10). Reinforced indirectly by L3's
  `TRY` category (tryceratops exception-handling discipline)
  and L7's `assert_never` (exhaustiveness over LivespecError
  subclass dispatch).
- **Static enumeration over dynamic discovery** (v005+).
  Reinforced by L11's ban on `eval` / `exec` / `__import__`.
- **Minimize new dependencies; reuse existing infrastructure**
  (v009/v010). Honored throughout: L3, L6, L10, L11 reuse the
  ruff rule-selection + TID-banned-imports infrastructure
  already enabled. L12+L13+L15a add mise-pinned dev-time deps
  rather than bundle vendoring. L15b explicitly rejects
  bundle vendoring on principle grounds.
- **Test-dep packaging convention.** L12 + L13 corrections
  reaffirm: test-only and dev-tool-only deps are mise-pinned,
  not vendored. Bundle vendoring is reserved for libs imported
  by `livespec/**` at runtime in user environments.

## Disposition by item

### L1. Pyright `reportUnusedCallResult` (incompleteness → accepted, option A)

The largest single hole in v011's ROP discipline: `pyright`
strict mode does not flag a discarded `Result` / `IOResult`
return value. An LLM can write `do_something(ctx)` instead of
`result = do_something(ctx)`, silently dropping the failure
track. The ENTIRE error-handling contract rests on Result
composition; one config-line fix.

Resolution:

- python style doc §"Type safety" — add:

> The `[tool.pyright]` configuration MUST set
> `reportUnusedCallResult = "error"` so that any discarded
> `Result` / `IOResult` (or other non-`None`-returning call
> result) is a type error. The rule has no exceptions in
> `livespec/**`. Supervisor side-effect calls (e.g.,
> `log.info(...)` returning `None`) are unaffected because
> `None` returns are not flagged. The rare legitimate fire-
> and-forget pattern uses explicit-discard binding:
> `_ = do_something(ctx)`.

`task-runner-and-ci-config` deferred-items entry scope-widened
to record the new pyright option in `pyproject.toml`.

### L2. Pyright strict-plus diagnostics (incompleteness → accepted, option A)

Six pyright diagnostics above the strict baseline, each closing
a documented LLM-authored-code failure pattern with a one-line
config addition.

Resolution:

- python style doc §"Type safety" — add:

> The `[tool.pyright]` configuration MUST also enable the
> following strict-plus diagnostics:
>
> - `reportImplicitOverride = "error"` — every method override
>   MUST carry `@override` (from `typing` 3.11+ or
>   `typing_extensions` 3.10).
> - `reportUninitializedInstanceVariable = "error"` — every
>   instance attribute MUST be initialized in `__init__` or
>   have a class-level default.
> - `reportUnnecessaryTypeIgnoreComment = "error"` — flags
>   `# type: ignore` comments that no longer suppress any
>   diagnostic.
> - `reportUnnecessaryCast = "error"` — flags `cast(X, value)`
>   where `value` is already typed `X`.
> - `reportUnnecessaryIsInstance = "error"` — flags
>   `isinstance(x, T)` when the type checker already knows
>   `x: T`.
> - `reportImplicitStringConcatenation = "error"` — catches
>   `["foo" "bar"]` (missing comma) bugs in lists / sets /
>   tuples.

**Open dependency follow-up:** `@override` requires
`typing_extensions` on Python 3.10. Verify whether
`typing_extensions` is transitively vendored via dry-python/
returns or whether it must be vendored explicitly.
`task-runner-and-ci-config` deferred-items entry tracks this.

### L3. Ruff rule selection expansion (incompleteness → accepted, option A)

Fourteen additional ruff rule categories cover known LLM bad-
choice patterns and reinforce v011's existing discipline
directions (K10 domain-vs-bugs, structlog logging style,
keyword-only construction).

Resolution:

- python style doc §"Linter and formatter" — extend rule
  selection from `E F I B UP SIM C90 N RUF PL PTH` to:
  `E F I B UP SIM C90 N RUF PL PTH TRY FBT PIE SLF LOG G TID ERA ARG RSE PT FURB SLOT ISC`.
- The `T20` (flake8-print) and `S` (flake8-bandit) categories
  are added separately in L10 and L11 respectively; together
  the v012 selection is 16 categories above v011's 11
  (27 total).
- TID configuration: add `[tool.ruff.lint.flake8-tidy-imports]`
  with `ban-relative-imports = "all"` and a banned-imports
  list (extended in L6 and L11).
- Per-category configuration tuning is left to the
  implementer; the rule selection itself is the load-bearing
  decision.

`task-runner-and-ci-config` deferred-items entry scope-widened
to record the rule-selection expansion in `pyproject.toml`.

### L4. `slots=True` completes the strict-dataclass triple (incompleteness → accepted, option A)

K4 mandated `frozen=True, kw_only=True`. Adding `slots=True`
catches attribute-name typos at access time and reduces
per-instance memory footprint. No livespec design relies on
`__weakref__` or multiple inheritance, so the standard
`slots=True` tradeoffs don't bite.

Resolution:

- python style doc §"Keyword-only arguments" — extend the K4
  rule wording:

> Every `@dataclass` decorator MUST include the full triple
> `frozen=True, kw_only=True, slots=True` (Python 3.10+).
> The generated `__init__` is keyword-only; the instance is
> immutable; attribute-name typos at access time raise
> `AttributeError` rather than silently creating new
> attributes.

- The existing `check-keyword-only-args` AST walker (added in
  K4 to verify `kw_only=True`) extends to also verify
  `frozen=True` and `slots=True` on the same `@dataclass`
  decorator. No new check needed.

`static-check-semantics` deferred-items entry scope-widened to
record the extended walker semantics.

### L5. `check-no-inheritance` AST check (ambiguity → accepted, revised option B)

REVISED from the originally recommended "both `@final` +
AST check" to user-chosen "AST check only" after the user
asked whether `@final` was redundant. Honest analysis:

- The AST check inspects every `class X(Y):` and rejects unless
  `Y` is in an immediate-parent allowlist. Catches subclass
  attempts whether or not the parent is `@final`-decorated.
- `@final` only catches subclass attempts on classes the author
  remembered to decorate. Strictly weaker as a single mechanism.
- `@final` adds: documentation-at-source value, pyright type-
  narrowing benefits. None of these change catching power.

Resolution:

- python style doc §"Type safety" (or new subsection) — add:

> Class inheritance in `livespec/**`, `bin/**`, and
> `dev-tooling/**` is RESTRICTED. The AST check
> `check-no-inheritance` rejects any `class X(Y):` definition
> where `Y` is not in the allowlist
> `{Exception, BaseException, LivespecError, Protocol,
> NamedTuple, TypedDict}` or a `LivespecError` subclass.
> This codifies the documented design direction (flat
> composition over inheritance; structural typing via
> `typing.Protocol`; sum-type dispatch via tagged dataclasses
> + structural pattern matching). The `LivespecError`
> hierarchy itself remains an open extension point — adding
> a new domain-error subclass (e.g., a future
> `RateLimitError(LivespecError)`) is permitted by the rule.

- Concrete effect on the LivespecError hierarchy: NO change in
  declared shape. `LivespecError` is the open base; each
  subclass (`UsageError`, `ValidationError`, etc.) remains a
  concrete leaf. Multi-level subclassing of any leaf domain
  error is forbidden by the rule (the leaf is not in the
  allowlist).
- `@final` decorator usage is OPTIONAL throughout livespec; the
  AST check is the source of truth. Authors may use `@final`
  as documentation-by-decorator for clarity but it is not
  required.

`enforcement-check-scripts` and `static-check-semantics`
deferred-items entries scope-widened to add the new check +
its semantics (AST scope; allowlist; `LivespecError`-subclass
discrimination).

### L6. ABC ban via TID banned-imports (incompleteness → accepted, revised option A)

REVISED from the originally proposed dedicated `check-no-abc`
AST check to user-chosen "extend L3's TID banned-imports config
with `abc.*` entries." TID is one config-file diff; reuses L3's
infrastructure. L5's `check-no-inheritance` already catches the
inheritance-form (`class X(ABC):`); L6 catches the import
itself, which is one signal earlier and also covers stray
`@abstractmethod` decorations.

Resolution:

- python style doc §"Linter and formatter" — extend the TID
  banned-imports list to include `abc.ABC`, `abc.ABCMeta`,
  `abc.abstractmethod`. (L11 extends the same list with
  security-relevant entries.)
- python style doc §"Type safety" — add a one-sentence note:

> Structural interfaces in `livespec/**` MUST be declared via
> `typing.Protocol`. `abc.ABC`, `abc.ABCMeta`, and
> `abc.abstractmethod` imports are banned via the TID rule
> configuration; see §"Linter and formatter."

`task-runner-and-ci-config` deferred-items entry scope-widened
to record the TID banned-imports list contents.

### L7. `assert_never` exhaustiveness (incompleteness → accepted, option A)

v011 uses structural pattern matching for supervisor exit-code
derivation, doctor `Finding.status` dispatch, sub-command
routing — each is a documented extension point where new
variants can be added later. Without `assert_never`, each
variant addition is a silent-runtime-bug risk; with it, the
type checker enumerates every dispatch site that needs
updating.

Resolution:

- python style doc §"Type safety" (new subsection
  "Exhaustiveness") — add:

> Every `match` statement in `livespec/**`, `bin/**`, and
> `dev-tooling/**` MUST terminate with
> `case _: assert_never(<subject>)` regardless of subject
> type. `assert_never` is from `typing` (3.11+) or
> `typing_extensions` (3.10).
>
> Rationale: `assert_never(x)` requires `x` to have type
> `Never`. When all variants of a closed-union subject are
> handled by preceding `case` arms, the residual type at
> the default arm is `Never` and pyright accepts the call.
> When a new variant is added without updating the dispatch
> site, the residual type narrows to the unhandled variant
> and `assert_never(x)` becomes a type error at the
> unhandled dispatch site.
>
> The conservative scope (every `match`, regardless of
> subject type) is preferred over a precise scope (only
> closed-union subjects) because false positives are cheap
> (just add the line) and the simpler check is more
> maintainable.

- New AST check `check-assert-never-exhaustiveness`: walks
  every `ast.Match` node in scope; verifies the final case
  arm is `case _:` and its body is exactly
  `assert_never(<subject-name>)`.

`enforcement-check-scripts` and `static-check-semantics`
deferred-items entries scope-widened.

**Open dependency follow-up (shared with L2):**
`assert_never` requires `typing_extensions` on Python 3.10.
Same verification as L2.

### L8. NewType domain primitives (ambiguity → accepted, option A)

v011 dataclass fields use raw `str`/`int`/`Path` for fields
with strong domain meaning. Cross-wiring (e.g., passing a
`run_id` where a `check_id` is expected, or `template_root`
where `spec_root` is expected) is silently accepted by the
type checker because both are the same primitive at the type
layer.

Resolution:

- New module `livespec/types.py` — exports the canonical
  NewType aliases:

```python
from pathlib import Path
from typing import NewType

CheckId = NewType("CheckId", str)
RunId = NewType("RunId", str)
TopicSlug = NewType("TopicSlug", str)
SpecRoot = NewType("SpecRoot", Path)
SchemaId = NewType("SchemaId", str)
TemplateName = NewType("TemplateName", str)
Author = NewType("Author", str)
VersionTag = NewType("VersionTag", str)
```

- python style doc §"Type safety" — add:

> Domain identifiers in `livespec/**` MUST use a `typing.NewType`
> alias from `livespec/types.py`. Dataclass fields and function
> signatures handling these concepts MUST use the NewType, not
> the underlying primitive. The canonical roles → NewType
> mapping:
>
> | Field role | NewType | Underlying |
> |---|---|---|
> | doctor-static check slug | `CheckId` | `str` |
> | per-invocation UUID | `RunId` | `str` |
> | proposed-change topic | `TopicSlug` | `str` |
> | resolved spec-root path | `SpecRoot` | `Path` |
> | JSON Schema `$id` | `SchemaId` | `str` |
> | `.livespec.jsonc` template field | `TemplateName` | `str` |
> | author identifier (per K7 rename) | `Author` | `str` |
> | `vNNN` version identifier | `VersionTag` | `str` |
>
> Additions to the canonical list are first-class deferred-items
> work (one-line update to `livespec/types.py` plus migrations).

- New AST check `check-newtype-domain-primitives`: walks
  `livespec/schemas/dataclasses/*.py` and `livespec/**.py`
  function signatures; verifies field annotations matching the
  listed roles use the corresponding NewType. The role-to-
  field-name mapping is enumerated explicitly in the check
  source; partial mismatches (right NewType, wrong field name;
  or right field name, wrong NewType) are both fail.

`enforcement-check-scripts` and `static-check-semantics`
deferred-items entries scope-widened. PROPOSAL.md does NOT
need to enumerate the NewTypes in its dataclass-field
descriptions (the style doc owns the rule; the dataclasses are
the implementation).

### L9. Per-module `__all__` declaration (incompleteness → accepted, option A)

Today `check-public-api-result-typed` infers public-vs-private
from the leading-underscore convention; `__all__` flips the
discipline so nothing is public unless explicitly listed.

Resolution:

- python style doc §"Type safety" (or new subsection
  "Module API surface") — add:

> Every module in `livespec/**` MUST declare a module-top
> `__all__: list[str]` listing the public API names. Public
> functions, public classes, and public NewType aliases
> belong in `__all__`; private helpers (single-leading-
> underscore prefix) MUST NOT appear in `__all__`. The
> `check-public-api-result-typed` check is REWORDED to
> scope its enforcement to names listed in `__all__`
> rather than to non-`_`-prefixed names.

- New AST check `check-all-declared`: walks every
  module under `livespec/**`; verifies a module-level
  `__all__: list[str]` assignment exists; verifies every
  name in `__all__` is actually defined in the module
  (catches stale entries after a rename).
- `__init__.py` files MAY declare `__all__` for re-export
  composition; the same rule applies (every name listed
  must resolve in the module's namespace, including
  imported names).

`enforcement-check-scripts` and `static-check-semantics`
deferred-items entries scope-widened (including the
`check-public-api-result-typed` scope adjustment to
`__all__`-based public-API detection).

### L10. `check-no-write-direct` + ruff `T20` (incompleteness → accepted, option A)

v011 reserves stdout for the structured-findings JSON contract
and stderr for structlog JSON, but no mechanical check forbids
`print(...)` or direct `sys.stdout.write` / `sys.stderr.write`
calls. A stray `print` corrupts the JSON wire format.

Resolution:

- python style doc §"Linter and formatter" — add `T20`
  (flake8-print) to the rule selection (combined with L3 +
  L11 → 17 added categories total above v011's 11).
- New AST check `check-no-write-direct`: walks every
  `ast.Call` in `livespec/**`, `bin/**`, `dev-tooling/**`;
  rejects calls of the form `sys.stdout.write(...)`,
  `sys.stderr.write(...)`. **Three documented exemptions**
  (caught during the v012 careful-review pass — the original
  L10 critique listed only `bin/_bootstrap.py`, but the v011
  K7 / J7 + K2 supervisor contracts require writing to
  stdout, and the doctor static-phase contract requires
  writing the findings JSON to stdout):
  - `bin/_bootstrap.py` — pre-livespec-import version-check
    stderr (structlog not yet configured).
  - Supervisor `main()` functions in `livespec/commands/**.py`
    — `sys.stdout.write` permitted for any documented stdout
    contract owned by the supervisor: `HelpRequested.text`
    per K7 / J7; `bin/resolve_template.py`'s single-line
    resolved-path output per K2; any future supervisor-owned
    stdout contract. Function-scoped (only `main`, not
    module-scoped helpers).
  - `livespec/doctor/run_static.py::main()` —
    `sys.stdout.write({"findings": [...]})` per the doctor
    static-phase output contract.
- python style doc §"Structured logging" — add a one-sentence
  note pointing at the new check.

`enforcement-check-scripts` and `static-check-semantics`
deferred-items entries scope-widened.

### L11. Forbidden imports via ruff `S` + TID extension (incompleteness → accepted, option A)

A handful of stdlib modules have no business in livespec
(`pickle`, `marshal`, `shelve`, `eval`, `exec`, `__import__`,
`subprocess.Popen(shell=True)`, `os.system`). Two-layer
coverage:

Resolution:

- python style doc §"Linter and formatter" — add `S`
  (flake8-bandit) to the rule selection. Catches `pickle.loads`,
  `subprocess` with `shell=True`, `eval`, `exec`, etc.
- python style doc §"Linter and formatter" — extend the TID
  banned-imports list (already started in L6 with `abc.*`)
  to include: `pickle`, `marshal`, `shelve`. These three are
  banned at the import line; bandit's `S` catches the
  function-call sites of the others.

`task-runner-and-ci-config` deferred-items entry scope-widened
to record the TID banned-imports list final contents (L6's
ABC entries + L11's stdlib entries).

### L12. Hypothesis property-based testing for pure modules (incompleteness → accepted, corrected option A)

Pure Result-returning modules (`livespec/parse/`,
`livespec/validate/`) are textbook PBT targets. v011 mandates
100% line+branch coverage with example-based pytest tests, but
coverage just verifies execution, not failure-on-broken-code.

Resolution (with packaging correction):

- `pyproject.toml` developer-time deps + `.mise.toml` —
  mise-pin `hypothesis` (HypothesisWorks/hypothesis,
  MPL-2.0) and `hypothesis-jsonschema` (MIT). NOT vendored
  in the bundle: both are test-only deps and follow the
  v011 test-dep packaging convention (pytest, pytest-cov,
  pytest-icdiff are all mise-pinned, not vendored). The
  MPL-2.0 license-policy expansion the L12 critique
  contemplated is NOT needed under this packaging — the
  vendored-libs license policy applies only to bundle-
  vendored libs.
- python style doc §"Testing" — add:

> Property-based testing via `hypothesis` (mise-pinned) is
> mandatory for tests of modules in `livespec/parse/` and
> `livespec/validate/`. Each test module under
> `tests/livespec/parse/` and `tests/livespec/validate/`
> MUST declare at least one `@given(...)`-decorated test
> function. For schema-driven validators,
> `hypothesis-jsonschema` provides auto-generated strategies
> from the schema's JSON Schema definition; tests SHOULD use
> this rather than hand-authoring `@composite` strategies.
> Enforced by AST check `check-pbt-coverage-pure-modules`.

- New AST check `check-pbt-coverage-pure-modules`: walks
  every test module under `tests/livespec/parse/` and
  `tests/livespec/validate/`; verifies at least one
  function in the module is decorated with `@given(...)`
  (from `hypothesis`).

`enforcement-check-scripts`, `static-check-semantics`, and
`task-runner-and-ci-config` deferred-items entries scope-
widened.

### L13. Mutation testing as release-gate (incompleteness → accepted, option A)

100% coverage with 0% mutation kill rate is a real and common
LLM-test failure mode (test asserts function was *called* but
not that the *result* is correct). Mutation testing is the
direct safety net.

Resolution (with packaging correction):

- `.mise.toml` — mise-pin `mutmut` (MIT). NOT vendored in
  the bundle: dev-tool only.
- python style doc §"Testing" — add:

> Mutation testing via `mutmut` (mise-pinned) runs on a
> release-gate schedule (CI release branch only; not per-
> commit). Threshold: ≥80% mutation kill rate on
> `livespec/parse/` and `livespec/validate/` (the pure
> modules where mutation testing is most informative).
> The 80% threshold is initial guidance; first real
> measurement may surface a different appropriate value.
>
> The release-gate scheduling is handled by a dedicated
> CI workflow that runs `just check-mutation` on
> release-tagged commits; per-commit CI does NOT invoke
> the target.

- New `just check-mutation` target. Added to the canonical
  target list under "release-gate" (or a similar)
  subsection — distinct from the always-on `just check`
  aggregator which continues to NOT run mutation testing.

`task-runner-and-ci-config` deferred-items entry scope-widened.

### L14. basedpyright deferred (ambiguity → accepted, option B)

basedpyright (DetachHead/basedpyright) bundles ~30 stricter
diagnostics by default, including most of L1+L2. With L1+L2
now manually enabled, the marginal value of switching tools is
reduced. User chose to stay on pyright and track basedpyright
separately.

Resolution:

- New deferred-items entry `basedpyright-vs-pyright`: when to
  re-evaluate switching from `pyright` to `basedpyright`,
  what diagnostics would collapse from manual enable to
  default, baselining-system migration cost.
- This is a STANDALONE deferred entry (NOT bundled with
  `returns-pyright-plugin-disposition`, the existing v007
  entry — different concerns).

### L15a. Import-Linter at dev-tooling layer (ambiguity → accepted, option A)

Import-Linter (seddonym/import-linter, BSD-2) declaratively
expresses architecture rules in `pyproject.toml`. Adopted at
the dev-tooling layer to express livespec's own architecture
rules (`check-purity`, `check-import-graph`, parts of
`check-no-raise-outside-io`).

Resolution:

- `.mise.toml` — mise-pin `import-linter`. NOT vendored in
  the bundle (per L15b).
- `pyproject.toml` — add `[tool.importlinter]` section with
  contracts replacing the planned hand-written checks:
  - **`forbidden` contract** for `parse/` + `validate/`:
    these packages MUST NOT import from `io/` or any
    effectful API module. Replaces planned `check-purity`.
  - **`layers` contract**: ordered package layers; higher
    layers may import lower but not vice-versa. Replaces
    planned `check-import-graph` (no circular imports
    follows from layered architecture).
  - **`forbidden` contract** for raising `LivespecError`
    subclasses outside `io/**` and `errors.py`. Replaces
    PARTS of planned `check-no-raise-outside-io` (the import-
    surface portion). The AST-level discipline of "raising
    bug-class exceptions permitted anywhere" remains in a
    smaller hand-written check OR in pyright's
    diagnostic infrastructure — implementer choice.
- python style doc §"Enforcement suite" — replace
  `check-purity` and `check-import-graph` rows in the
  canonical target list with `check-imports-architecture`
  (a single target invoking `lint-imports`). Update the
  `check-no-raise-outside-io` row's purpose description to
  note the import-surface portion is delegated to
  `check-imports-architecture`.

`enforcement-check-scripts` deferred-items entry scope-widened
to record the Import-Linter adoption (the planned hand-written
checks now collapse into one declarative configuration).

### L15b. No bundle vendoring of Import-Linter (ambiguity → accepted, option B by principle)

Vendoring a Python architecture-checking library "in case
custom templates want it" would set a precedent of vendoring
libraries livespec OFFERS to extension authors rather than
libraries livespec NEEDS. This conflicts with the new
governing principle (see "Governing principles" above): user-
provided extensions get minimal requirements; livespec is not
responsible for what they import.

Resolution:

- Import-Linter is NOT added to `_vendor/`.
- PROPOSAL.md §"Vendored third-party libraries" — no change
  to the vendored bundle (returns, fastjsonschema, structlog,
  jsoncomment).
- PROPOSAL.md §K5 doctor-extensibility section (or §"Custom
  templates are in v1 scope" or wherever the K5 hook is
  documented) — add an explicit user-provided-extensions
  scope clarification:

> User-provided extensions loaded via `template.json`'s
> `doctor_static_check_modules` (and any future extension
> hook) carry MINIMAL requirements: only the calling-API
> contract (the `TEMPLATE_CHECKS` export shape, `CheckRunFn`
> signature, `Finding` payload shape). livespec imposes no
> library-usage, architecture, or pattern expectations on
> extension code beyond that contract. Extension authors
> bring their own dependency-resolution mechanism; livespec
> does NOT vendor third-party libraries on extension
> authors' behalf, and livespec's enforcement suite does
> NOT lint or evaluate extension-loaded code.

- python style doc §"Scope" — extend the existing scope
  paragraph to make the boundary explicit:

> The rules in this document apply to livespec-AUTHORED
> Python code under `.claude-plugin/scripts/livespec/**`,
> `.claude-plugin/scripts/bin/**`, and
> `<repo-root>/dev-tooling/**`. They do NOT apply to:
>
> - `.claude-plugin/scripts/_vendor/**` — vendored third-party
>   libraries (already documented as exempt).
> - User-provided Python modules loaded via custom-template
>   extension hooks (e.g., `doctor_static_check_modules`).
>   Extension code is the extension author's responsibility;
>   livespec's enforcement suite does NOT scope to it.

## Deferred-items inventory (carried forward + scope-widened + new)

Per the deferred-items discipline, every carried-forward item
is enumerated below. Additions, scope-widenings, and renames
are flagged.

**Carried forward unchanged from v011:**

- `template-prompt-authoring` (v001).
- `python-style-doc-into-constraints` (v005).
- `companion-docs-mapping` (v001).
- `returns-pyright-plugin-disposition` (v007).
- `user-hosted-custom-templates` (v010 J3).
- `skill-md-prose-authoring` (v008 H4; widened every pass
  since). No L-item changes its scope.

**Scope-widened in v012:**

- `enforcement-check-scripts` (v005). v012 additions:
  - L5: `check-no-inheritance` AST check.
  - L7: `check-assert-never-exhaustiveness` AST check.
  - L8: `check-newtype-domain-primitives` AST check.
  - L9: `check-all-declared` AST check.
  - L10: `check-no-write-direct` AST check.
  - L12: `check-pbt-coverage-pure-modules` AST check.
  - L15a: Import-Linter ADOPTION at dev-tooling layer
    REPLACES planned `check-purity` + `check-import-graph` +
    parts of `check-no-raise-outside-io`. New
    `check-imports-architecture` target invoking
    `lint-imports` against `[tool.importlinter]` config.
- `static-check-semantics` (v007; widened every pass since).
  v012 additions:
  - L4: extended `check-keyword-only-args` walker semantics
    (now also verifies `frozen=True` and `slots=True` on
    `@dataclass` decorators).
  - L5: `check-no-inheritance` semantics (immediate-parent
    allowlist; LivespecError-subclass handling).
  - L7: `check-assert-never-exhaustiveness` semantics
    (conservative scope: every `match`; final case arm body
    must be exactly `assert_never(<subject>)`).
  - L8: `check-newtype-domain-primitives` semantics (role-
    to-NewType enumeration; partial-mismatch failure).
  - L9: `check-all-declared` semantics + `check-public-api-
    result-typed` scope adjustment from underscore-convention
    to `__all__`-based public-API detection.
  - L10: `check-no-write-direct` semantics (`sys.stdout.write`
    + `sys.stderr.write` ban with `_bootstrap.py` exemption).
  - L12: `check-pbt-coverage-pure-modules` semantics
    (`@given(...)` decorator presence verified per test
    module).
  - L15a: Import-Linter contract semantics (the three
    contracts replacing hand-written checks); how
    `check-imports-architecture` composes with the
    remaining hand-written `check-no-raise-outside-io`
    (AST-level raise-site discipline).
- `task-runner-and-ci-config` (v006; widened every pass
  since). v012 additions:
  - L1: `[tool.pyright]` `reportUnusedCallResult = "error"`.
  - L2: six pyright strict-plus diagnostics enabled in
    `[tool.pyright]`.
  - L3: ruff rule selection expanded to 16 categories above
    v011's 11 (combining L3's 14 + L10's T20 + L11's S = 16
    added; 27 total).
  - L6 + L11: `[tool.ruff.lint.flake8-tidy-imports]`
    banned-imports list contents (`abc.ABC`, `abc.ABCMeta`,
    `abc.abstractmethod`, `pickle`, `marshal`, `shelve`).
  - L12: `hypothesis` + `hypothesis-jsonschema` mise-pinned
    in `.mise.toml`; `pyproject.toml` test config integrates
    the strategies-from-schema discipline.
  - L13: `mutmut` mise-pinned in `.mise.toml`; new release-
    gate `just check-mutation` target; CI workflow split
    into per-commit (no mutation) + release-tag (with
    mutation).
  - L15a: `import-linter` mise-pinned in `.mise.toml`;
    `[tool.importlinter]` configuration in `pyproject.toml`
    expressing the three contracts; new
    `check-imports-architecture` target.
  - L2 follow-up: verify `typing_extensions` availability
    on Python 3.10 (transitive via dry-python/returns OR
    direct dev-only mise-pin); document the resolution in
    the `.mise.toml` section.
- `wrapper-input-schemas` (v008; widened in v012 per L4 + L8
  during the third careful-review pass). v012 additions:
  - L4: every wrapper-input-schema's paired dataclass
    (`ProposalFindings`, `DoctorFindings`, `SeedInput`,
    `ReviseInput`, `TemplateConfig`, `LivespecConfig`) uses
    the strict triple `@dataclass(frozen=True, kw_only=True,
    slots=True)`.
  - L8: domain-meaningful fields use the canonical NewType
    aliases from `livespec/types.py` — relevant mappings:
    `topic` → `TopicSlug`, `author` / `author_human` /
    `author_llm` → `Author`, `template` → `TemplateName`
    (note: field name is `template` matching `.livespec.jsonc`'s
    field; `template_root: Path` is a different field that
    uses raw `Path`), `check_id` → `CheckId`. Other fields use
    underlying primitives. `check-newtype-domain-primitives`
    enforces.
- `front-matter-parser` (v007; widened in v012 per L4 + L8
  during the third careful-review pass). v012 additions:
  - L4: `ProposedChangeFrontMatter` and `RevisionFrontMatter`
    dataclasses use the strict triple.
  - L8: NewType aliases for domain-meaningful fields —
    `topic` → `TopicSlug`, `author_human` / `author_llm` →
    `Author`.
- `claude-md-prose` (v006; widened in v012 during the third
  careful-review pass). v012 additions:
  - Per-directory `CLAUDE.md` notes for v012-introduced
    constraints: `livespec/parse/CLAUDE.md` and
    `livespec/validate/CLAUDE.md` note the L12 Hypothesis
    PBT requirement (each test module here MUST have ≥1
    `@given(...)`-decorated function); `livespec/types.py`
    is the canonical NewType-aliases location per L8 (single
    file; no CLAUDE.md required per the per-directory rule);
    `livespec/io/CLAUDE.md` notes that supervisor-stdout-write
    exemptions per L10 apply to `commands/<cmd>.py::main()`
    and `doctor/run_static.py::main()` only, NOT to `io/`
    helpers.

**New in v012:**

- **`basedpyright-vs-pyright`** (L14). When to re-evaluate
  switching from pyright to basedpyright. Standalone entry
  (NOT bundled with `returns-pyright-plugin-disposition`).
  Notes: ~30 stricter diagnostics become defaults; baselining-
  system migration; tool-fork tradeoff (smaller maintainer
  pool than upstream pyright). Scope: `SPECIFICATION/
  constraints.md` (`python-skill-script-style-requirements.md`
  companion); decision lives in the next focused tool-
  selection pass.

**Removed:**

None.

## Self-consistency check

Post-revision invariants rechecked:

- **`reportUnusedCallResult` enabled.** `[tool.pyright]` shows
  `reportUnusedCallResult = "error"` per L1.
- **Six strict-plus diagnostics enabled.** `[tool.pyright]`
  shows all six per L2; `typing_extensions` follow-up tracked.
- **Ruff selection at 16 categories above v011's 11 (27 total).** Style
  doc §"Linter and formatter" lists the full v012 selection;
  TID banned-imports list contains 6 entries (3 from L6 + 3
  from L11).
- **Strict-dataclass triple uniformly applied.** Style doc K4
  rule reads `frozen=True, kw_only=True, slots=True`;
  extended `check-keyword-only-args` walker enforces.
- **`check-no-inheritance` adopted; `@final` optional.** Style
  doc records the AST check; LivespecError hierarchy unchanged.
- **`abc.*` banned via TID.** Style doc TID config and the
  one-sentence Type-safety note both reference the ban.
- **`assert_never` mandated on every match.** Style doc has
  the rule + AST check.
- **`livespec/types.py` declared with 8 NewTypes.** Style doc
  enumerates the role-to-NewType mapping table; AST check
  verifies usage at the dataclass-field layer.
- **`__all__` mandated per module.** Style doc has the rule;
  `check-public-api-result-typed` rescoped.
- **`print` / `sys.stdout.write` / `sys.stderr.write` banned.**
  T20 in ruff selection; `check-no-write-direct` records
  `_bootstrap.py` exemption.
- **Forbidden imports active.** Ruff `S` enabled + TID list
  extended.
- **Hypothesis + mutmut + Import-Linter mise-pinned.** Not in
  the vendored bundle. License-policy expansion not needed.
- **L15b principle applied.** PROPOSAL.md and style doc both
  carry the user-provided-extensions scope clarification.
- **Recreatability.** A competent implementer can generate the
  v012 livespec plugin + built-in template + sub-commands +
  enforcement suite + dev-tooling from v012 PROPOSAL.md +
  `livespec-nlspec-spec.md` + updated
  `python-skill-script-style-requirements.md` + updated
  `deferred-items.md` alone. All cross-document references to
  the new pyright flags, ruff rules, dataclass triple,
  enforcement checks, and Import-Linter contracts reconciled.
  The user-provided-extensions scope boundary is explicit and
  consistent across PROPOSAL.md and the style doc.

## Outstanding follow-ups

Tracked in the updated `deferred-items.md` (see inventory
above). The v012 pass touched 6 existing entries (adding
scope-widenings — three during initial revision drafting:
`enforcement-check-scripts`, `task-runner-and-ci-config`,
`static-check-semantics`; three during the third careful-
review pass: `wrapper-input-schemas`, `front-matter-parser`,
`claude-md-prose`) and added 1 new entry (`basedpyright-vs-
pyright`). No entries were removed.

Open dependency follow-up: `typing_extensions` availability
on Python 3.10 for `@override` (L2) and `assert_never` (L7).
Resolution path: (a) verify transitive vendoring via
dry-python/returns, OR (b) add `typing_extensions` as a direct
mise-pinned dev-only dep, OR (c) bump the floor to Python
3.11 (out of scope for v012; would require its own pass).
Tracked under `task-runner-and-ci-config`.

## What was rejected

Nothing was rejected outright. Six items underwent revision
during the interview:

- **L5** (`@final` mandate) — moved from originally-recommended
  "both `@final` + AST check" to user-chosen "AST check only"
  after user asked whether `@final` was redundant. Honest
  analysis confirmed `check-no-inheritance` is strictly stronger
  as a single mechanism.
- **L6** (Protocol over ABC) — moved from originally-recommended
  dedicated `check-no-abc` AST check to user-chosen "extend
  L3's TID banned-imports config." User noted reuse of existing
  rule infrastructure was cleaner.
- **L12** (Hypothesis PBT) — packaging-corrected from "vendor"
  to "mise-pin" during revision drafting. User-chosen intent
  ("include Hypothesis; mandate PBT; AST check") preserved
  unchanged; the packaging mechanism was wrong in the critique.
  Sidesteps the MPL-2.0 license-policy expansion.
- **L13** (mutation testing) — packaging-corrected from "vendor"
  to "mise-pin" same reason as L12. User chose A (mandate +
  threshold + release-gate); 80% threshold flagged as tunable.
- **L15** (Import-Linter consolidation) — split into L15a
  (dev-tooling) and L15b (bundle) after user noted the
  original L15 conflated two different concerns.
- **L15b** specifically — the user's clarification request
  surfaced a NEW project-wide governing principle ("user-
  provided extensions get minimal requirements"). The
  principle resolved L15b directly (no bundle vendoring) and
  reshapes the scope statement for every v012-accepted
  constraint. Recorded as a new feedback memory.

No item "pulled threads" into reopening prior-version
decisions about what livespec does. The v009 I0 architecture-
vs-mechanism discipline, I10 domain-vs-bugs discipline, K4
keyword-only discipline, and K5 template-shape decoupling
all held throughout the pass. v012 preserves v011's
structural architecture while substantially tightening agent-
guardrails for livespec-authored Python and explicitly
bounding the enforcement scope to NOT touch user-provided
extension code.
