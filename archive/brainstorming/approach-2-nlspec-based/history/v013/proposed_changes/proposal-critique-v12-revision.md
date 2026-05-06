---
proposal: proposal-critique-v12.md
decision: modify
revised_at: 2026-04-23T23:30:00Z
author_human: thewoolleyman
author_llm: Claude Opus 4.7 (1M context)
---

# Revision: proposal-critique-v12

## Provenance

- **Proposed change:** `proposal-critique-v12.md` (in this directory)
  — a recreatability-and-integration-gap critique surfacing 13
  items across v012 PROPOSAL.md,
  `python-skill-script-style-requirements.md`, and
  `deferred-items.md`. The critique was framed as a mix of:
  - recreatability defects (places where a competent implementer
    building from the three brainstorming docs alone would be
    blocked or forced to guess),
  - workflow / discipline gaps (operational-semantics ambiguities
    that would produce divergent implementations), and
  - cross-doc self-consistency residue the v012 careful-review
    passes missed.
- **Revised by:** thewoolleyman (human) in dialogue with Claude
  Opus 4.7 (1M context).
- **Revised at:** 2026-04-23 (UTC).
- **Scope:** v012 PROPOSAL.md + python style doc + `deferred-items.md`
  → v013 equivalents. `livespec-nlspec-spec.md` unchanged.
  `goals-and-non-goals.md`, `prior-art.md`, and
  `subdomains-and-unsolved-routing.md` unchanged. Focus areas:
  closing the largest recreatability blocker (M1:
  `typing_extensions` disposition for L2 + L7); two operational-
  contract ambiguities (M2/M8: heading-coverage registry format
  + lifecycle; M3: mutation-testing first-measurement bootstrap;
  M4: retry-count discipline); one self-contradiction
  (M5: `check-no-inheritance` leaf-closed intent vs codified
  transitive AST semantics); one recreatability gap (M6:
  `validate/` per-schema pairing); one mechanism-level anchor
  (M7: Import-Linter concrete contract example); six smaller
  cleanups (C1-C6).

## Pass framing

This pass was a **recreatability-and-integration-gap critique**
producing 13 items plus one new item (M8) surfaced mid-interview
when the user clarified that the M2 format question had an
unaddressed operational-lifecycle counterpart. Each item carried
one of four NLSpec failure modes (ambiguity / malformation /
incompleteness / incorrectness) and was grouped by impact:
- major gap (M1, the single largest recreatability blocker),
- significant gaps (M2-M7, each closing a concrete
  recreatability / contract / self-consistency hole),
- smaller cleanup (C1-C6, cross-doc residue the v012 review
  passes missed).

One item (M8) was added mid-interview. One item (M2) had its
scope narrowed mid-interview to keep a single decision per
question (the user reframed my initial M2 formulation, which
bundled the format question with a lifecycle question, into
two separate items).

Three items (M4, M5, C5) moved from recommended disposition to
alternate option based on user choice; in each case the
alternate is the more conservative or tighter option:
- **M4** moved from "Option A: 3 retries = 3 invocations
  following the initial (4 total max)" to "Option B: 3 total
  invocations (initial + 2 retries)." The rename from "retries"
  to "attempts" is slightly more churn but produces a cleaner
  3-total count that doesn't ambiguously count the initial.
- **M5** moved from "Option A: accept transitive-subclass AST
  semantics as authoritative" to "Option B: tighten AST check
  to direct-parent-only." The tighter reading enforces the
  leaf-closed intent the v012 revision file expressed but did
  not enforce mechanically.
- **C5** moved from "Option A: canonicalize on short
  `livespec/**` + explanatory note" to "Option B: canonicalize
  on full `.claude-plugin/scripts/livespec/**` path form
  throughout." Verbose but unambiguous; no shortcut/prefix
  cognitive load for readers.

One item (M1) underwent a mid-lifecycle correction. The
interview initially resolved M1 with Option A ("mise-pin
`typing_extensions` as a direct dev-only dep"); during the
subsequent apply phase, the assistant caught that the option's
framing was self-contradictory (mise-pinning makes a tool
available to DEVELOPERS only, but `livespec/**` imports
`@override` and `assert_never` from `typing_extensions` at
USER runtime). The user was re-interviewed with corrected
framing; the final disposition is **Option A''': vendor a
~15-line shim at `.claude-plugin/scripts/_vendor/
typing_extensions/__init__.py`**. The shim retains the
`typing_extensions` module name so pyright's
`reportImplicitOverride` and `check-assert-never-
exhaustiveness` recognize the import path; it exports exactly
`override` (no-op decorator per PEP 698) and `assert_never`
(raises `AssertionError` at runtime, `Never`-typed parameter);
it ships the upstream PSF-2.0 `LICENSE` file verbatim with
attribution to
`https://github.com/python/typing_extensions`. The vendored-
libs license policy is extended from
`MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0` to include
`PSF-2.0` narrowly for this one library. Future widening of
the shim (re-exporting additional symbols) is a one-line
edit; re-vendoring full upstream is a scope-widening decision,
not a v013 default. `typing_extensions` is NOT mise-pinned
(it's vendored, not dev-only).

## Summary of dispositions

| Item | Failure mode | Disposition |
|---|---|---|
| M1 | incompleteness | (corrected mid-lifecycle) A''' — vendor `typing_extensions` as ~15-line shim at `_vendor/typing_extensions/__init__.py`; license policy extended to admit PSF-2.0; import `@override` + `assert_never` from `typing_extensions` uniformly |
| M2 | incompleteness | A — registry shape `{spec_file, heading, test}`; `Scenario:`-prefixed headings excluded from meta-test scope |
| M3 | incompleteness | A — `.mutmut-baseline.json` + ratchet comparison; `just check-mutation` emits structured JSON mutant report |
| M4 | ambiguity | (revised) B — 3 total attempts (1 initial + 2 retries); rename "retries" → "attempts" in all sections |
| M5 | malformation | (revised) B — `check-no-inheritance` tightens to direct-parent-only; LivespecError subclasses NOT transitively extensible; enforces v012 revision-file leaf-closed intent |
| M6 | incompleteness | A — three-way `check-schema-dataclass-pairing` (schema ↔ dataclass ↔ validator); enumerate v1 validators in PROPOSAL.md |
| M7 | incompleteness | A — concrete minimum `[tool.importlinter]` TOML example + illustrative caveat preserving architecture-vs-mechanism |
| M8 | incompleteness | A2'-repo — registry field `reason`; `test: "TODO"` with non-empty `reason` tolerated by `just check`; new release-gate `check-no-todo-registry` rejects all TODO; livespec-repo-internal (not shipped) |
| C1 | incorrectness | A — fix typo `python-skill-script-script-style-requirements.md` → single "script" at PROPOSAL.md line 392 |
| C2 | malformation | B — style doc §"Dev tooling and task runner" references PROPOSAL.md as single source of truth for dev-tool enumeration |
| C3 | ambiguity | A — codify test-filename rule for leading-underscore source modules (strip leading underscore: `_bootstrap.py` → `test_bootstrap.py`) |
| C4 | ambiguity | A — keep `livespec/types.py`; add one-sentence note in style doc §"Type safety — Domain primitives via `NewType`" acknowledging stdlib-`types` shadow and TID-ban safety |
| C5 | ambiguity | (revised) B — canonicalize on full-path `.claude-plugin/scripts/livespec/**` etc. throughout style doc |
| C6 | ambiguity | A — replace "unconditionally" at PROPOSAL.md line 889 with precedence-matching phrasing + cross-reference to four full-precedence sections |

## Governing principles reinforced

- **Recreatability discipline.** M1, M2, M6, M7 all close gaps
  where a competent implementer could not proceed from the
  brainstorming docs alone. M8 converted a registry-lifecycle
  ambiguity into a concrete livespec-repo-internal mechanism
  (`check-no-todo-registry` release-gate) after the user's
  architectural clarification that shipped-plugin surface must
  stay livespec-user-generic.
- **Strongest-possible guardrails for livespec-authored
  Python.** M5's tightening (direct-parent-only for
  `check-no-inheritance`) enforces the v012 leaf-closed intent
  mechanically; an LLM writing `class X(UsageError):` is now
  rejected at check time rather than accepted via the
  transitive-subclass path. M1's `typing_extensions` vendored
  shim (A''') closes the implementation-blocking ambiguity for
  the L2 + L7 strict-plus rules by making `override` and
  `assert_never` available at user runtime from the
  `typing_extensions` module-named import path.
- **Architecture-vs-mechanism** (v009 I0). M7 preserves
  mechanism freedom via an illustrative caveat ("contract names
  / structure / layer names / ignore globs illustrative;
  authoritative rules are three English-language statements")
  while anchoring the load-bearing outcomes with a minimum TOML
  example.
- **Shipped-vs-not-shipped discipline** (new, reinforced
  mid-interview at M8). Livespec-repo-only artifacts
  (`dev-tooling/`, `tests/`, `justfile`, `lefthook.yml`,
  `.mise.toml`, and now the `heading-coverage.json` lifecycle
  machinery) are specified in PROPOSAL.md + style doc but do
  NOT ship to users via `.claude-plugin/**`. The `revise`
  wrapper, shipped `doctor/static/` checks, and shipped
  `SKILL.md` prose stay user-generic; livespec-dev enforcement
  runs via `just` targets under `dev-tooling/` that are
  invisible to users of the plugin. Recorded implicitly in the
  M8 disposition; adjacent to the v012 L15b "user-provided
  extensions get minimal requirements" principle but distinct
  (L15b is about what livespec DEMANDS of extension authors;
  this is about what livespec SHIPS to users).
- **Single source of truth.** C2 moves the dev-dep enumeration
  to a single location (PROPOSAL.md). M6's three-way pairing
  check extends the existing drift-catcher to cover validators
  too.
- **Static enumeration over dynamic discovery.** M6 explicitly
  enumerates v1 validators in the PROPOSAL.md layout tree
  (matching the v007 static registry principle).

## Disposition by item

### M1. `typing_extensions` disposition (incompleteness → accepted, corrected option A''')

The largest recreatability blocker in v012. L2's
`reportImplicitOverride = "error"` requires `@override`
decorators; L7's `assert_never` exhaustiveness requires
`assert_never`; both live in `typing` from Python 3.11+ only.
On the 3.10 floor (codified in `.mise.toml` discipline +
PROPOSAL.md §Runtime dependencies), neither symbol is
available from stdlib `typing`. v012 deferred the resolution
to `task-runner-and-ci-config` with three open options; v013
closes the resolution with **corrected Option A''' (vendored
minimal shim)**.

**Interview / correction history.** The initial interview
answer selected Option A ("mise-pin `typing_extensions` as a
direct dev-only dep"). During the apply phase, the assistant
caught that the option was self-contradictory: mise makes a
tool available to DEVELOPERS only at their shell, but
`livespec/**` imports `@override` and `assert_never` at USER
runtime via the shipped plugin. A mise-pinned typing_extensions
is invisible to end users. The user was re-interviewed with
corrected framing (A' = full vendor; A'' = self-implement with
livespec-authored module but no pyright recognition on
`override`; A''' = vendor a minimal shim keeping the
`typing_extensions` module name). The user chose A''' after
noting the library size (~150 KB) was disproportionate to the
~10 lines of actual usage; A'' was ruled out because pyright
recognizes `@override` only when imported from `typing` or
`typing_extensions` by fully-qualified name.

Resolution:

- `.claude-plugin/scripts/_vendor/typing_extensions/__init__.py`
  is a ~15-line shim file exporting exactly `override` (no-op
  decorator per PEP 698, sets `method.__override__ = True`) and
  `assert_never` (raises `AssertionError` at runtime; signature
  `def assert_never(arg: Never) -> NoReturn`). The module name
  `typing_extensions` is retained so pyright recognizes the
  import path.
- `.claude-plugin/scripts/_vendor/typing_extensions/LICENSE` is
  a verbatim copy of the upstream PSF-2.0 license, with
  attribution to
  `https://github.com/python/typing_extensions`.
- python style doc §"Vendored third-party libraries" — extend
  the license policy from `MIT, BSD-2-Clause, BSD-3-Clause,
  Apache-2.0` to include `PSF-2.0` narrowly for this one
  library. Add `typing_extensions` as a fifth bullet in the
  vendored-libs list documenting the shim + upstream
  attribution + widening-is-one-line-edit property.
- python style doc §"Type safety" — replace the existing
  "Open dependency follow-up" block with:

> **`@override` and `assert_never` import source (v013 M1
> resolution).** Both symbols MUST be imported uniformly from
> `typing_extensions`, not from stdlib `typing`, regardless
> of Python version. `typing_extensions` is **vendored as a
> minimal shim** at `.claude-plugin/scripts/_vendor/
> typing_extensions/__init__.py` (v013 M1); the shim exports
> exactly `override` and `assert_never` and retains the
> `typing_extensions` module name so pyright's
> `reportImplicitOverride` recognizes the import path and
> `check-assert-never-exhaustiveness` recognizes the
> Never-narrowing signature. Uniform import discipline
> (`from typing_extensions import override, assert_never`)
> eliminates per-version conditionals and survives a future
> widening of the shim or re-vendoring of the full upstream
> library.

- python style doc §"Exhaustiveness" — update the existing
  parenthetical from "`assert_never` is from `typing` (3.11+)
  or `typing_extensions` (3.10)" to "`assert_never` is
  imported from `typing_extensions` per the v013 M1 uniform-
  import discipline."
- python style doc §"Structural pattern matching —
  HelpRequested example" — update the code-comment from
  `# Python 3.11+; on 3.10 use typing_extensions` to
  `# per v013 M1 uniform-import discipline`.
- python style doc §"Type safety — Inheritance and structural
  typing" — the `@final` note simplifies to "imported from
  `typing_extensions`" for consistency; extending the shim to
  export `final` is a one-line edit if/when needed.
- PROPOSAL.md §"Runtime dependencies — Vendored pure-Python
  libraries" — add `typing_extensions` as the fifth vendored
  lib with shim + attribution + PSF-2.0 details.
- PROPOSAL.md §"Skill layout inside the plugin" — add
  `typing_extensions/` to the `_vendor/` layout tree.
- PROPOSAL.md §"Runtime dependencies — Developer-time
  dependencies" — do NOT add `typing_extensions` to the
  mise-pinned list; it is vendored, not dev-only. Add a note
  at the end of the Developer-time section pointing to the
  vendored-libs section.
- PROPOSAL.md §"Developer tooling layout" `.mise.toml`
  annotation and `.vendor.jsonc` annotation — update to note
  `typing_extensions` is vendored, NOT mise-pinned.
- `deferred-items.md` `task-runner-and-ci-config` entry —
  close the "typing_extensions availability follow-up" open
  question; replace with the v013 M1 CLOSED disposition.
- `deferred-items.md` `static-check-semantics` entry's
  `check-assert-never-exhaustiveness` subsection — the check
  MUST verify the import path resolves to `typing_extensions`
  specifically; a stray `from typing import assert_never`
  fails the check.

### M2. `heading-coverage.json` format (incompleteness → accepted, option A)

v012's meta-test registry at `tests/heading-coverage.json` was
shaped as `[{heading, test}, ...]`. Multiple spec files can
have the same `##` heading text (e.g., "Overview" appearing
in both `spec.md` and `contracts.md`), but the registry had
no `spec_file` field to disambiguate. Separately, scenario-
block headings (`## Scenario: <name>`) in `scenarios.md` would,
without a scope exclusion, require per-scenario registry
entries — not the intended coverage granularity.

Resolution:

- PROPOSAL.md §"Testing approach — Coverage registry"
  (lines 2104-2113) — update the registry shape example:

> **Coverage registry**: `tests/heading-coverage.json` maps
> (spec file, heading) triples to test identifiers:
>
> ```json
> [
>   { "spec_file": "spec.md", "heading": "Proposed-change file format", "test": "test_propose_change.py::test_multi_proposal_write" }
> ]
> ```
>
> The `spec_file` field is the spec-root-relative path to the
> specification file containing the heading. The `heading` field
> is the exact `##` heading text without the `## ` prefix. The
> `test` field is a pytest node identifier
> (`<path>::<function>`), OR (per M8 below) the literal
> `"TODO"` when the test is not yet authored — in which case
> the entry MUST also carry a non-empty `reason` field.
>
> **Scope exclusion.** The meta-test skips any `##` heading
> whose text begins with the literal `Scenario:` prefix.
> Scenario blocks are exercised end-to-end by the per-spec-file
> rule test for the scenario-carrying spec file; per-scenario
> registry entries are not required.

### M3. Mutation-testing first-measurement bootstrap (incompleteness → accepted, option A)

v012 L13 set the mutation-kill-rate threshold at ≥80% with
the note "tunable on first real measurement via a new propose-
change cycle." But the first measurement may be well below 80%,
and the propose-change cycle to adjust requires livespec's own
tooling to work. Without a concrete bootstrap discipline, CI
releases block indefinitely. Separately, the failure mode of
`just check-mutation` was unspecified (exit-only vs identifying
survivors); without mutant identification, remediation is
trial-and-error.

Resolution:

- python style doc §"Mutation testing as release-gate" — add:

> **Bootstrap discipline.** Before first release-tag run, a
> `.mutmut-baseline.json` file is committed recording the
> mutation-kill-rate measurement at initial adoption (fields:
> `measured_at`, `kill_rate_percent`, `mutants_surviving`,
> `mutants_total`). The `[tool.mutmut]` threshold in
> `pyproject.toml` is set to 80%; each subsequent release-tag
> run compares the current measurement against
> `min(baseline.kill_rate_percent - 5, 80)`. Once a release-tag
> run measures sustained ≥80% kill rate, `.mutmut-baseline.json`
> is deprecated (content retained for history; threshold
> collapses to the static 80%) via a new propose-change cycle.
>
> **Failure output.** `just check-mutation` MUST emit to stderr
> a structured JSON summary when the threshold fails,
> containing: `threshold` (the effective threshold from the
> ratchet), `kill_rate_percent` (measured), and
> `surviving_mutants` (an array of
> `{file, line, mutation_kind}` entries). The implementation
> mechanism is implementer choice inside the `just` recipe.

- python style doc §"Enforcement suite — release-gate targets"
  — update the `just check-mutation` row description to note
  the baseline/ratchet + structured-output discipline.
- `deferred-items.md` `task-runner-and-ci-config` entry —
  record `.mutmut-baseline.json` as a new tracked file at repo
  root (sibling of `pyproject.toml`).

### M4. Retry-count discipline (ambiguity → accepted, revised option B)

v012's "up to 3 retries" phrasing could be read as either 3
total invocations (1 initial + 2 retries) or 4 total
invocations (1 initial + 3 retries). Two implementations
diverge by one wrapper invocation; time-to-abort varies.

REVISED from the originally recommended "Option A: 3 retries =
3 invocations following the initial (4 total max)" to
user-chosen "Option B: 3 total invocations (initial + 2
retries)." The tighter total preserves the spirit of "up to
3" while removing the count-the-initial ambiguity.

Resolution:

- Rename "retries" → "attempts" wherever the count is
  specified (not where "retryable" is used as a property).
- PROPOSAL.md §"Per-sub-command SKILL.md body structure"
  step 4 (lines 239-243) — rewrite:

> - **Retry-on-exit-4:** on wrapper exit code `4` (schema
>   validation failed; LLM-provided JSON payload did not conform
>   to the wrapper's input schema), re-invoke the relevant
>   template prompt with the structured error context from stderr
>   and re-assemble the JSON payload. **Up to 3 attempts
>   total (1 initial invocation plus up to 2 retries) per
>   PROPOSAL.md §"Templates — Skill↔template communication
>   layer";** abort on the third failing attempt with a visible
>   user message. Exit code `3` (precondition/doctor-static
>   failure) is NOT retryable — it surfaces the findings to the
>   user and aborts.

- PROPOSAL.md §"Per-sub-command SKILL.md body structure"
  exit-4 row (line 263-265) — update to "retryable via template
  re-prompt, up to 2 retries (3 attempts total)."
- PROPOSAL.md §"Templates — Skill↔template communication layer"
  (line 1066-1071) — update "After a configured number of
  retries (3), the skill aborts…" to "After 3 attempts total
  (1 initial + 2 retries) fail, the skill aborts…"
- PROPOSAL.md §"seed" (line 1266) — update "up to 3 retries"
  → "up to 2 retries (3 attempts total)".
- PROPOSAL.md §"propose-change" (line 1322) — same update.
- PROPOSAL.md §"critique" (line 1387) — same update.
- PROPOSAL.md §"revise" (lines 1474-1475) — same update.
- PROPOSAL.md line 465 ("abort after N retries") — update
  to "abort after N attempts".
- python style doc §"Exit code contract" exit-4 row
  (line 1215) — update "up to 3 retries" to "up to 2 retries
  (3 attempts total)".
- python style doc §"Exit code contract" `ValidationError`
  docstring (line 1250) — same update.
- `deferred-items.md` `skill-md-prose-authoring` entry
  (line 746) — update wording to "up to 2 retries (3 attempts
  total); exit 3 is NOT retryable".

### M5. `check-no-inheritance` direct-parent-only (malformation → accepted, revised option B)

The v012 revision file stated that "multi-level subclassing of
any leaf domain error is forbidden by the rule (the leaf is
not in the allowlist)" — a leaf-closed intent. But the codified
AST-check semantics in `deferred-items.md` (v012-era
`static-check-semantics` entry) accepted "a `LivespecError`
subclass (transitively; check examines the base's MRO)." The
two readings diverge: `class RateLimitError(UsageError):` is
accepted by transitive-MRO walk and rejected by leaf-closed
intent.

REVISED from originally-recommended "Option A: accept
transitive AST semantics as authoritative" to user-chosen
"Option B: tighten AST check to direct-parent-only." The
tighter reading enforces the leaf-closed intent the v012
revision file expressed but did not enforce mechanically.

Resolution:

- python style doc §"Type safety — Inheritance and structural
  typing" (line 700-712) — rewrite:

> Class inheritance in `.claude-plugin/scripts/livespec/**`,
> `.claude-plugin/scripts/bin/**`, and
> `<repo-root>/dev-tooling/**` is RESTRICTED. The AST check
> `check-no-inheritance` rejects any `class X(Y):` definition
> where `Y` is not in the **direct-parent allowlist**:
> `{Exception, BaseException, LivespecError, Protocol,
> NamedTuple, TypedDict}`. The rule is DIRECT-PARENT only;
> `LivespecError` subclasses (e.g., `UsageError`,
> `ValidationError`) are NOT acceptable bases for further
> subclassing. New domain-error classes MUST inherit directly
> from `LivespecError` and explicitly set their own `exit_code`
> class attribute (or rely on `LivespecError`'s default of 1).
>
> This codifies the flat-composition direction: the
> `LivespecError` hierarchy is intentionally ONE level deep
> below the open base `LivespecError`. Adding a new domain
> error subclass like `RateLimitError(LivespecError)` is
> permitted by the rule; `RateLimitError(UsageError)` is NOT.
> Authors who want "rate-limit-like-usage-error" semantics set
> `RateLimitError.exit_code = 2` explicitly.

- python style doc canonical target list
  `check-no-inheritance` row (line 1476) — update the
  description to drop the "or a `LivespecError` subclass"
  phrasing; keep only the direct-parent allowlist.
- `deferred-items.md` `static-check-semantics` entry's
  `check-no-inheritance` semantics subsection (line 510-521)
  — rewrite to remove the "transitively; check examines the
  base's MRO" + "LivespecError subclass detection examines
  whether the base class is defined in `livespec/errors.py`
  AND has `LivespecError` in its base list" wording. Replace
  with: "For every `ast.ClassDef` with non-empty `bases`,
  inspect each base; reject unless base name resolves (by
  AST-level name resolution; imports walked) to a class in
  the direct-parent allowlist `{Exception, BaseException,
  LivespecError, Protocol, NamedTuple, TypedDict}`. `LivespecError`
  subclasses are NOT acceptable bases; the check rejects
  `class X(UsageError):` even though `UsageError` is itself a
  `LivespecError` subclass. The direct-parent-only reading
  enforces the v012 leaf-closed intent mechanically."

### M6. `validate/` per-schema pairing (incompleteness → accepted, option A)

v012 PROPOSAL.md's `validate/` directory in the package-layout
tree listed no modules, and `check-schema-dataclass-pairing`
walked only schema ↔ dataclass. A competent implementer could
infer that each schema needs a validator (per the factory-shape
contract in the style doc), but nothing mechanically enforced
validator existence, and the validator enumeration was absent.

Resolution:

- PROPOSAL.md §"Skill layout inside the plugin" (lines 133-134)
  — extend the `validate/` entry to enumerate v1 validators:

```
│       ├── validate/                        # pure validators (Result-returning, factory shape)
│       │   ├── doctor_findings.py
│       │   ├── proposal_findings.py
│       │   ├── seed_input.py
│       │   ├── revise_input.py
│       │   ├── livespec_config.py
│       │   ├── template_config.py                    # (v011 K5)
│       │   ├── proposed_change_front_matter.py       # (deferred: front-matter-parser)
│       │   └── revision_front_matter.py              # (deferred: front-matter-parser)
```

- python style doc §"Per sub-package conventions — `validate/`"
  (line 229-237) — extend:

> **`validate/`** — pure validators using the **factory shape**:
> each validator at `validate/<name>.py` exports a function
> `validate_<name>(payload: dict, schema: dict) ->
> Result[<Dataclass>, ValidationError]` where `<Dataclass>` is
> the paired dataclass at `schemas/dataclasses/<name>.py`.
> Validators invoke `livespec.io.fastjsonschema_facade.compile_schema`;
> the facade owns the compile cache. Every schema at
> `schemas/*.schema.json` MUST have a paired validator at
> `validate/<name>.py`; drift (schema without validator; dataclass
> without validator) is caught by `check-schema-dataclass-pairing`
> (now a three-way walker per v013 M6). `validate/` stays strictly
> pure (no module-level mutable state, no filesystem I/O).

- python style doc canonical target list
  `check-schema-dataclass-pairing` row (line 1471) — update to
  three-way:

> | `just check-schema-dataclass-pairing` | AST: for every `schemas/*.schema.json`, verifies a paired dataclass at `schemas/dataclasses/<name>.py` (the `$id`-derived name) AND a paired validator at `validate/<name>.py` exists; every listed schema field matches the dataclass's Python type; vice versa in both walks. Drift in any direction fails. |

- `deferred-items.md` `static-check-semantics` entry's
  `check-schema-dataclass-pairing` semantics subsection
  (line 343-349 + line 423-433) — widen to three-way walker
  scope; retain the J11 walker-scope note (still walks
  `schemas/dataclasses/*.py` as one of three sides).

### M7. Import-Linter minimum concrete example (incompleteness → accepted, option A)

v012 L15a adopted Import-Linter for dev-tooling architecture
enforcement, replacing three hand-written checks. The style
doc described the three contract intents in prose but left
contract configuration "implementer choice." The outcomes
(layer ordering, forbidden-module enumeration) are load-bearing
for purity + layered architecture + raise-discipline; three
implementers would likely produce three different layer
orderings.

Resolution:

- python style doc §"Enforcement suite" — add a new
  subsection `### Import-Linter contracts (minimum configuration)`
  anchoring the load-bearing outcomes:

> The three L15a contracts in `pyproject.toml`'s
> `[tool.importlinter]` section MUST collectively enforce
> purity, layered architecture, and raise-discipline import
> surface. The minimum concrete configuration below is
> illustrative of the canonical shape; contract names, layer
> names, and ignore-import globs MAY be restructured so long
> as the three English-language rules below are enforced.
>
> ```toml
> [tool.importlinter]
> root_packages = ["livespec"]
>
> [[tool.importlinter.contracts]]
> name = "parse-and-validate-are-pure"
> type = "forbidden"
> source_modules = ["livespec.parse", "livespec.validate"]
> forbidden_modules = [
>     "livespec.io",
>     "subprocess",
>     "returns.io",
>     "socket",
>     "http",
>     "urllib",
>     "pathlib",
> ]
>
> [[tool.importlinter.contracts]]
> name = "layered-architecture"
> type = "layers"
> layers = [
>     "livespec.commands | livespec.doctor",
>     "livespec.io",
>     "livespec.validate",
>     "livespec.parse",
> ]
>
> [[tool.importlinter.contracts]]
> name = "livespec-errors-raise-discipline-imports"
> type = "forbidden"
> source_modules = ["livespec"]
> forbidden_modules = ["livespec.errors"]
> ignore_imports = [
>     "livespec.io.* -> livespec.errors",
>     "livespec.errors.* -> livespec.errors",
> ]
> ```
>
> The authoritative rules (enforced by ANY valid Import-Linter
> configuration satisfying these three statements):
>
> 1. Modules in `livespec.parse` and `livespec.validate` MUST
>    NOT import `livespec.io`, `subprocess`, filesystem APIs
>    (`pathlib`, `open`), `returns.io`, `socket`, `http`,
>    `urllib`.
> 2. Higher layers MAY import lower layers but not vice-versa;
>    the layer stack is `parse` < `validate` < `io` <
>    `commands` | `doctor`. No circular imports follow by
>    construction.
> 3. `livespec.errors.LivespecError` (and any of its
>    subclasses) MAY be imported only from `livespec.io.*` and
>    `livespec.errors` itself. Other modules must not import
>    `LivespecError` subclasses for raising.

- `deferred-items.md` `static-check-semantics` entry's
  Import-Linter contract semantics subsection (line 618-642)
  — shorten the prose description and reference the style-doc
  codified minimum configuration rather than re-describing
  the three contracts independently.

### M8. `heading-coverage.json` update-lifecycle (incompleteness → accepted, option A2'-repo)

Added mid-interview after the user's clarification that the
M2 format question had an orthogonal lifecycle question
("where does it live? When does it get committed? How does
it stay source-of-truth?"). The user additionally clarified
that lifecycle-enforcement machinery must NOT leak into the
shipped plugin surface (shipped `revise/SKILL.md`, shipped
doctor-static checks, or shipped wrappers) — because
`heading-coverage.json` is a livespec-repo-internal artifact
at `<repo-root>/tests/`, not a user-spec concern.

The architectural clarification surfaced mid-interview: v012's
own `dev-tooling/`, `justfile`, `.mise.toml`, `tests/` tree,
etc. are ALREADY livespec-repo-only artifacts specified in
PROPOSAL.md + style doc without shipping. The
`heading-coverage.json` lifecycle fits the same pattern.

Resolution:

- PROPOSAL.md §"Testing approach" — replace lines 2118-2119
  (the "implementation concern, not specified here" punt)
  with a concrete livespec-repo-internal lifecycle:

> **Registry lifecycle.** Entries in `tests/heading-coverage.json`
> may carry `test: "TODO"` when a real test for the referenced
> rule does not yet exist; such entries MUST also carry a
> non-empty `reason` field explaining why (e.g.,
> `"rule added in v015; implementation and test pending"`).
> The meta-test `test_meta_section_drift_prevention.py`
> accepts `"TODO"` test values when `reason` is non-empty;
> otherwise rejects.
>
> The release-gate target `just check-no-todo-registry`
> (grouped with `just check-mutation` on the release-tag CI
> workflow only; NOT included in `just check`; NOT run
> per-commit) rejects any `test: "TODO"` entry regardless of
> `reason`, ensuring every release ships with full rule-test
> coverage.
>
> Registry-update authority is livespec-repo-internal:
> whoever lands a spec change introducing a new `##` heading
> SHOULD add a corresponding registry entry in the same
> commit (with a real test if implemented; with
> `test: "TODO"` + reason otherwise). The meta-test catches
> drift at `just check` time; the release-gate forces
> eventual cleanup.

- python style doc §"Enforcement suite — release-gate
  targets" — add `just check-no-todo-registry` row:

> | `just check-no-todo-registry` | Rejects any `test: "TODO"` entry in `tests/heading-coverage.json`. Release-gate only (paired with `check-mutation` on release-tag CI workflow); NOT in `just check`; NOT per-commit. |

- `deferred-items.md` `task-runner-and-ci-config` entry —
  add the new `check-no-todo-registry` release-gate target.

### C1. Typo `python-skill-script-script-style-requirements.md` (incorrectness → accepted, option A)

Four v012 careful-review passes missed the double-"script"
typo at PROPOSAL.md line 392.

Resolution:

- PROPOSAL.md line 392 — change
  `python-skill-script-script-style-requirements.md` to
  `python-skill-script-style-requirements.md`.

### C2. Dev-dependency list drift (malformation → accepted, option B)

PROPOSAL.md §Developer-time dependencies enumerates the full
v012 dev deps; style doc §Dev tooling and task runner line
1423-1424 lists only the v011 subset (missing hypothesis,
hypothesis-jsonschema, mutmut, import-linter; and now
typing_extensions per M1).

Resolution:

- python style doc §"Dev tooling and task runner" line
  1423-1424 — replace the enumeration with:

> - `.mise.toml` pins every dev tool listed in PROPOSAL.md
>   §"Runtime dependencies — Developer-time dependencies." No
>   tool pinning is duplicated here; single source of truth
>   lives in PROPOSAL.md to eliminate drift.

### C3. Test-naming convention for leading-underscore modules (ambiguity → accepted, option A)

`_bootstrap.py` → `test_bootstrap.py` (single underscore) is
the existing convention, but the mirror rule didn't codify
leading-underscore handling.

Resolution:

- PROPOSAL.md §"Testing approach — Test organization rules"
  — add a new bullet:

> **Leading-underscore source modules.** Source modules whose
> filename begins with `_` (e.g., `_bootstrap.py`) use a test
> filename that strips the leading underscore:
> `_<name>.py` → `test_<name>.py` (NOT `test__<name>.py`).
> This matches pytest's idiomatic `test_`-prefix convention.

### C4. `livespec/types.py` shadows stdlib `types` (ambiguity → accepted, option A)

v012 L8's `livespec/types.py` NewType-aliases module shadows
stdlib `types`. TID's `ban-relative-imports = "all"` rule
precludes any import-resolution bug; the shadow is a minor
authoring smell.

Resolution:

- python style doc §"Type safety — Domain primitives via
  `NewType`" — add a one-sentence note following the
  canonical-roles table:

> The module name `livespec.types` intentionally echoes the
> stdlib `types` module name. The TID rule
> `ban-relative-imports = "all"` (see §"Linter and formatter")
> and absolute-import discipline throughout `livespec/**`
> preclude any import-resolution conflict between
> `from livespec.types import Author` and
> `from types import ModuleType`.

### C5. Scope wording canonicalize on full-path form (ambiguity → accepted, revised option B)

Three different wordings for semantically the same scope
appear throughout the style doc: `.claude-plugin/scripts/
livespec/**`, `scripts/livespec/**`, and `livespec/**`. Same
for `bin/**`. NLSpec spec-economy principle says define-once.

REVISED from originally-recommended "Option A: canonicalize
on short form with explanatory note" to user-chosen
"Option B: canonicalize on full-path form throughout." The
full-path form is verbose but maximally explicit with no
shortcut-resolution cognitive load.

Resolution:

- python style doc — sweep-replace:
  - `livespec/**` → `.claude-plugin/scripts/livespec/**`
    (where `livespec/**` refers to the Python package tree).
  - `bin/**` → `.claude-plugin/scripts/bin/**`.
  - `dev-tooling/**` → `<repo-root>/dev-tooling/**`
    (where it is not already prefixed).
  - `scripts/livespec/**` → `.claude-plugin/scripts/livespec/**`.
  - `scripts/bin/**` → `.claude-plugin/scripts/bin/**`.
- The sweep applies to prose rules, subsection headings, and
  canonical target-list table entries uniformly. Code
  examples (e.g., inside triple-backtick blocks) that import
  from `livespec.<submodule>` are NOT path-scope statements
  and stay unchanged (they're Python import-path form, not
  filesystem-path form).

### C6. `LIVESPEC_AUTHOR_LLM` "unconditionally" wording (ambiguity → accepted, option A)

PROPOSAL.md §Environment variables line 887-894 says the env
var is used "unconditionally" — but CLI `--author` wins over
env var per the unified precedence documented in four other
sections. "Unconditionally" misleads readers who only scan
the env-var section.

Resolution:

- PROPOSAL.md §"Environment variables" (line 886-894) —
  rewrite the `LIVESPEC_AUTHOR_LLM` paragraph:

> - **`LIVESPEC_AUTHOR_LLM`** (default unset). When set and
>   non-empty, the `propose-change`, `critique`, and `revise`
>   wrappers use this value for the `author` payload/file-
>   front-matter field (and for the `author_llm` field on
>   revision-file front-matter, where applicable), overriding
>   the LLM-self-declared `author` in the JSON payload and the
>   `"unknown-llm"` fallback. A `--author <id>` CLI flag on
>   the invocation still wins over the env var per the
>   unified precedence rules — see §"propose-change → Author
>   identifier resolution", §"critique", §"revise", and
>   §"Revision file format".

## Deferred-items inventory (carried forward + scope-widened + new)

Per the deferred-items discipline, every carried-forward item
is enumerated below. Additions, scope-widenings, and renames
are flagged.

**Carried forward unchanged from v012:**

- `template-prompt-authoring` (v001; unchanged by this pass).
- `python-style-doc-into-constraints` (v005; unchanged).
- `companion-docs-mapping` (v001; unchanged).
- `returns-pyright-plugin-disposition` (v007; unchanged).
- `user-hosted-custom-templates` (v010 J3; unchanged).
- `claude-md-prose` (v006; unchanged by this pass).
- `basedpyright-vs-pyright` (v012 L14; unchanged).

**Scope-widened in v013:**

- `enforcement-check-scripts` (v005; widened every pass
  since). v013 additions:
  - M6: `check-schema-dataclass-pairing` widened to three-way
    (schema ↔ dataclass ↔ validator); validator existence
    enforcement folded in.
- `static-check-semantics` (v007; widened every pass since).
  v013 additions:
  - M1: `check-assert-never-exhaustiveness` semantics
    updated to require the `typing_extensions` import path
    specifically (a stray `from typing import assert_never`
    fails the check), matching the uniform-import discipline.
  - M4: "up to 3 attempts total" counting semantics in the
    retry discipline section.
  - M5: `check-no-inheritance` semantics tightened to
    direct-parent-only; LivespecError subclasses NOT
    acceptable bases. Removes the v012-era "transitively;
    check examines the base's MRO" phrasing.
  - M6: `check-schema-dataclass-pairing` three-way walker
    semantics (walks validators too).
- `task-runner-and-ci-config` (v006; widened every pass
  since). v013 additions:
  - M1: `typing_extensions` vendored as minimal shim in
    `_vendor/typing_extensions/` (NOT mise-pinned; resolving
    the v012 `typing_extensions` follow-up with license policy
    extended to admit PSF-2.0).
  - M3: `.mutmut-baseline.json` tracked at repo root
    (baseline / ratchet discipline for the mutation-testing
    release-gate).
  - M7: Import-Linter minimum concrete `[tool.importlinter]`
    configuration in `pyproject.toml` per the codified style
    doc example.
  - M8: new release-gate target `just check-no-todo-registry`;
    release-tag CI workflow invokes it alongside
    `just check-mutation`.
- `skill-md-prose-authoring` (v008; widened every pass since).
  v013 additions:
  - M4: retry-on-exit-4 prose phrasing updated to "up to 2
    retries (3 attempts total)".
- `wrapper-input-schemas` (v008; widened in v012 via L4 + L8;
  touched in v013 via M6). v013 additions:
  - M6: the three-way pairing requirement extends to every
    wrapper-input schema — each has a paired validator at
    `validate/<name>.py` in addition to the v012-era
    paired dataclass.
- `front-matter-parser` (v007; widened in v012; touched in
  v013 via M6). v013 additions:
  - M6: `proposed_change_front_matter.schema.json` and
    `revision_front_matter.schema.json` each require a paired
    validator at `validate/proposed_change_front_matter.py`
    and `validate/revision_front_matter.py` respectively.

**New in v013:**

None. All v013 dispositions extend existing deferred entries
or close v012 open follow-ups.

**Removed:**

None. The `typing_extensions` availability follow-up under
`task-runner-and-ci-config` is CLOSED (resolved to vendored
minimal shim per M1 option A''' after mid-lifecycle
correction), but the parent entry remains (it continues to
track other config concerns).

## Self-consistency check

Post-revision invariants rechecked:

- **`typing_extensions` vendored shim + uniform-import.**
  Style doc §"Type safety" records the import rule; style doc
  §"Vendored third-party libraries" documents the shim +
  PSF-2.0 license extension; PROPOSAL.md layout tree lists
  `_vendor/typing_extensions/`; `.vendor.jsonc` records the
  upstream ref; `task-runner-and-ci-config` deferred entry
  notes the closed follow-up; `.mise.toml` does NOT pin
  `typing_extensions` (it's vendored, not dev-only).
- **Heading-coverage registry shape extended.** PROPOSAL.md
  example carries `{spec_file, heading, test}` and (per M8)
  optional `reason`; scenario-header exclusion codified.
- **Heading-coverage lifecycle codified.** `test: "TODO"`
  with `reason` tolerated; `check-no-todo-registry`
  release-gate rejects TODO; livespec-repo-internal (not
  shipped).
- **Mutation testing bootstrap discipline.** Baseline file +
  ratchet comparison + structured mutant output codified in
  style doc; deferred entry records the tracked file.
- **Retry count disambiguated.** All PROPOSAL.md + style doc
  + deferred-items references to "3 retries" converted to
  "up to 2 retries (3 attempts total)" or "3 attempts"
  wording.
- **`check-no-inheritance` direct-parent-only.** Style doc
  rewritten to drop the "or a `LivespecError` subclass"
  phrasing; deferred-items AST semantics rewritten to remove
  "transitively; check examines the base's MRO."
- **Validate/ three-way pairing.** PROPOSAL.md layout tree
  enumerates 8 v1 validators; style doc codifies the
  factory-shape pairing; `check-schema-dataclass-pairing`
  description updated to three-way.
- **Import-Linter minimum example.** Style doc carries a 25-
  line `[tool.importlinter]` TOML example with illustrative
  caveat; the three authoritative English rules remain
  primary.
- **Typo + dev-deps + test-naming + types.py-shadow + scope
  wording + env-var wording.** All C1-C6 edits applied.
- **Recreatability.** A competent implementer can generate
  the v013 livespec plugin + built-in template +
  sub-commands + enforcement suite + dev-tooling from v013
  PROPOSAL.md + `livespec-nlspec-spec.md` + updated
  `python-skill-script-style-requirements.md` + updated
  `deferred-items.md` alone. All cross-document references
  to typing_extensions import-source, heading-coverage
  format + lifecycle, mutation-testing baseline, retry count,
  check-no-inheritance direct-parent rule, validator
  enumeration, and Import-Linter minimum configuration
  reconciled.

## Outstanding follow-ups

Tracked in the updated `deferred-items.md` (see inventory
above). The v013 pass touched 6 existing entries (adding
scope-widenings): `enforcement-check-scripts`,
`static-check-semantics`, `task-runner-and-ci-config`,
`skill-md-prose-authoring`, `wrapper-input-schemas`,
`front-matter-parser`. No new entries were added; no entries
were removed.

The `typing_extensions` availability follow-up under
`task-runner-and-ci-config` is CLOSED (M1 resolution).

## What was rejected

Nothing was rejected outright. Three items moved from
recommended to alternate option during the interview:

- **M4** — moved from "Option A: 3 retries = 3 invocations
  after initial (4 total max)" to user-chosen "Option B: 3
  total attempts (initial + 2 retries)." Tighter and less
  ambiguous; matches the "3 attempts" numeric anchor.
- **M5** — moved from "Option A: accept codified transitive
  AST semantics as authoritative" to user-chosen "Option B:
  tighten AST check to direct-parent-only." Enforces the
  v012 revision-file leaf-closed intent mechanically;
  stronger guardrail.
- **C5** — moved from "Option A: canonicalize on short
  `livespec/**` + explanatory note" to user-chosen
  "Option B: canonicalize on full `.claude-plugin/scripts/
  livespec/**` throughout." Verbose but maximally explicit.

Two items were reshaped mid-interview; one item was
corrected mid-lifecycle (apply phase):

- **M2** — was originally formulated to bundle the format
  question (spec_file field + scenario exclusion) with a
  lifecycle question (when/who/where updates the registry).
  User requested clarification; I split into M2 (format only)
  + M8 (lifecycle, new). Both resolved.
- **M8** — was introduced mid-interview. Initial options
  (A1/A2/B/C) leaked livespec-dev-specific mechanisms into
  the shipped plugin surface (shipped `revise/SKILL.md`,
  shipped doctor-static checks, shipped wrappers). User
  clarified the shipped-vs-not-shipped distinction;
  `heading-coverage.json` is a livespec-repo-internal
  artifact at `<repo-root>/tests/`, not shipped. Options
  were re-framed as livespec-repo-internal mechanisms
  (A2'-repo / C-repo / A1-repo / Withdraw); user chose
  A2'-repo.
- **M1 (correction during apply phase)** — interview
  initially picked Option A ("mise-pin `typing_extensions`
  as a direct dev-only dep"). The assistant caught the
  self-contradiction during the apply phase (mise-pinning
  makes a tool available only to developers at their shell;
  `livespec/**` imports `typing_extensions` at USER runtime
  via the shipped plugin). The user was re-interviewed with
  corrected framing; final disposition is Option A''' (vendor
  a ~15-line shim at `_vendor/typing_extensions/__init__.py`
  keeping the `typing_extensions` module name so pyright's
  `reportImplicitOverride` diagnostic recognizes the import
  path; ships PSF-2.0 LICENSE verbatim; narrow license-policy
  extension admits PSF-2.0). Pyright recognition requirement
  ruled out Option A'' (livespec-authored
  `_typing_compat.py`); size proportionality ruled out
  Option A' (vendor full ~150 KB upstream); pyright
  recognition and the 3.10-floor preservation ruled out
  Option B (bump floor to 3.11).

No item reopened any v001-v012 decision about what livespec
does. The v009 I0 architecture-vs-mechanism discipline, I10
domain-vs-bugs discipline, K4 keyword-only discipline, K5
template-shape decoupling, and v012 L15b user-provided-
extensions-minimal-requirements principle all held throughout
the pass. v013 preserves v012's structural architecture while
closing integration gaps and tightening one self-contradiction
(M5).
