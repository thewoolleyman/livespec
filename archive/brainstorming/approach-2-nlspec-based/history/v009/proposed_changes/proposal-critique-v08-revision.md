---
proposal: proposal-critique-v08.md
decision: modify
revised_at: 2026-04-22T23:00:00Z
reviser_human: thewoolleyman
reviser_llm: Claude Opus 4.7 (1M context)
---

# Revision: proposal-critique-v08

## Provenance

- **Proposed change:** `proposal-critique-v08.md` (in this directory) — a
  recreatability-focused defect critique evaluating v008 PROPOSAL.md +
  `python-skill-script-style-requirements.md` against the embedded
  `livespec-nlspec-spec.md` guidelines.
- **Revised by:** thewoolleyman (human) in dialogue with Claude Opus 4.7
  (1M context).
- **Revised at:** 2026-04-22 (UTC).
- **Scope:** v008 PROPOSAL.md + python style doc + `livespec-nlspec-spec.md`
  + `deferred-items.md` → v009 equivalents. Meta-rule codification
  (architecture-level vs mechanism-level specification), error-handling
  discipline codification (domain errors vs bugs), seed pre-step
  exemption, run_static chain back-off, schema-dataclass pairing,
  supervisor return wording, git-config read allowlist extension,
  Result/IOResult lifting back-off, spec_root parameterization,
  wrapper-internal validation, reserved `livespec-` author prefix,
  `LivespecError` hierarchy clarification, symlink direction,
  front-matter schema split, LLM-id precedence, doctor_static flag
  rejection, and housekeeping (reintroduce `nlspec-spec.md` at
  `<repo-root>/prior-art/`).

## Pass framing

This pass was a **recreatability-focused defect critique** producing
14 items (I1-I14) plus one meta-item (I0) added mid-interview. The
user's mid-interview pushback on I2 ("are we over-specifying against
the spirit of the nlspec guidelines?") triggered the I0 meta-item:
codify the architecture-level-vs-mechanism-level distinction so
future critique/revise passes don't drift into mechanism. A second
mid-interview push on I10 ("unrecoverable bugs should not be handled
via ROP track; only EXPECTED errors — externally caused by user,
environment, system, infra, timing — which can potentially succeed
again") reshaped I10 entirely and widened into a full Error Handling
Discipline subsection grounded in [GitLab Remote Development's
domain-message discipline](https://gitlab.com/gitlab-org/gitlab/-/blob/master/ee/lib/remote_development/README.md#what-types-of-errors-should-be-handled-as-domain-messages).

Each I item carried one of four NLSpec failure modes (ambiguity /
malformation / incompleteness / incorrectness) and was grouped by
impact: major gaps (I1-I3; recreatability-blocking), significant gaps
(I4-I10; load-bearing guesses), smaller cleanup (I11-I14; freeze /
enumerate / rename).

No item reopened any v005-v008 decision about what livespec does. The
pass clarified, integrated, back-offed where mechanism-drift was
found, and codified two cross-cutting principles that shape future
passes.

## Summary of dispositions

| Item | Failure mode | Disposition |
|---|---|---|
| I0 (meta) | N/A | Accept: add Architecture-Level Constraints section + Error Handling Discipline subsection to livespec-nlspec-spec.md; reintroduce `nlspec-spec.md` at `<repo-root>/prior-art/` |
| I1 | malformation | Accepted as recommended (option A — seed exempt from pre-step) |
| I2 | ambiguity | Modified-on-accept: back off (strip ROP chain illustration; state behavior only) |
| I3 | incompleteness | Accepted as recommended (option A — hand-author dataclasses + check-schema-dataclass-pairing) |
| I4 | malformation | Accepted as recommended (option A — boundary-based supervisor exception) |
| I5 | malformation | Accepted as recommended (option A — extend git-read allowlist) |
| I6 | incorrectness | Modified-on-accept: back off (strip bind_result lifting example) |
| I7 | ambiguity | Accepted as recommended (option A — template-aware spec_root) |
| I8 | incompleteness | Accepted as recommended (option B — fold validation into main wrapper) |
| I9 | ambiguity | Accepted as recommended (option A — reserved `livespec-` prefix namespace) |
| I10 | incompleteness | Modified-on-accept (option A reshaped — full domain-vs-bugs discipline; retire `DoctorInternalError`; @impure_safe targeted; supervisor bug-catcher; assert first-class) |
| I11 | ambiguity | Accepted as recommended (option A — `.claude/skills/ → ../.claude-plugin/skills/`) |
| I12 | ambiguity | Accepted as recommended (option A — split into two front-matter schemas) |
| I13 | incompleteness | Modified-on-accept: combined A+B with precedence (env var → LLM payload best-effort → `unknown-llm`) |
| I14 | ambiguity | Accepted as recommended (option A — reject with UsageError) |

## Governing principles established or reinforced during this pass

Two cross-cutting principles were codified into `livespec-nlspec-spec.md`
as durable discipline, self-propagating to every future critique pass
(the doc is injected as reference context before every template-prompt
invocation).

### Architecture-level vs mechanism-level specification

Architecture-constrained specs (where code-quality / agent-generation
guardrails are first-class) MAY extend into implementation architecture
— BUT only at the architecture level. The carve-out names what's in
scope (language deps, code-quality tooling, type-level guarantees at
the public-API layer, structural boundaries enforced by checks,
externally-visible architectural invariants, directory layouts the
enforcement suite inspects) and what stays OUT of scope even in such
specs (internal composition details, illustrative code presented as
normative, private-function signatures, mechanism where an enforcement
check already binds it).

The test: *could this sentence be deleted without losing the
guardrail?* If an AST/type/style check already enforces the same
discipline, the sentence is redundant.

Applied this pass to I2 and I6: both treated internal Python ROP
composition as normative. Back-off dispositions remove the illustrative
chains from the style doc and replace with behavioral prose. The
enforcement suite (`check-public-api-result-typed`, `check-purity`,
`check-no-raise-outside-io`, etc.) carries the actual guardrail work.

### Domain errors vs bugs (error-handling discipline)

Unrecoverable bugs / coding errors MUST NOT flow through the Result /
IOResult track. Only EXPECTED errors (externally caused by user,
environment, system, infrastructure, or timing — where retry or fix
could succeed) are domain errors and thus Result-track citizens. Bugs
propagate as raised exceptions until the outermost supervisor logs
them and emits the bug-class exit code.

Concrete implications:

- `@impure_safe` / `@safe` wraps specific expected exception types
  only, never blanket-catch.
- `check-no-raise-outside-io` narrows to "no raising of
  `LivespecError` subclasses outside `io/**` and `errors.py`";
  raising bug-class exceptions is permitted anywhere.
- Supervisors in `commands/<cmd>.py` and `bin/doctor_static.py` gain
  a top-level `try/except Exception` bug-catcher (logs via structlog
  with traceback, exit 1). This is the ONLY permitted catch-all.
- `assert` statements are permitted and encouraged.
- `LivespecError` hierarchy is strictly expected-failure types;
  `DoctorInternalError` retired (a "bug" subclass on the domain
  hierarchy is a category confusion).

Inspired by GitLab Remote Development's domain-message discipline.

## Disposition by item

### I0. Meta-rule: architecture-level vs mechanism-level; reintroduce nlspec-spec.md (new mid-interview)

User surfaced mid-I2 interview: "we said we wanted to define the
shape of the contracts, but this seems like we are over specifying
and going against the spirit of our nlspec guidelines."

Resolution:

- New top-level section added to `livespec-nlspec-spec.md` positioned
  between §"Spec Economy" and §"Intentional vs. Accidental Ambiguity":
  **"Architecture-Level Constraints (Implementation Discipline)"**.
  Section codifies what is in scope (language deps, tooling, type-
  level public-API guarantees, structural boundaries enforced by
  checks, externally-visible invariants, inspected directory
  layouts) and what stays out of scope (internal composition,
  illustrative code as normative, non-public function signatures,
  redundancy with enforcement suite).
- A nested subsection **"Error Handling Discipline"** codifies the
  domain-vs-bugs rule (established during I10 interview).
- Propagation: `livespec-nlspec-spec.md` is injected as reference
  context before every template-prompt invocation per PROPOSAL.md
  §"NLSpec conformance." Future critique passes automatically see
  this discipline.

Housekeeping also completed this turn:

- Created `<repo-root>/prior-art/` directory.
- Moved `brainstorming/approach-2-nlspec-based/nlspec-spec.md` →
  `<repo-root>/prior-art/nlspec-spec.md` (via `git mv`).
- Replaced the first-line "NOTE: Prior art copied from from <URL>"
  with proper HTML-comment permalink + diffing-intent line.
- Updated `livespec-nlspec-spec.md` header to reference the
  relocated path.
- Updated `brainstorming/approach-2-nlspec-based/prior-art.md`
  entry #1 to cite the local verbatim copy for diffing.
- Updated `brainstorming/approach-2-nlspec-based/critique-interview-prompt.md`
  required-reading path to the new location.

### I1. Seed pre-step contradicts seed's purpose (malformation → accepted, option A)

Pre-step doctor static's `template-files-present` and
`proposed-changes-and-history-dirs` fail on a green-field repo where
seed has yet to create the files. The lifecycle invariant and seed's
creation-from-empty contract contradicted.

Resolution: seed is **exempt from pre-step doctor static**. Seed's
ROP chain is `seed_run(ctx) |> bind(run_static)` (post-step only).
PROPOSAL.md §"Sub-command lifecycle orchestration" adds seed to the
pre-step exemption list alongside `help` and `doctor`. The
`static-check-semantics` deferred item covers the exemption rationale
and any edge cases (e.g., seed invoked on a partially-seeded repo —
idempotency refusal still fires).

### I2. run_static return type in lifecycle chain (ambiguity → modified-on-accept: back off)

Per I0's Architecture-Level Constraints discipline, specifying the
internal ROP composition type for the wrapper chain is mechanism, not
architecture. The two-implementer test: independent implementations
picking different internal composition strategies produce identical
observable behavior.

Resolution (back-off):

- Style doc §"Railway-Oriented Programming" strips the illustrative
  `flow(ctx, run_static, bind(cmd_run), bind(run_static))` example
  AND the `run_static(ctx) -> IOResult[FindingsReport, ...]` specific
  return annotation.
- Replace with behavioral prose: "The wrapper runs pre-step doctor
  static, sub-command logic, and post-step doctor static in that
  order. On any `status: fail` finding from pre-step, the wrapper
  aborts with exit 3 and sub-command logic does not run. On any
  `status: fail` finding from post-step, the wrapper aborts with
  exit 3 after sub-command logic has already mutated state; the
  user is instructed to commit the partial state and proceed.
  `bin/doctor_static.py` emits `{findings: [...]}` to stdout per its
  documented contract. Other sub-command wrappers emit findings to
  stderr via structlog. Python composition mechanism is implementer
  choice under the architecture-level constraints (public functions
  return `Result` or `IOResult`; purity-by-directory; ROP via
  `dry-python/returns`)."
- Style doc §"Sub-command lifecycle composition" simplifies to
  behavioral language.
- PROPOSAL.md §"Sub-command lifecycle orchestration" mirrors.

### I3. Schema → dataclass generation unspecified (incompleteness → accepted, option A)

`LivespecConfig`, `SeedInput`, `ProposalFindings`, `ReviseInput` are
referenced as "dataclasses generated from schemas" with no defined
generation path.

Resolution:

- Hand-author each dataclass at `scripts/livespec/schemas/dataclasses/
  <name>.py`; `scripts/livespec/schemas/__init__.py` re-exports every
  dataclass.
- Add new enforcement check `check-schema-dataclass-pairing`: for
  every `schemas/*.schema.json`, assert a paired dataclass with the
  `$id`-derived name and every listed field (type-matched). And vice
  versa. Drift in either direction fails the check.
- Add the check to the canonical `just` target list in
  `python-skill-script-style-requirements.md`.
- Widen the `wrapper-input-schemas` deferred item to also cover
  paired dataclass authorship (alternative: new entry
  `dataclass-schema-pairing` — one-item granularity preferred).

### I4. Supervisor return rule self-contradictory (malformation → accepted, option A)

"Every public function MUST return `Result[_,_]` or `IOResult[_,_]`
unless it returns `None` for a deliberate side-effect boundary (e.g.,
`main() -> int` supervisors in `commands/*.py`)" says `None` but cites
`int`.

Resolution: rewrite the style doc §"Type safety" rule as boundary-
based, not return-type-based:

> Every public function's return annotation MUST be `Result[_, _]` or
> `IOResult[_, _]`, UNLESS the function is a supervisor at a
> deliberate side-effect boundary (e.g., `main() -> int` in
> `commands/*.py` and `bin/doctor_static.py`, or a function returning
> `None`). The rule exempts only such supervisors.

`static-check-semantics` deferred item covers `check-public-api-
result-typed`'s precise AST exemption scope (functions named `main`
in `commands/**.py` and `doctor/run_static.py`).

### I5. git config read outside documented allowlist (malformation → accepted, option A)

Revision front-matter and seed auto-capture require reading
`git config user.name` / `user.email`, but PROPOSAL.md §"Git"
allowlist names only the out-of-band-edits check as a git reader.

Resolution:

- PROPOSAL.md §"Git" extends the documented git-reader list: (1)
  `doctor-out-of-band-edits` check (unchanged), (2) `revise` and
  `seed` wrappers for author-identity capture via `git config
  user.name` / `git config user.email`.
- New function `livespec.io.git.get_git_user()` returning
  `IOResult[str, GitUnavailableError]` (success = `"<name>
  <email>"` or fallback literal `"unknown"`; failure only on
  unexpected git-binary absence).
- `static-check-semantics` deferred item covers the exact
  fallback behavior on missing config or unset values (always
  returns "unknown" literal; never raises; domain error not bug).

### I6. Result / IOResult lifting in ROP chains (incorrectness → modified-on-accept: back off)

Same category as I2: the specific lifter choice is mechanism. Under
`dry-python/returns`, mixing `Result`-returning pure functions and
`IOResult`-returning impure functions requires `bind_result` or
equivalent lifting — but the style doc's illustration used plain
`bind` and wouldn't type-check verbatim.

Resolution (back-off):

- Strip the `read_file / bind(parse_jsonc) / bind(validate_config)`
  mixed-monad example from style doc §"Railway-Oriented Programming."
- Replace with behavioral prose: "Composing `Result`-returning pure
  functions inside `IOResult` chains requires appropriate lifting per
  `dry-python/returns` (e.g., `bind_result`, `IOResult.from_result`,
  or equivalent). The specific lifter is implementer choice. Pyright
  strict and the `check-public-api-result-typed` check are the
  guardrails that catch mis-composition."
- `returns-pyright-plugin-disposition` deferred item continues to
  cover whether the returns pyright plugin is vendored (and whether
  it gives usable diagnostics for mis-lifting).

### I7. SPECIFICATION/ path vs custom-template root freedom (ambiguity → accepted, option A)

Doctor-static checks hard-code `SPECIFICATION/` literal; templates
MAY place spec files at repo root or any subdirectory per PROPOSAL.md
§"Templates."

Resolution:

- `template.json` gains an optional field `spec_root: string` (default
  `"SPECIFICATION/"`). PROPOSAL.md §"Templates → template directory
  layout" documents it.
- `DoctorContext.spec_root: Path` added to the context dataclass in
  the style doc.
- Every check's description in PROPOSAL.md §"Static-phase checks"
  changes hard-coded `SPECIFICATION/` to `<spec-root>/` parameterized
  from the resolved `DoctorContext.spec_root`. This covers
  `proposed-changes-and-history-dirs`, `version-directories-
  complete`, `version-contiguity`, `out-of-band-edits`,
  `anchor-reference-resolution`, and the cross-file reference rule in
  §"Template-agnostic principles."
- `gherkin-blank-line-format` remains conditional on the active
  template being `livespec` (unchanged).
- `static-check-semantics` deferred item covers exact path-
  parameterization semantics and edge cases (e.g., spec_root = "./"
  for repo-root templates).

### I8. LLM → validator invocation protocol (incompleteness → accepted, option B)

PROPOSAL.md's SKILL.md body shape named
`livespec.validate.<name>.validate` as the LLM-side validation entry
point, but the LLM invokes Python only via Bash; no CLI shape was
specified.

Resolution (fold validation into wrapper):

- Each sub-command wrapper (`bin/propose_change.py`,
  `bin/seed.py`, `bin/critique.py`, `bin/revise.py`) validates its
  input JSON internally using the factory-shape validator from
  `livespec/validate/<name>/`. On validation failure, the wrapper
  exits 3 with findings on stderr via structlog.
- SKILL.md prose per sub-command: on wrapper exit 3 with a
  validation-class finding, re-invoke the template prompt with the
  error context and retry, up to 3 retries (matches PROPOSAL.md's
  existing 3-retry rule).
- PROPOSAL.md §"Per-sub-command SKILL.md body structure" step shape
  "Validate output against a schema" becomes "Re-invoke on wrapper
  exit 3 with validation-class findings (up to 3 retries)." No
  separate validator CLI wrappers.
- PROPOSAL.md §"propose-change" / §"seed" / §"critique" / §"revise":
  drop phrases like "the LLM validates this against the schema via
  `livespec.validate.<name>.validate`" in favor of "the wrapper
  validates internally."
- `skill-md-prose-authoring` deferred item covers the retry prose per
  sub-command; `wrapper-input-schemas` covers the validation-error
  finding shape.

### I9. reviser_llm / author identity semantics (ambiguity → accepted, option A)

`reviser_llm` defined as model ID but populated as `livespec-seed` /
`livespec-doctor` for auto-capture; `author` similarly dual-purpose.

Resolution:

- Reserved `livespec-` prefix namespace for automated skill-tool
  authorship. Identifiers starting with `livespec-` (e.g.,
  `livespec-seed`, `livespec-doctor`) are reserved; non-`livespec-`-
  prefixed identifiers are human or LLM.
- PROPOSAL.md §"Proposed-change file format" and §"Revision file
  format" state the namespace convention explicitly.
- `front_matter.schema.json` (now split per I12) pattern-validates
  the namespace reservation where applicable.
- `front-matter-parser` deferred item picks up the pattern-based
  prefix check.

### I10. Domain-vs-bugs error-handling discipline (incompleteness → modified-on-accept)

User push: "Unrecoverable bugs or coding / syntax errors should not
be handled via ROP track. Only errors which are EXPECTED (externally
caused by user, environment, system, infra, timing) and thus can be
potentially successful again should be ROP errors."

Resolution (full discipline codification):

- New subsection **"Error Handling Discipline"** added under the new
  "Architecture-Level Constraints" section in `livespec-nlspec-spec.md`
  (I0). Grounded in the GitLab Remote Development domain-message
  discipline.
- `DoctorInternalError` **retired**. Doctor static check signatures
  become `run(ctx) -> IOResult[Finding, DomainError]` where
  `DomainError` is the expected-failure branch of `LivespecError`.
  A bug inside a check propagates as a raised exception; the
  supervisor's top-level `try/except Exception` catches it, logs
  via structlog with traceback, and emits exit 1.
- `@impure_safe` / `@safe` usage changes from blanket-catch to
  **targeted-catch**. Every use MUST enumerate the specific
  expected exception types, e.g.,
  `@safe(exceptions=(FileNotFoundError, PermissionError))`. Style
  doc §"Railway-Oriented Programming" updated.
- `check-no-raise-outside-io` **narrows**: "no raising of
  `LivespecError` subclasses outside `io/**` and `errors.py`";
  raising bug-class exceptions (`TypeError`, `NotImplementedError`,
  `AssertionError`, `RuntimeError` for unreachable branches, etc.)
  is permitted anywhere.
- `check-no-except-outside-io` mirrors the narrowing.
- **Supervisor discipline gains a bug-catcher.** Every supervisor
  (`main()` in `commands/<cmd>.py`, `bin/doctor_static.py`'s
  `main()`) MUST wrap its ROP chain body in one
  `try/except Exception` that logs via structlog and returns the
  bug-class exit code (1). This is the ONLY catch-all permitted in
  the codebase. `check-supervisor-discipline` enforces.
- **`assert` is first-class.** Style doc documents that `assert`
  statements for invariants are permitted and encouraged; an
  `AssertionError` is a bug (propagates to the supervisor).
- `LivespecError` hierarchy is strictly expected-failure types:
  `UsageError`, `PreconditionError`, `ValidationError`,
  `GitUnavailableError`, `PermissionDeniedError`, `ToolMissingError`.
  No `DoctorInternalError`. Style doc §"Exit code contract" hierarchy
  block updated with prose noting the domain-error-only scope.
- `static-check-semantics` deferred item widens to cover the exact
  AST semantics of the narrowed `check-no-raise-outside-io`,
  `check-no-except-outside-io`, and `check-supervisor-discipline`
  (supervisor bug-catcher exemption).

### I11. Dogfood symlink direction (ambiguity → accepted, option A)

Resolution: PROPOSAL.md §"Plugin delivery" specifies: **`.claude/
skills/`** is a relative symlink pointing at **`../.claude-plugin/
skills/`**. The plugin-delivery directory is canonical; Claude Code
consumption flows through the symlink. `just bootstrap` creates the
symlink idempotently if missing.

### I12. front_matter schema single-vs-plural (ambiguity → accepted, option A)

Resolution: split into two schemas:

- `proposed_change_front_matter.schema.json` — `topic`, `author`,
  `created_at`.
- `revision_front_matter.schema.json` — `proposal`, `decision`,
  `revised_at`, `reviser_human`, `reviser_llm`.

PROPOSAL.md layout tree in §"Skill layout" and style doc §"Package
layout" updated. PROPOSAL.md §"Proposed-change file format" and
§"Revision file format" name their respective schemas.
`front-matter-parser` deferred item updated to cover both schemas +
the reserved-prefix pattern from I9.

### I13. Host-provided LLM id mechanism (incompleteness → modified-on-accept: combined A+B with precedence)

Resolution: precedence-based resolution:

1. If env var `LIVESPEC_REVISER_LLM` is set and non-empty, use its
   value.
2. Otherwise, the template prompt instructs the LLM to do
   best-effort self-identification and emit a `reviser_llm` field
   in the JSON wrapper-input payload. If present and non-empty,
   use it.
3. Otherwise, use the literal `"unknown-llm"`.

Wrapper logic: `reviser_llm = env["LIVESPEC_REVISER_LLM"] or
payload.get("reviser_llm") or "unknown-llm"`.

PROPOSAL.md §"Configuration: `.livespec.jsonc`" adds an "Environment
variables" subsection documenting `LIVESPEC_REVISER_LLM` with
default "(unset → LLM self-declaration → `unknown-llm`)". The
critique and revise template prompts instruct the LLM to populate
`reviser_llm` with its model identifier or `unknown-llm` as fallback
(`template-prompt-authoring` deferred item picks this up).

### I14. doctor_static vs --skip-pre-check (ambiguity → accepted, option A)

Resolution: `bin/doctor_static.py`'s argparse does NOT accept
`--skip-pre-check`; passing it produces a usage error (exit 2 via
`IOFailure(UsageError)`). PROPOSAL.md §"Sub-command lifecycle
orchestration" adds an explicit sentence: "`bin/doctor_static.py`
does not accept `--skip-pre-check`; it IS the static phase and has
no pre/post wrap." Canonical SKILL.md body failure-handling section
includes exit 2 narration.

## Deferred-items inventory (carried forward + new + scope-widened)

Per the deferred-items discipline, every carried-forward item is
enumerated below. Additions, scope-widenings, and renames are
flagged.

**Carried forward unchanged from v008:**

- `template-prompt-authoring` (v001).
- `python-style-doc-into-constraints` (v005).
- `companion-docs-mapping` (v001).
- `enforcement-check-scripts` (v005).
- `claude-md-prose` (v006).
- `task-runner-and-ci-config` (v006).
- `returns-pyright-plugin-disposition` (v007).
- `skill-md-prose-authoring` (v008).

**Scope-widened in v009:**

- `static-check-semantics` (v007; renamed v008 from
  `ast-check-semantics`; widened again in v009). Added scope:
  seed pre-step exemption semantics (I1), supervisor-`main()`
  scope in `check-public-api-result-typed` (I4), git-config
  fallback behavior in `io/git.py` (I5), spec_root path-
  parameterization for every check (I7), narrowed
  `check-no-raise-outside-io` / `check-no-except-outside-io` AST
  semantics distinguishing domain-error from bug-class exceptions
  (I10), supervisor bug-catcher exemption in
  `check-supervisor-discipline` (I10), and
  `check-schema-dataclass-pairing` AST semantics (I3).
- `front-matter-parser` (v007). Scope widened to cover two
  front-matter schemas (I12: `proposed_change_front_matter.schema.
  json` + `revision_front_matter.schema.json`) AND the reserved
  `livespec-` prefix pattern-check (I9).
- `wrapper-input-schemas` (v008). Scope widened to also cover
  the paired hand-authored dataclasses per I3
  (`LivespecConfig`, `SeedInput`, `ProposalFindings`,
  `ReviseInput`) and their paths under
  `scripts/livespec/schemas/dataclasses/`.
- `task-runner-and-ci-config` (v006). Scope picks up
  `check-schema-dataclass-pairing` and the narrowed
  `check-no-raise-outside-io` / `check-no-except-outside-io`
  targets.

**New in v009:**

None beyond the above scope widenings.

**Removed:**

None.

## Self-consistency check

Post-revision invariants rechecked:

- **Architecture-level constraint discipline self-propagates.**
  `livespec-nlspec-spec.md` §"Architecture-Level Constraints"
  is injected as reference context before every template-prompt
  invocation per PROPOSAL.md §"NLSpec conformance." Future
  critique passes automatically have this discipline in context.
- **Error-handling discipline is load-bearing.** Retires
  `DoctorInternalError`, narrows AST checks, adds supervisor
  bug-catcher. All references to `DoctorInternalError` in
  PROPOSAL.md and the style doc were rewritten to `DomainError`
  or dropped.
- **Seed lifecycle consistent.** Seed chain reduces to
  `seed_run(ctx) |> bind(run_static)`; first-ever invocation
  works on a green-field repo.
- **git-read allowlist explicit.** Two documented readers:
  `doctor-out-of-band-edits` (unchanged) and `revise`/`seed`
  auto-capture (new).
- **Template flexibility preserved.** `spec_root` parameterizes
  the spec-root path per template; `livespec` default remains
  `"SPECIFICATION/"`.
- **LLM-side validation simplified.** No separate validator CLI
  wrappers; wrapper exit 3 + SKILL.md retry prose is the loop.
- **Author-identity namespace reserved.** `livespec-` prefix
  unambiguous.
- **LivespecError hierarchy clean.** Expected-failure-only
  subclasses; bugs propagate as raised exceptions.
- **Symlink direction specified.** `.claude/skills/ →
  ../.claude-plugin/skills/`.
- **Front-matter schemas split.** Two distinct files; sum-type
  fidelity.
- **LLM id precedence codified.** Env var → LLM payload
  best-effort → `unknown-llm`.
- **doctor_static flag discipline explicit.** `--skip-pre-check`
  rejected with exit 2.
- **Housekeeping landed.** `nlspec-spec.md` lives at
  `<repo-root>/prior-art/` with permalink header; cross-references
  in `livespec-nlspec-spec.md`, `prior-art.md`,
  `critique-interview-prompt.md` updated.
- **Recreatability.** A competent implementer can generate the
  v009 livespec plugin + built-in template + sub-commands +
  enforcement suite + dev-tooling from v009 PROPOSAL.md +
  `livespec-nlspec-spec.md` + updated
  `python-skill-script-style-requirements.md` + `deferred-items.md`
  alone. Pre-step lifecycle for seed works green-field; wrapper
  inputs are schema-validated internally; domain errors are
  Result-track; bugs raise to supervisor; mechanism is
  implementer choice within the architectural guardrails.
- **Cross-doc consistency.** PROPOSAL.md, Python style doc, and
  `livespec-nlspec-spec.md` agree on: the architecture-vs-
  mechanism rule, the domain-vs-bugs error discipline, seed
  exemption, spec_root, git-read allowlist, wrapper-internal
  validation, reserved prefix namespace, symlink direction,
  split front-matter schemas, LLM id precedence, dataclass
  pairing, updated AST check scopes.

## Outstanding follow-ups

Tracked in the updated `deferred-items.md` (see inventory above).

## What was rejected

Nothing was rejected outright. Two reshape patterns occurred during
the interview:

- **Over-specification flagged by user → back-off disposition:**
  - I2 (run_static return type in wrapper chain) — user flagged
    "going against the spirit of our nlspec guidelines." Resolved
    to back-off disposition AND meta-item I0 codifying the
    architecture-vs-mechanism rule in `livespec-nlspec-spec.md` to
    prevent future drift.
  - I6 (bind_result lifting example) — same category; resolved
    to same back-off disposition under I0's discipline.

- **Mechanism-level framing reshaped into discipline principle:**
  - I10 (DoctorInternalError undefined) — user push:
    "Unrecoverable bugs or coding / syntax errors should not be
    handled via ROP track." Reshaped from "add type to hierarchy"
    to "retire type; codify full domain-vs-bugs discipline;
    narrow AST checks; add supervisor bug-catcher; assert
    first-class." Grounded in GitLab's domain-message discipline.

No pattern of "pulling endless threads" occurred; the user's
mid-interview convergence check confirmed v009 is 1-2 passes from
seed-ready.
