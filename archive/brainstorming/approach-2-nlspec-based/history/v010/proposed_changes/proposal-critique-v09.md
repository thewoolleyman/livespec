---
topic: proposal-critique-v09
author: Claude Opus 4.7 (1M context)
created_at: 2026-04-22T21:30:00Z
---

# Critique scope

This critique evaluates **v009 PROPOSAL.md** plus its companions
`python-skill-script-style-requirements.md` and the embedded
`livespec-nlspec-spec.md` guidelines (including v009's new
"Architecture-Level Constraints" section and "Error Handling
Discipline" subsection). Primary focus: the **recreatability test**
over v009 — given only PROPOSAL.md, the Python style doc,
`livespec-nlspec-spec.md`, `deferred-items.md`, and the four
companion brainstorming docs, can a competent implementer produce
a working v009 livespec plugin?

The v009 revision (`history/v009/proposed_changes/
proposal-critique-v08-revision.md`) locked in 14 item dispositions
(I1-I14) plus one meta-item (I0) covering architecture-vs-mechanism
discipline codification, domain-errors-vs-bugs error-handling
discipline grounded in GitLab Remote Development's domain-message
pattern, seed pre-step exemption, ROP-composition back-off for
illustrative chains, schema-dataclass pairing, supervisor return-
rule boundary-based exemption, git-config read allowlist extension,
spec_root parameterization, wrapper-internal validation, reserved
`livespec-` author prefix, `LivespecError` hierarchy cleanup,
front-matter schema split, LLM-id precedence, and
`doctor_static.py` `--skip-pre-check` rejection. This critique
does **not** reopen any of those decisions.

The recreatability test over v009 surfaces gaps in five clusters:

1. **Stale residual references to v009-retired mechanism and
   types.** The v009 revision retired `DoctorInternalError` (I10)
   and backed off from naming `Fold.collect` as the composition
   primitive (I2/I6), but multiple sections of PROPOSAL.md and the
   style doc still reference both. These are the cleanest internal
   contradictions in v009.
2. **`io/git.get_git_user()` domain-fallback vs domain-error
   disposition disagreement between PROPOSAL.md and
   deferred-items.md.** The revision (I5) said git-binary absence
   is `IOFailure(GitUnavailableError)` (exit 3); PROPOSAL.md as
   written says it falls back to `IOSuccess("unknown")`. Two
   separate fallback semantics for the same function.
3. **Custom-template prompt-path resolvability from SKILL.md.**
   Per-sub-command SKILL.md prose uses literal `@`-reference
   paths to the built-in template's `prompts/` directory; no
   mechanism is specified for reaching a custom template's
   prompts when `.livespec.jsonc`'s `template` field names an
   arbitrary user-provided path. Since custom templates are in
   v1 scope (PROPOSAL.md §"Custom templates are in v1 scope"),
   this blocks recreatability of the `seed` / `propose-change` /
   `critique` / `revise` LLM flows against a custom template.
4. **LLM retry semantics on wrapper exit 3 cannot distinguish
   validation-class findings from doctor-static-class findings.**
   The `Retry-on-exit-3` SKILL.md step retries the template
   prompt only "with validation-class findings" — but exit 3 is
   emitted by validation failures, pre-step doctor static, post-
   step doctor static, and other precondition errors. No
   structured distinguishing field exists in the findings
   emitted on stderr.
5. **Integration gaps where a v009 decision updated document A
   but not every downstream consumer.** `build_parser()` in
   `commands/<cmd>.py` violates `check-public-api-result-typed`
   as narrowed by I4. `author` field in propose-change
   front-matter has no precedence rule analogous to I13's
   `reviser_llm`. `--help` handling reroutes through the railway
   as a `UsageError` → exit 2 under I4's CLI seam disposition,
   conflating help-request with usage-error. `bin/*.py` wrapper
   coverage scope is silent in the 100% line+branch mandate.
   `.vendor.toml` "or per-lib VERSION files" holdover from
   pre-v007 still appears. Symlink git-tracking disposition
   unspecified.

Items are labelled `J1`–`J14` (the `J` prefix distinguishes
"v009 gap" findings from prior critiques' `G`- (v007), `H`-
(v008), and `I`- (v009) items). Each item carries one of the
four NLSpec failure modes:

- **ambiguity** — admits multiple incompatible interpretations.
- **malformation** — self-contradiction within or across
  documents.
- **incompleteness** — missing information needed to act.
- **incorrectness** — internally consistent but specifies
  behavior that cannot work as written or contradicts an
  established external convention.

Major gaps appear first (block recreatability outright), then
significant gaps (force load-bearing guesses or produce wrong
behavior), then smaller cleanup.

---

## Major gaps

These items would block a competent implementer from producing a
working v009 livespec without filing additional propose-changes,
because a downstream document still references a v009-retired
concept, a v009 disposition is missing its downstream update, or
a mandated flow has no defined mechanism.

---

## Proposal: J1-doctor-internal-error-and-fold-collect-residuals

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**malformation** (internal contradiction across v009 documents;
retired v008-era class and mechanism-level primitive still named
in the doctor static-phase module contract and orchestrator
description, while the revision text and the errors.py hierarchy
block both say they are retired).

### Summary

The v009 revision explicitly retired `DoctorInternalError` (I10
disposition: "`DoctorInternalError` **retired**. Doctor static
check signatures become `run(ctx) -> IOResult[Finding,
DomainError]` where `DomainError` is the expected-failure branch
of `LivespecError`.") and backed off from naming `Fold.collect`
as normative composition mechanism (I2/I6 disposition:
"implementer choice under the architecture-level constraints").
But both names still appear in PROPOSAL.md §"Static-phase
structure" and the style doc §"Package layout," producing an
internal self-contradiction with PROPOSAL.md's Definition of Done
and the errors.py hierarchy definition.

### Motivation

**PROPOSAL.md line 1284** (Static-phase structure, per-check
signature):

> - Exports `run(ctx: DoctorContext) -> IOResult[Finding,
>   DoctorInternalError]`.

**PROPOSAL.md line 1303** (run_static.py orchestrator
composition):

> - Composes all check results via `Fold.collect` from
>   dry-python/returns into one `IOResult[FindingsReport,
>   DoctorInternalError]`.

**PROPOSAL.md line 1928** (Definition of Done #6):

> orchestrated by `scripts/livespec/doctor/run_static.py` via a
> single ROP chain (`Fold.collect`)

**python-skill-script-style-requirements.md line ~254** (per
sub-package conventions, static check module contract):

> **`doctor/static/<check>.py`** — one module per static check.
> Exports `SLUG` constant and `run(ctx) -> IOResult[Finding,
> DoctorInternalError]`.

Both documents' later sections already reflect v009's retirement:

**style doc line 871** (Exit code contract → doctor static
signatures):

> `IOFailure(err)` payloads are `LivespecError` subclasses.
> Doctor static check signatures are `run(ctx) -> IOResult[Finding,
> E]` where `E` is any `LivespecError` subclass (NOT the retired
> `DoctorInternalError` from prior revisions; bugs in a check
> propagate as raised exceptions to the supervisor's bug-catcher
> and result in exit `1`).

**style doc line ~420** (Railway-Oriented Programming):

> The specific primitives chosen to compose a given chain are
> **implementer choice** under the architecture-level constraints.

Both primary references violate both v009 dispositions at once.
A recreator reading top-to-bottom will author `run(ctx) ->
IOResult[Finding, DoctorInternalError]` following PROPOSAL.md,
then get blocked by `check-no-raise-outside-io` when they try to
import the name from a retired hierarchy. And they'll hard-code
`Fold.collect` as mandatory when the architecture-level
constraint is only "single ROP chain" — leaving a competent
implementer unable to pick any alternative composition primitive
(e.g., a recursive fold, a `reduce(bind, checks, base)` chain)
even though the enforcement suite would accept it.

### Proposed Changes

Harmonize every reference with the v009 revision intent:

- **A. Rewrite both residuals to match v009 I2/I6/I10.**
  - PROPOSAL.md line 1284: change
    `IOResult[Finding, DoctorInternalError]` →
    `IOResult[Finding, DomainError]`, where `DomainError` is
    shorthand for "any `LivespecError` subclass" per the style
    doc. Match the style doc line 871 wording.
  - PROPOSAL.md line 1303: strip the `Fold.collect` naming.
    Replace with behavioral prose: "Composes all check results
    into one `IOResult[FindingsReport, LivespecError]` via the
    composition primitives from `dry-python/returns` — the
    specific primitive is implementer choice under the
    architecture-level constraints (per
    `livespec-nlspec-spec.md` §'Architecture-Level
    Constraints')."
  - PROPOSAL.md line 1928 (DoD #6): drop the parenthetical
    `(Fold.collect)`. Keep "a single ROP chain" as the
    architectural contract.
  - Style doc line ~254: change
    `IOResult[Finding, DoctorInternalError]` → `IOResult[Finding,
    E]` matching the Exit code contract block; cross-reference
    the Exit code contract section.

- **B. Rewrite only PROPOSAL.md; leave the style doc as is.**
  Bet that the style doc's Exit code contract block will be read
  by any recreator and override the package-layout block. Risk:
  the style doc's internal contradiction remains; implementers
  reading top-to-bottom hit the contradiction before reaching
  the clarifying block.

- **C. Rewrite only the style doc; leave PROPOSAL.md as is.**
  Bet that PROPOSAL.md's Fold.collect is acceptable as a
  reference implementation of "a single ROP chain." Risk: I2/I6
  explicitly backed off from mechanism-naming; re-permitting
  Fold.collect reopens the discipline.

Recommended: **A**. This is a clean sweep rewrite; both
references are obvious v009-implementer-pass oversights; fixing
them costs two-sentence edits. The architecture-vs-mechanism
discipline from I0 + the domain-vs-bugs discipline from I10
don't just bind future critique passes — they bind the v009
documents themselves.

---

## Proposal: J2-git-get-git-user-fallback-semantics-disagreement

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**malformation** (cross-document contradiction on the fallback
semantics of `livespec.io.git.get_git_user()`; PROPOSAL.md's
description and deferred-items' `static-check-semantics` entry
disagree on when the function returns success vs failure).

### Summary

PROPOSAL.md §"Git" and `deferred-items.md`'s
`static-check-semantics` entry (both written in v009) define
mutually incompatible behaviors for `io/git.get_git_user()`
when the git binary is absent. PROPOSAL.md says
`IOSuccess("unknown")` (domain fallback, not failure);
deferred-items says `IOFailure(GitUnavailableError)` (domain
error, exit 3). Both are authored as if final.

### Motivation

**PROPOSAL.md lines 373-381** (Git section):

> 2. The `revise` and `seed` wrappers, which read
>    `git config --get user.name` and `git config --get user.email`
>    to populate `reviser_human` on auto-captured revisions.
>    Implemented as `livespec.io.git.get_git_user() ->
>    IOResult[str, GitUnavailableError]`. The function returns
>    `IOSuccess("<name> <email>")` on success, `IOSuccess("unknown")`
>    when either config value is unset **or git is unavailable
>    (domain fallback, not failure)**, and `IOFailure(...)` only
>    on unexpected errors.

**deferred-items.md lines 212-218**:

> **`io/git.get_git_user()` semantics** (v009 I5):
> fallback behavior on missing git binary, missing config,
> unset `user.name` or `user.email`; always returns
> success with literal `"unknown"` rather than failure for
> the missing-config case; **failure only on unexpected
> `git`-binary absence (domain error `GitUnavailableError`,
> exit 3)**.

**v009 revision file lines 275-281** (I5 disposition):

> - New function `livespec.io.git.get_git_user()` returning
>   `IOResult[str, GitUnavailableError]` (success = `"<name>
>   <email>"` or fallback literal `"unknown"`; **failure only on
>   unexpected git-binary absence (domain error
>   `GitUnavailableError`, exit 3)**).

So the revision and deferred-items agree: git-binary absence =
`IOFailure(GitUnavailableError)` = exit 3. PROPOSAL.md's
implementer-pass rewrote this to "git is unavailable (domain
fallback, not failure)" = `IOSuccess("unknown")` = no failure
at all.

A recreator implementing from PROPOSAL.md gets one behavior. A
recreator implementing from deferred-items (or the revision file
if they read history) gets the opposite. Both authorities claim
to be final. The two-implementer test fails: `revise` on a
container without `git` would (PROPOSAL path) succeed with an
`unknown` author field, or (deferred-items path) fail with exit
3 directing the user to install git.

There is a further ambiguity even within the deferred-items
reading: is the "missing git binary" path truly exit 3 domain
error? If `livespec doctor` needs git only for out-of-band-edits
(which already self-skips on non-git-repo), and `revise`/`seed`
need git only for author capture (which gracefully falls back
to `"unknown"` for missing config), the case for hard-failing
on "no git binary" is weak. It's a design question the v009
revision implicitly picked ("exit 3") but the PROPOSAL.md
implementer pass effectively overrode ("IOSuccess fallback").

### Proposed Changes

Pick one disposition and update all three documents to match:

- **A. Align everything to the revision's original intent:
  missing git binary = `IOFailure(GitUnavailableError)`, exit 3.**
  Rewrite PROPOSAL.md's §"Git" to say: "The function returns
  `IOSuccess('<name> <email>')` on success,
  `IOSuccess('unknown')` when git is available but either
  config value is unset (domain fallback), and
  `IOFailure(GitUnavailableError)` when the git binary is
  absent from PATH (domain error; supervisor maps to exit 3)."
  Keep deferred-items and revision as-is (they're already
  correct). Rationale: `revise` and `seed` are
  specification-writing operations; running them without git
  on a project that otherwise uses git governance is a real
  configuration error worth surfacing. The narrower exception
  (`user.name`/`user.email` unset) is a softer case worth
  falling back on.

- **B. Align everything to PROPOSAL.md's as-written intent:
  missing git binary = `IOSuccess("unknown")`.** Rewrite
  deferred-items `io/git.get_git_user()` semantics: "always
  returns success; literal `'unknown'` on missing git binary,
  missing config, or unset values; never raises; never IOFailure
  in v1." And reduce `GitUnavailableError` to a removable type
  (no domain condition triggers it). Risk: `GitUnavailableError`
  is still named in the style doc `LivespecError` hierarchy;
  removing it is cleaner but more surgical. Rationale:
  `"unknown"` is a sane fallback; users in ephemeral containers
  without git should not be blocked from writing specs.

- **C. Split the cases explicitly.** Define two separate
  fallback conditions: (c1) git binary missing → exit 3 if
  `livespec.io.git.get_git_user()` is the reason, but
  the calling site (`revise`/`seed` auto-capture) soft-catches
  the failure and uses `"unknown"`; (c2) config unset →
  `IOSuccess("unknown")`. Rewire the wrapper to always soft-
  fallback at the call site even when the function itself fails.
  Rationale: preserves the failure typing for potentially other
  callers while keeping the auto-capture flow resilient. Adds
  complexity.

Recommended: **A**. The v009 revision was explicit; PROPOSAL.md's
implementer pass drifted. Aligning to the revision costs one
sentence in PROPOSAL.md; `deferred-items.md` and the revision
already say the right thing; the style doc's
`GitUnavailableError` subclass and `exit_code = 3` stay
meaningful.

---

## Proposal: J3-custom-template-prompt-path-unresolvable

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**incompleteness** (no defined mechanism for the LLM to reach a
custom template's prompt files when `.livespec.jsonc`'s `template`
field resolves to a user-provided directory path rather than the
built-in `livespec` template).

### Summary

Per-sub-command SKILL.md prose invokes template prompts via
Claude Code's `@`-reference syntax, literal and static:
`@../../specification-templates/<template>/prompts/<name>.md`.
This works for the built-in `livespec` template (a known
path relative to the skill). It does NOT work for custom
templates at an arbitrary user path read at runtime from
`.livespec.jsonc`. No mechanism — copy-to-canonical, wrapper-
resolved path echoed to the LLM, Read-tool dispatch, etc. — is
specified for the custom-template case. Custom templates are in
v1 scope (PROPOSAL.md §"Custom templates are in v1 scope").

### Motivation

**PROPOSAL.md lines 212-214** (Per-sub-command SKILL.md body
structure, step 4):

> - Invoke a template prompt at
>   `@../../specification-templates/<template>/prompts/<name>.md`
>   and capture its output.

**PROPOSAL.md lines 846-851** (Custom templates are in v1 scope):

> - `.livespec.jsonc`'s `template` field accepts either a
>   built-in name or a path to a template directory.
> - Doctor check `template-exists` validates the resolved
>   template directory has the required layout and that
>   `template_format_version` matches what livespec supports.

**PROPOSAL.md line 1026-1030** (seed):

> The LLM (per `seed/SKILL.md`) invokes the active template's
> `prompts/seed.md` with `<intent>` and the template's
> `specification-template/` starter content as input.

`@`-reference syntax in Claude Code is literal — it names a
specific path. There is no documented runtime interpolation that
lets `@<variable>/prompts/seed.md` resolve at invocation time
from a config-read field. The SKILL.md body therefore cannot
name the custom-template path in its step instructions; the LLM
has no mechanism to follow the instruction for a custom
template.

Three workable mechanisms exist; none is chosen:

1. **Skill prose dispatch via Read tool** — the SKILL.md prose
   instructs the LLM to read `.livespec.jsonc`, resolve
   `template` to an absolute or repo-relative path, then use
   the Read tool to fetch `<resolved-path>/prompts/<name>.md`.
2. **Wrapper resolves and emits the path** — a new wrapper
   step (or a helper under `bin/`) reads `.livespec.jsonc` and
   prints the resolved template path to stdout; the LLM reads
   the output and then uses Read.
3. **Copy-to-canonical** — at seed or bootstrap, the active
   template's `prompts/` is copied to a skill-local canonical
   path (e.g., `.claude-plugin/scripts/active-template-prompts/`)
   and SKILL.md `@`-references that canonical location. Costs:
   mutation under `.claude-plugin/scripts/`, stale-copy risk on
   template swap.

Recreatability is broken without picking one.

### Proposed Changes

Pick a mechanism and codify it in PROPOSAL.md §"Per-sub-command
SKILL.md body structure" + §"Templates" + each affected
sub-command section:

- **A. Skill-prose Read-tool dispatch (runtime resolution).**
  Codify: SKILL.md step 4 reads as "Invoke the active template's
  `prompts/<name>.md`: resolve `.livespec.jsonc`'s `template`
  field to a directory path (relative to project root; built-in
  names resolve to `../../specification-templates/<name>/`,
  arbitrary strings resolve to the literal path relative to
  project root), then read the resulting
  `<template-path>/prompts/<name>.md` via the Read tool." Drop
  the literal `@`-reference syntax requirement. Risks: LLM
  reliability reading conditional paths. Benefit: no canonical-
  copy mutation; no bootstrap step; no wrapper helper.

- **B. Wrapper-emits-resolved-template-path.** Add a `bin/
  resolve_template.py` wrapper (or extend an existing wrapper
  with a query mode) that prints the resolved template path
  (built-in or custom) to stdout. Each sub-command's SKILL.md
  step 4 first invokes `resolve_template.py` via Bash, captures
  stdout, then uses Read to fetch
  `<captured-path>/prompts/<name>.md`. Cleaner handoff; costs
  one new Python module + tests.

- **C. Copy-to-canonical at seed/bootstrap.** `just bootstrap`
  (and `seed`, post-invocation) copy the active template's
  `prompts/` to
  `.claude-plugin/scripts/_active_template/prompts/`. SKILL.md
  `@`-references that canonical location. Invalidate on
  template swap (new config doctor check). Introduces scripted
  mutation in the plugin bundle (a user-project run writes into
  the shipped plugin tree — awkward under plugin-install
  semantics); discouraged.

- **D. Drop custom templates from v1.** Revisit the v003
  decision that put custom templates in v1 scope. Keep only the
  built-in `livespec` template. `template` field accepts only
  `"livespec"` in v1. Defer user-provided template paths to v2.
  Cleanest simplification but reopens a settled v003 decision.

Recommended: **A**. Least mechanism added; the skill layer is
already LLM-mediated and reading a config file + a prompt file
is within the LLM's natural capability. The instruction in
SKILL.md becomes longer but stays declarative. Option B is a
reasonable alternative if we find the LLM's path handling
unreliable during dogfood testing; we can upgrade A→B via
propose-change without breaking users. Option D would be a
significant scope reduction (v003 explicitly put custom
templates in-scope); not recommended unless we decide custom-
template support is buying us less than we thought.

---

## Proposal: J4-retry-on-exit-3-class-ambiguity

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-script-style-requirements.md
- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**ambiguity** (the SKILL.md `Retry-on-exit-3` step instructs the
LLM to retry the template prompt "with validation-class
findings," but exit 3 is the shared exit code for multiple
failure classes and no structured discriminator in the findings
schema lets the LLM classify the failure cause).

### Summary

The wrapper-side ROP chain emits exit 3 under at least four
distinct failure conditions: (1) JSON-schema validation failure
(LLM output malformed — retryable), (2) pre-step doctor static
failure (working tree in wrong state — NOT retryable; user must
fix), (3) sub-command-logic domain error (e.g., precondition
like "no proposals in proposed_changes/" for `revise` — NOT
retryable), (4) post-step doctor static failure (e.g., generated
output violates static rule — NOT retryable without different
LLM output). All four paths produce the same exit code. The
findings emitted via structlog on stderr don't carry a
discriminator field. The SKILL.md prose tells the LLM to "re-
invoke the relevant template prompt with the error context from
stderr" only on "validation-class findings" — without a way for
the LLM to tell validation failures apart from the other three.

### Motivation

**PROPOSAL.md lines 221-226** (Per-sub-command SKILL.md body,
step 4):

> - **Retry-on-exit-3:** on wrapper exit code 3 with
>   validation-class findings, re-invoke the relevant template
>   prompt with the structured error context from stderr and
>   re-assemble the JSON payload. Up to 3 retries per PROPOSAL.md
>   §"Templates — Skill↔template communication layer"; abort
>   on repeated failure with a visible user message.

**PROPOSAL.md lines 463-468** (wrapper lifecycle):

> Behavioral contract of each static phase in the wrapper chain:
> - The check registry runs; every check produces a `Finding`
>   (`pass` / `fail` / `skipped`).
> - On any `status: "fail"` the wrapper aborts with exit 3.
>   Findings are emitted to stderr via structlog for LLM
>   narration.

**PROPOSAL.md line 1043-1045** (seed):

> The wrapper validates the payload against the schema internally;
> on validation failure, it exits 3 with structured findings on
> stderr

**doctor_findings.schema.json shape** (PROPOSAL.md line 1323):

> { "check_id": "doctor-version-contiguity", "status": "fail",
>   "message": "...", "path": "SPECIFICATION/history", "line":
>   null }

**proposal_findings.schema.json shape** (PROPOSAL.md lines
1104-1111): `name`, `target_spec_files`, `summary`, `motivation`,
`proposed_changes` — no `status` field, no class discriminator.

The doctor findings schema has `check_id` that can distinguish
categories (prefix `doctor-`) — but validation failures (which
don't come from doctor checks, they come from the wrapper's
internal `validate/<name>` call) won't have a `doctor-` prefix.
What IS their `check_id`? Unspecified. Is there even a
`check_id` field for validation failures, or do they use a
different shape?

A conservative reader would conclude the LLM has no protocol
to tell validation failures apart from doctor static failures:
the retry loop would retry pre-step doctor failures (wrong) or
skip validation-failure retries (worse). Either behavior
violates the intended contract.

Related: the v009 I8 resolution ("fold validation into main
wrapper... SKILL.md prose: on wrapper exit 3 with a
validation-class finding, re-invoke the template prompt with
error context and retry, up to 3 retries") assumed the LLM
could distinguish classes from findings content. But the
findings schema + wrapper doesn't emit that discriminator.

### Proposed Changes

Add a structured finding-class discriminator, or use exit-code
granularity, so the LLM can classify the failure deterministically:

- **A. Add `finding_class` (or `source`) field to the findings
  on stderr; SKILL.md retry-gate reads it.** Extend the structlog
  event schema on stderr (NOT the stdout doctor_findings schema)
  with a `finding_class` field taking values like
  `"schema-validation"`, `"pre-step-static"`, `"sub-command-
  precondition"`, `"post-step-static"`. The SKILL.md retry step
  reads structlog output for the most recent event, parses the
  `finding_class` field, and retries only when class ==
  `"schema-validation"`. Codify this contract in the style doc
  §"Structured logging" and add the finding-class enumeration
  to `deferred-items.md`'s `static-check-semantics` (widened).

- **B. Split exit codes: validation gets its own code (e.g., 4);
  exit 3 stays "precondition/doctor-class."** The LLM retry rule
  becomes "retry on exit 4; abort on exit 3." Simpler for the
  LLM; requires updating the §"Exit code contract" table to
  define exit 4. Breaks the v005/v006 exit-code convention
  (0/1/2/3/126/127) slightly. Arguably cleaner.

- **C. Retry everything on exit 3 (up to 3 tries); accept that
  non-validation exits waste retry budget.** Simplest for the
  LLM; worst UX when a pre-step fail just loops uselessly 3
  times before aborting. Not recommended.

- **D. Drop the retry loop entirely; exit 3 always aborts.** The
  LLM re-prompts the user (not the template) with error context
  on any exit 3. Simpler; forfeits automated validation-retry
  recovery. Implements the original v007 pre-I8 shape.

Recommended: **A**. Minimal cost (one more structlog kwarg),
keeps the exit code table intact, operationalizes I8's "retry
on validation-class findings" phrase. `static-check-semantics`
deferred item picks up the exact enumeration of
`finding_class` values and which event classes are retryable.

---

## Proposal: J5-build-parser-violates-public-api-result-typed

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md
- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**malformation** (self-contradiction in the style doc:
`build_parser() -> ArgumentParser` is defined as a public
function in `livespec/commands/<cmd>.py` but violates
`check-public-api-result-typed` as narrowed by v009 I4, which
exempts only `main` in `commands/**.py` and `doctor/run_static.py`).

### Summary

The style doc §"CLI argument parsing seam" (added by v009 I4 + v008
H3) establishes `livespec/commands/<cmd>.py` exposes a pure
`build_parser() -> ArgumentParser` factory. `ArgumentParser` is
neither `Result[_, _]` nor `IOResult[_, _]`. `build_parser` is
public (not underscore-prefixed). It is not the `main` supervisor.
Per the narrowed `check-public-api-result-typed` exemption (I4
disposition: "exempts supervisor functions (by name `main` in
`commands/**.py` and in `doctor/run_static.py`) from the
Result/IOResult return requirement"), `build_parser` is not
exempted — and hence fails the check as written.

### Motivation

**style doc lines 378-383** (CLI argument parsing seam):

> **`livespec/commands/<cmd>.py`** exposes a pure
> `build_parser() -> ArgumentParser` factory. This factory
> constructs the parser (subparsers, flags, help strings) but does
> NOT parse. Keeping construction pure lets tests introspect the
> parser shape without effectful invocation.

**style doc lines 586-591** (Type safety):

> Every public function's return annotation MUST be `Result[_, _]`
> or `IOResult[_, _]`, UNLESS the function is a supervisor at a
> deliberate side-effect boundary (e.g., `main() -> int` in
> `commands/*.py` and `doctor/run_static.py`, or any function
> returning `None`). The rule exempts only such supervisors.

**deferred-items.md line 168-173** (static-check-semantics
supervisor public-API exemption):

> `check-public-api-result-typed` exempts supervisor functions
> (by name `main` in `commands/**.py` and in `doctor/run_static.py`)
> from the Result/IOResult return requirement

`build_parser` returns `ArgumentParser` and is public. It is not
`main`. It is not returning `None`. The AST check rejects it.
An implementer faithfully implementing both sections produces
code that fails their own enforcement.

### Proposed Changes

Narrow the check scope or broaden the exemption:

- **A. Add `build_parser` (by function name) to the
  `check-public-api-result-typed` exemption list.** Parallel to
  `main`. Rationale: `build_parser` is a factory that
  constructs a static framework type (argparse) without
  effects; it's a constructor, not a live function. The exemption
  is surgical. Update the deferred-items `static-check-semantics`
  entry to enumerate `build_parser` alongside `main`. Update the
  style doc §"Type safety" exemption list explicitly.

- **B. Rename `_build_parser` (private).** Single-leading-
  underscore prefix removes it from the "public function"
  domain. `main()` calls it internally. Costs: test code
  technically has to access a private symbol to introspect the
  parser. pytest and pyright accept this fine in practice.

- **C. Wrap `build_parser` to return `Result[ArgumentParser,
  Never]`.** Mechanical fix that satisfies the rule literally.
  Ugly. A parser factory is deterministic and can't fail, so the
  `Result` wrapping is ceremony. Not recommended.

- **D. Move `build_parser` out of `commands/<cmd>.py` into
  `io/cli.py` (where `@impure_safe` already marks the surface).**
  Then `build_parser` is part of the CLI seam itself. Problem:
  this spreads argparse construction across sub-commands into a
  single `cli.py`, which loses per-sub-command scoping.
  Not recommended.

Recommended: **A**. The `build_parser` name is well-known;
enumerating it as an exempt function name parallels the `main`
exemption and avoids a testing-exposes-private-symbol wart.
Keep the rest of the style doc architecture intact.

---

## Significant gaps

These items force a load-bearing guess from the implementer or
produce clearly wrong behavior when followed literally. Each has
a narrow fix.

---

## Proposal: J6-propose-change-author-precedence-rule-missing

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**incompleteness** (`author` field in propose-change-created
proposed-change front-matter has no defined precedence rule;
v009 I13 established precedence for `reviser_llm` on
critique/revise/seed but propose-change was not covered).

### Summary

`bin/propose_change.py --findings-json <tempfile> <topic>` creates
a file with YAML front-matter (`topic`, `author`, `created_at`).
`topic` comes from the CLI arg; `created_at` is current time.
`author` has no defined source. For critique and revise, v009 I13
established env-var `LIVESPEC_REVISER_LLM` → LLM-self-declared
`reviser_llm` field in the JSON payload → `"unknown-llm"`
fallback. For seed, the wrapper uses `author: livespec-seed` (the
reserved skill-tool prefix). For direct `propose-change` calls
(LLM-mediated with `--findings-json`), the wrapper has no
documented `author` source.

### Motivation

**PROPOSAL.md lines 1542-1548** (Proposed-change file format,
front-matter):

> ```yaml
> ---
> topic: <kebab-case-topic>
> author: <author-id>                # LLM identifier, human handle, or reserved livespec-<tool>
> created_at: <UTC ISO-8601 seconds>
> ---
> ```

**PROPOSAL.md lines 783-789** (Environment variables):

> **`LIVESPEC_REVISER_LLM`** (default unset). When set and
> non-empty, the `revise` and `critique` wrappers use this value
> for the `reviser_llm` / `<author>` field unconditionally...

Note: "revise and critique wrappers" — not propose-change.
Propose-change's `author` is not covered by the env var.

**PROPOSAL.md lines 1090-1100** (propose-change wrapper):

> **`bin/propose_change.py` ONLY accepts `--findings-json <path>`**
> ... The wrapper validates the JSON against
> `scripts/livespec/schemas/proposal_findings.schema.json` and
> maps each finding to one `## Proposal` section. The mapping is
> one-to-one field-copy: ...

The proposal_findings schema items are `name`, `target_spec_files`,
`summary`, `motivation`, `proposed_changes`. No author-per-finding
or author-per-file field. Whose name goes in the `author` key of
the file-level front-matter?

The wrapper has nothing to fill that field with. The LLM
generating the findings could be instructed to include an
`author` in the payload, but no schema field is defined, and no
precedence is documented. An implementer following PROPOSAL.md
literally writes nothing in that position, producing
schema-invalid output.

### Proposed Changes

- **A. Mirror I13 for `propose-change` `author`.** Extend the
  proposal-findings schema with a (file-level? first-finding?)
  optional `author` field. Or add a new CLI flag
  `--author <id>` to `bin/propose_change.py`. Or widen
  `LIVESPEC_REVISER_LLM` env var coverage to include
  propose-change. Or combine: precedence (1) CLI
  `--author <id>` → (2) env var `LIVESPEC_REVISER_LLM` → (3)
  LLM self-declared field in payload → (4) `"unknown-llm"`
  fallback. Update PROPOSAL.md §"Configuration → Environment
  variables" to list propose-change alongside revise/critique.
  Update `wrapper-input-schemas` deferred item to cover the
  schema extension.

- **B. Propose-change is always `"unknown-llm"` in v1.** Simplest:
  propose-change files have `author: unknown-llm` literal. LLM
  doesn't self-declare. Users can manually edit the file post-
  creation if they care. Costs: reduced provenance fidelity; no
  way to tell who authored a given proposed-change file.

- **C. Propose-change takes a required `--author <id>` CLI flag;
  LLM is instructed to determine and pass it.** Rigorous; user
  never sees `"unknown-llm"`. Costs: more prescription.

Recommended: **A**. Consistent with I13's discipline; surgical
extension to schema + env var coverage. Update the proposal-
findings schema to include optional file-level `author`, keep
precedence behavior identical to I13.

---

## Proposal: J7-help-flag-exits-as-usage-error

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incorrectness** (internally consistent but specifies behavior
that conflicts with a universally-followed CLI convention;
`--help` and `-h` invoke the IOFailure(UsageError) path and the
supervisor maps that to exit 2, treating a user-intentional
help request as a usage error).

### Summary

The style doc §"CLI argument parsing seam" (part of v008 H3 + v009
I4's wrapper-shape disposition) routes `--help` / `-h` detection
through `IOFailure(UsageError("<help text>"))` and maps that to
exit 2 via the railway. Exit 2 is defined in the exit-code table
as "Usage error: bad flag, wrong argument count, malformed
invocation." A user asking for help is not making a usage error.
Standard CLI convention: `--help` → stdout prints help → exit 0.
Routing help through the usage-error branch conflicts with the
exit-code table's own definition and surprises any script or
CI pipeline that inspects exit codes.

### Motivation

**style doc lines 371-378** (CLI argument parsing seam):

> **`livespec/io/cli.py`** exposes `@impure_safe`-wrapped functions
> that construct argparse invocations with `exit_on_error=False`
> (Python 3.9+), returning `IOResult[Namespace, UsageError]`.
> `-h`/`--help` is detected explicitly before `parse_args` runs;
> on detection, the function returns `IOFailure(UsageError("<help
> text>"))` so the supervisor can emit the help text and exit `2`
> via the railway rather than argparse's implicit `SystemExit(0)`.

**style doc line 827** (Exit code contract table):

> | `2` | Usage error: bad flag, wrong argument count, malformed
> invocation. |

A help request is not a bad flag, not a wrong argument count, not
malformed. It is a user asking to see usage. Treating it as exit 2
directly contradicts the exit-code definition.

Practical consequence: CI pipelines and scripts that run
`livespec --help` in setup/validation scripts will treat the exit
as failure (exit 2). GNU/POSIX convention: `--help` exits 0.
argparse's default (sys.exit(0) on `--help`) matches that
convention; the v009 workaround (route through UsageError to
avoid argparse's implicit SystemExit) broke the convention as a
side effect.

The underlying concern was legitimate: the supervisor discipline
forbids `sys.exit` outside `bin/*.py`; argparse's implicit
`sys.exit(0)` on `--help` violates that. The fix (detect
`-h`/`--help` first, route through IOFailure) needs a finer-
grained shape.

### Proposed Changes

- **A. Add a `HelpRequested` marker class that is NOT a
  `LivespecError` subclass; supervisor maps to exit 0.** Extend
  `livespec/io/cli.py` to return
  `IOResult[Namespace, UsageError | HelpRequested]`. `HelpRequested`
  carries the help text. The supervisor pattern-match:
  `IOFailure(HelpRequested)` → emit text to stdout → exit 0;
  `IOFailure(UsageError)` → emit text to stderr → exit 2;
  otherwise proceed. Update the exit-code contract: add
  "Intentional help output: exit 0" as a non-error completion
  path. Update the ROP composition type to accommodate.

- **B. Supervisor gains a pre-flow `--help`/`-h` check; emits
  help text and `return 0` before entering the railway.** Simpler
  implementation; violates the "all CLI concerns in the railway"
  cleanliness. Keeps `UsageError` narrower (genuinely bad flags
  only). `main()` supervisor body becomes:
  ```python
  if "-h" in argv or "--help" in argv:
      print(build_parser().format_help())
      return 0
  ctx = flow(argv, ...)
  return derive_exit_code(ctx)
  ```
  Still compatible with `check-supervisor-discipline` (no
  `sys.exit`; `return 0` exits via the shebang wrapper's
  `raise SystemExit(main())`).

- **C. Accept the v009 wording: `--help` exits 2; users who
  script around livespec learn to accept the non-standard exit.**
  Not recommended.

Recommended: **A**. Clean type-system expression of the
distinction; matches the sum-type fidelity principle (help is a
different category from usage error). Update
`livespec/errors.py` to include `HelpRequested` at module level
but note it is NOT a `LivespecError` subclass (not a domain
error; not a bug; a third category — informational early-exit).
Include an explicit "exit 0 for intentional --help" row in the
exit-code contract table.

---

## Proposal: J8-coverage-scope-silence-on-bin

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**ambiguity** (the 100% line+branch coverage mandate names
`scripts/livespec/**` and `<repo-root>/dev-tooling/**` as in
scope; `scripts/bin/**` — home of `_bootstrap.py` and every
shebang wrapper — is neither explicitly included nor explicitly
excluded; its covered-ness is inferable only from scattered
hints).

### Summary

The coverage scope is defined as `scripts/livespec/**` and
`dev-tooling/**`. The shebang wrappers live at `scripts/bin/*.py`
— outside `scripts/livespec/**`. `_bootstrap.py` also lives there
and is actively tested by `tests/bin/test_bootstrap.py`.
Wrapper bodies are pragma-excluded via `# pragma: no cover`. The
mandate would naturally treat `bin/` as out-of-scope for
coverage entirely (the named scope doesn't include it); the
presence of tests for `_bootstrap.py` plus the wrapper-body
pragma imply it IS in scope; nothing ties the threads together.

### Motivation

**PROPOSAL.md lines 1693-1696** (Testing approach, coverage):

> Coverage MUST be 100% line + branch across all Python files
> under `.claude-plugin/scripts/livespec/**` and
> `<repo-root>/dev-tooling/**`.

**style doc line 718**:

> **100% line + branch coverage** is mandatory across the whole
> Python surface in `scripts/livespec/**` and
> `<repo-root>/dev-tooling/**`.

**style doc lines 725-729** (Escape hatch):

> Common legitimate uses: `if TYPE_CHECKING:` guards,
> `sys.version_info` gates in `bin/_bootstrap.py`, the
> `bin/*.py` wrapper bodies (each is a trivial 6-line pass-through
> covered by the wrapper-shape meta-test).

**style doc line 721-722**:

> `pyproject.toml`'s `[tool.coverage.run]` sets `source =
> ["livespec"]`

So `source = ["livespec"]` — i.e., only the `livespec` package
(under `scripts/livespec/`). `bin/` is not a source root. Which
means coverage.py won't measure `bin/*.py` at all. Yet
`tests/bin/test_bootstrap.py` tests `_bootstrap.py`. Whose
coverage does that measurement register against?

Three possible interpretations, each with different downstream
effects:

1. `bin/*.py` is excluded from coverage altogether — `tests/
   bin/test_bootstrap.py` exists but doesn't contribute to
   the 100% mandate. Pragma statements in wrappers are
   vestigial (covering nothing that would otherwise be counted).
2. `bin/*.py` is implicitly included in coverage — `source =
   ["livespec"]` is wrong or shorthand for "livespec's source
   roots including bin/." Pragma statements in wrappers matter.
3. Only `_bootstrap.py` is covered (via tests); wrappers are
   trivially exempt; the `source` list is actually wrong.

A recreator can pick any of the three; they produce different
`pyproject.toml` layouts.

### Proposed Changes

- **A. Make `scripts/bin/` explicitly in scope; set `source =
  ["livespec", "../bin"]` (or equivalent path).** The 100%
  mandate covers every Python file shipped in the plugin
  bundle (not just `livespec/`). `_bootstrap.py` is fully
  covered by `tests/bin/test_bootstrap.py`; wrapper bodies
  are pragma-excluded. Update PROPOSAL.md and the style doc to
  name `scripts/bin/**` explicitly in the coverage scope.
  Recommended.

- **B. Explicitly exclude `scripts/bin/` from coverage.** The
  100% mandate covers `livespec/**` and `dev-tooling/**` only.
  `_bootstrap.py` + wrapper bodies are not coverage-measured.
  The `tests/bin/test_bootstrap.py` tests still exist (verify
  behavior) but don't contribute to coverage. Wrapper pragma
  statements are unnecessary. Cleaner `source` list.

- **C. Keep silent; let the implementer pick.** Not recommended;
  this is the current state and it's ambiguous.

Recommended: **A**. `_bootstrap.py` is non-trivial (version
check + sys.path construction) and deserves coverage
enforcement. Rule-as-intended: the whole plugin bundle's
Python surface is at 100%. Make it explicit.

---

## Proposal: J9-vendored-lib-version-file-source-ambiguity

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**ambiguity** (PROPOSAL.md names `.vendor.toml` OR "per-lib
VERSION files" as the source for vendored-library version
records; every other v009 document names `.vendor.toml` as
the sole source; the "or" clause is a stale v008 / pre-v007
leftover).

### Summary

PROPOSAL.md §"Runtime dependencies → Vendored" reads as if
two mechanisms are acceptable: `.vendor.toml` at repo root or
per-lib `VERSION` files. Every other authoritative document
(style doc, deferred-items, developer-tooling layout, DoD) says
`.vendor.toml` alone. Recreator uncertainty: "set up per-lib
VERSION files" vs "set up `.vendor.toml`" — or does
`.vendor.toml` have to coexist with per-lib files for redundancy?

### Motivation

**PROPOSAL.md lines 323-335** (Runtime dependencies, vendored):

> - **Vendored pure-Python libraries** bundled with the skill, each
>   pinned to an exact upstream version recorded in
>   `<repo-root>/.vendor.toml` (or per-lib `VERSION` files):

**PROPOSAL.md line 1832** (Developer tooling layout):

> ├── .vendor.toml                              (records exact upstream version pinned for each vendored library)

**style doc lines 124-127** (Vendored third-party libraries):

> Locked vendored libs for v008 (each pinned to an exact upstream
> ref recorded in `<repo-root>/.vendor.toml`):

**style doc lines 163-168** (Vendoring discipline):

> - **`.vendor.toml`** records `{upstream_url, upstream_ref,
>   vendored_at}` per lib.

**deferred-items.md line 111**:

> `<repo-root>/.vendor.toml` (or per-lib VERSION files per G12)

Only the PROPOSAL.md line 325 + deferred-items.md line 111
preserve the "or per-lib VERSION files" language from pre-v007.
The G12 reference is to the v007 critique of vendor-audit, where
the "or per-lib VERSION files" was a live option. That option
was not adopted (v007 chose `.vendor.toml`). The parenthetical
survives as an editorial leftover.

### Proposed Changes

- **A. Strip "or per-lib VERSION files" from PROPOSAL.md and
  deferred-items.md.** `.vendor.toml` is the sole documented
  mechanism; it already appears in every other document. Two-
  sentence edits. Recommended.

- **B. Leave the choice open to the implementer.** If both
  mechanisms are acceptable, codify both. But the DoD and
  developer-tooling layout only name `.vendor.toml`, so the
  implementer producing both formats would write one that's
  never referenced. Not sensible.

- **C. Reopen the v007 choice.** Discuss whether per-lib
  VERSION files would be preferable (they're simpler, grep-
  friendly, more git-history-visible per-lib). Reopens a
  settled decision. Not recommended.

Recommended: **A**.

---

## Proposal: J10-prepushstep-skip-has-no-cli-re-enable

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**incompleteness** (no CLI-level path to re-enable pre-step
doctor static when `.livespec.jsonc`'s
`pre_step_skip_static_checks: true` is set; the "effective skip
= config OR wrapper flag" formula is union-monotonic, so config
can't be overridden from CLI).

### Summary

The documented skip semantics (PROPOSAL.md lines 476-481) say:
"Effective skip = config OR wrapper flag." Starting from config
= `true`, no value of the wrapper flag can produce effective
skip = false. The user who set `pre_step_skip_static_checks:
true` globally and now wants to invoke `livespec propose-change`
WITH pre-step for a one-off is stuck: their only option is
editing the config (persisting the change for all subsequent
invocations) or removing `--skip-pre-check` (which does nothing,
since config already skips). No inverse flag exists
(`--run-pre-check` or similar).

### Motivation

**PROPOSAL.md lines 476-481** (Pre-step skip control):

> - The `--skip-pre-check` flag (and config key
>   `pre_step_skip_static_checks: true`) skips the pre-step static
>   run for sub-commands that have one. The skill MUST surface a
>   warning via LLM narration whenever pre-step is skipped.
>   Effective skip = config OR wrapper flag.

OR is union. Once `config = true`, wrapper flag value is
irrelevant. There is no `--no-skip-pre-check` or `--run-pre-check`
listed.

**PROPOSAL.md lines 724-729** (.livespec.jsonc schema):

> // If true, sub-commands skip the pre-step static check.
> // Intended for emergency recovery when the project is in a
> // broken state that normal commands cannot repair. The skill
> // MUST print a warning every time pre-step is skipped.
> // Default: false

Config explicitly for "emergency recovery when the project is
in a broken state that normal commands cannot repair" — which
would likely be set project-wide so that normal
operations can proceed, and then the user would want to re-enable
for one-off invocations to verify recovery is complete. No
mechanism exists.

Related: the effective-skip formula is asymmetric with
`--skip-subjective-checks` (LLM-layer; I8 says "Effective skip =
config OR LLM-layer flag") — same one-way bias at the LLM layer.

### Proposed Changes

- **A. Add inverse CLI flag `--run-pre-check` (or
  `--enforce-pre-check`).** Effective skip becomes "config AND
  NOT --run-pre-check, OR --skip-pre-check." Three-valued CLI
  flag: skip, run, unset (use config). Codify. Update PROPOSAL.md
  + add to SKILL.md body structure step 3 (Inputs) for every
  pre-step-having sub-command.

- **B. Leave as-is; document the limitation.** The config is
  for emergency use; users are expected to toggle it on/off
  textually. The "effective skip = union" formula is intentional.
  Update PROPOSAL.md comment for the config key:
  `pre_step_skip_static_checks` — "Once set to true, pre-step
  is skipped for every invocation until the key is set back to
  false; no CLI override exists."

- **C. Reverse the formula: Effective skip = wrapper flag
  (default = config value).** Wrapper flag default is the config
  value; when set, it overrides. Cleaner; breaks the current
  "union" semantics; matches most CLI precedence conventions
  (CLI overrides config).

Recommended: **B**. The config is for emergency recovery; it's
rare, and "toggle the key on when needed, off when done" is a
reasonable workflow. Adding an inverse flag grows the surface
for minimal benefit. Document the limitation explicitly.

---

## Proposal: J11-finding-dataclass-pairing-with-schema

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**ambiguity** (the `Finding` dataclass lives at
`livespec/doctor/finding.py` but `check-schema-dataclass-pairing`
(I3) requires every JSON schema to pair with a dataclass under
`schemas/dataclasses/<name>.py`; how does the check handle the
nested Finding-in-DoctorFindings relationship, and where does
Finding actually belong?).

### Summary

PROPOSAL.md and style doc locate the `Finding` dataclass at
`livespec/doctor/finding.py` (separate from the `schemas/
dataclasses/` tree). The v009 I3 disposition established
`check-schema-dataclass-pairing`: "every `schemas/*.schema.json`
has a paired dataclass at `schemas/dataclasses/<name>.py`." The
`doctor_findings.schema.json` is one such schema, and its shape
is `{"findings": [{"check_id", "status", "message", "path",
"line"}, ...]}`. The paired dataclass `DoctorFindings` would
need a `findings: list[Finding]` field — but `Finding` lives
elsewhere. The pairing rule doesn't specify whether it walks
transitively through nested types, whether `Finding` should
move to `schemas/dataclasses/finding.py`, or whether the
`DoctorFindings` dataclass should redefine the Finding shape
inline.

### Motivation

**PROPOSAL.md line 104** (Skill layout):

> │       ├── doctor/
> │       │   ├── run_static.py
> │       │   ├── finding.py               # Finding dataclass + pass/fail constructors
> │       │   └── static/

**PROPOSAL.md line 138-145** (schemas tree):

> │       ├── schemas/                             # JSON Schema Draft-7 files + paired dataclasses
> │       │   ├── dataclasses/                       # paired hand-authored dataclasses (see I3)
> │       │   │   ├── ...
> │       │   │   ├── doctor_findings.py
> │       │   │   ├── ...
> │       │   ├── doctor_findings.schema.json       # doctor static-phase output contract

**style doc lines 217-222** (schemas tree):

> ├── schemas/                          # JSON Schema Draft-7 files + paired dataclasses
> │   ├── dataclasses/                             # paired hand-authored dataclasses (see below)
> │   │   ├── ...
> │   │   ├── doctor_findings.py
> │   │   ├── ...

**deferred-items.md lines 173-179** (static-check-semantics,
I3):

> **`check-schema-dataclass-pairing` semantics** (v009 I3):
> walks `scripts/livespec/schemas/*.schema.json` and
> `scripts/livespec/schemas/dataclasses/*.py`; for each
> schema, asserts a paired dataclass exists (by
> `$id`-derived name) with every listed field in matching
> Python type; and vice versa.

So the check walks `schemas/dataclasses/*.py` — it does NOT walk
`doctor/finding.py`. If `DoctorFindings.findings: list[Finding]`
references an external `Finding`, the pairing walker needs to
follow the type. Can it? The deferred entry says "every listed
field in matching Python type" — ambiguous whether the check
resolves the `list[Finding]` annotation to the external
`finding.py` module.

Three readings:

1. **`Finding` is re-exported via `schemas/__init__.py`**;
   `DoctorFindings` imports it from there; pairing check
   resolves types through the `schemas/` namespace only.
   Requires a `__init__.py` re-export and `Finding` still
   lives at `doctor/finding.py`.
2. **`Finding` should be moved to `schemas/dataclasses/finding.py`**
   so that the pairing check's walk catches it natively. No
   re-exports needed.
3. **The `DoctorFindings` dataclass defines the Finding shape
   inline** (e.g., as a nested `@dataclass` inside
   `doctor_findings.py`). Doesn't break `doctor/finding.py`
   but duplicates the type.

### Proposed Changes

- **A. Move `Finding` to `schemas/dataclasses/finding.py`; pair
  with a new `finding.schema.json` (or keep it only as
  `DoctorFindings.findings` item shape).** Simplest; the pairing
  check walks `schemas/dataclasses/*.py` finds `Finding` and
  `DoctorFindings`. `doctor/finding.py` is replaced by an
  import re-export: `from livespec.schemas.dataclasses.finding
  import Finding, pass_finding, fail_finding`. Costs: move the
  constructor helpers (`pass_finding`, `fail_finding`) either
  to the dataclass file or to a new helper. Recommended.

- **B. Keep `Finding` at `doctor/finding.py`; re-export via
  `schemas/__init__.py` and extend the pairing check to resolve
  imported symbols.** Deferred-items `static-check-semantics`
  widens to specify: "if a dataclass field type is a user-
  defined class imported from another module within
  `scripts/livespec/**`, the pairing check resolves the import
  and applies recursively." More AST complexity.

- **C. `DoctorFindings` inline-redefines the Finding shape** —
  flat dataclass with list of dicts (i.e., `findings:
  list[dict[str, object]]`). Trashes type fidelity; `Finding`
  dataclass still exists but isn't used in the schemas tree.
  Worst of both worlds.

Recommended: **A**. Puts all dataclass-paired types in one tree;
avoids the import-resolution complication; keeps the
schema-dataclass pairing check simple.

---

## Proposal: J12-dogfood-symlink-git-tracking-disposition

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**ambiguity** (PROPOSAL.md states the
`.claude/skills/ → ../.claude-plugin/skills/` symlink is created
by `just bootstrap` idempotently if missing; does not specify
whether the symlink is committed to git as a tracked symbolic
link, or is gitignored and requires `just bootstrap` after every
fresh clone).

### Summary

The dogfood symlink direction is specified (v009 I11) but not
the git-tracking disposition. Relevant to first-time developer
experience: on a fresh clone, does Claude Code see the skills
immediately (symlink tracked) or does the user need to run
`just bootstrap` first (symlink gitignored + bootstrap-created)?
The answer affects onboarding speed and CI behavior.

### Motivation

**PROPOSAL.md lines 32-39** (Plugin delivery):

> - During dogfooded development in the livespec repo,
>   `.claude/skills/` is a relative symlink pointing at
>   `../.claude-plugin/skills/` (i.e., `ln -s ../.claude-plugin/skills
>   .claude/skills`). The `.claude-plugin/skills/` directory is the
>   canonical plugin-delivery location; Claude Code reads the skills
>   via the symlink, avoiding a plugin-install step during
>   development. `just bootstrap` creates the symlink idempotently if
>   missing.

"`just bootstrap` creates the symlink idempotently if missing"
supports both readings:

1. **Gitignored symlink.** `.gitignore` excludes `.claude/skills/`.
   On fresh clone, symlink is absent; user runs
   `just bootstrap` to create it. Without the run, Claude Code
   can't find the skills. "Idempotent" here means "creates if
   missing; does nothing if present."
2. **Tracked symlink.** `.gitignore` does not exclude
   `.claude/skills/`. Fresh clone includes the symlink; Claude
   Code sees the skills immediately. `just bootstrap` is a
   no-op in the symlink dimension; other bootstrap steps
   (lefthook install) are still needed. "Idempotent" means
   "re-creates if a developer accidentally deleted it."

Onboarding UX differs: (1) requires documenting
`just bootstrap` as a mandatory first step for dogfood
development; (2) makes skills work immediately post-clone but
requires the repository's `.claude/` directory to contain a
tracked symlink (which some editors/tools handle awkwardly).

### Proposed Changes

- **A. Codify: `.claude/skills/` symlink IS committed to git
  as a tracked symbolic link; `just bootstrap`'s role is
  defensive (re-create if deleted).** Update PROPOSAL.md
  §"Plugin delivery" to add: "The symlink is committed to git
  as a tracked symbolic link under `.claude/skills/`;
  `just bootstrap` recreates it if a developer accidentally
  removes it. No `.gitignore` entry for `.claude/skills/`."
  Onboarding benefit: fresh clone works without bootstrap.
  Developer-tooling layout in PROPOSAL.md needs no `.gitignore`
  update.

- **B. Codify: `.claude/skills/` is gitignored;
  `just bootstrap` is mandatory for dogfood development.**
  Update PROPOSAL.md: "`.claude/skills/` is listed in
  `.gitignore`; fresh clones require `just bootstrap` before
  Claude Code can load the skills." Add `.claude/skills/` to a
  committed `.gitignore` file. Less magical; more explicit
  setup step; matches "plugin install is not a v1 delivery
  path" concern.

- **C. Leave silent; implementer picks.** Current state. Not
  recommended.

Recommended: **A**. Tracked symlink is standard practice for
monorepos with skill-like trees; onboarding is immediate; git
tracks symlinks cross-platform (Linux/macOS — both in v1
scope); one less surprise for new contributors. Clarifies that
`just bootstrap` is for fresh setup + defensive re-creation, not
a mandatory precondition.

---

## Proposal: J13-template-format-version-supported-set

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**ambiguity** (the `template-exists` check validates that
`template.json`'s `template_format_version` matches
`.livespec.jsonc`'s value AND "is supported by livespec"; the
set of supported versions is not enumerated).

### Summary

PROPOSAL.md §"Static-phase checks → template-exists" says the
check validates `template_format_version` is "supported by
livespec." In v1, only version `1` is referenced anywhere; no
authoritative enumeration lists the supported set. An implementer
hard-codes `SUPPORTED = {1}` or writes a list they treat as
authoritative — but there's no place in PROPOSAL.md, the style
doc, or deferred-items that names the set. Forward-looking
consumers (v2 adding version 2) have no clear extension point.

### Motivation

**PROPOSAL.md lines 1362-1366** (template-exists check):

> - **`template-exists`** — The active template (built-in or at the
>   configured path) exists and has the required layout
>   (`template.json`, `prompts/`, `specification-template/`).
>   `template.json`'s `template_format_version` matches
>   `.livespec.jsonc`'s `template_format_version` and is supported
>   by livespec.

**PROPOSAL.md line 822** (Template directory layout):

> - `template.json` is REQUIRED and MUST contain at minimum
>   `{"template_format_version": 1}`.

**PROPOSAL.md line 716** (.livespec.jsonc schema comment):

> // Expected template format version. Belt-and-suspenders check
> // against the template's own declared `template_format_version`
> // in its `template.json`. Doctor validates they match.
> // Default: 1

Nothing in PROPOSAL.md or the style doc says "v1 supports only
template_format_version 1" as a one-sentence invariant. The
nearest hint is the DoD (line 1913) "`template.json` declaring
`template_format_version: 1`" — inferential, not normative.

### Proposed Changes

- **A. Add explicit invariant in PROPOSAL.md §"Templates" (or
  §"Static-phase checks"): "v1 livespec supports only
  `template_format_version: 1`. The check MUST reject any
  other value as unsupported."** Trivial addition. Covers
  forward compatibility by naming the v1 set; v2+ can add
  values. Recommended.

- **B. Defer the supported-set enumeration to
  `static-check-semantics`.** Covered implicitly under
  "template_format_version check" — but this is an
  architectural invariant, not an edge case; deferring it is
  weaker than stating it in the main spec.

- **C. Leave silent.** Implementer hard-codes `{1}`;
  future reviewers can't tell if any other value was considered.
  Not recommended.

Recommended: **A**. One sentence in PROPOSAL.md resolves the
ambiguity. Subsequent versions update the line.

---

## Proposal: J14-prune-history-already-pruned-repeat-behavior

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**ambiguity** (`prune-history` behavior on an already-pruned
project — one `PRUNED_HISTORY.json` marker at `v(N-1)` plus one
full `vN` directory — is not defined; rule only covers "only
v001 with no marker = no-op").

### Summary

PROPOSAL.md line 986 says "Running `prune-history` on a project
with only `v001` (nothing to prune) is a no-op." This covers
the never-pruned state. But projects that have been pruned
previously reach a state like:
```
history/
├── README.md
├── v042/
│   └── PRUNED_HISTORY.json       # {"pruned_range": [1, 42]}
└── v043/
    ├── spec.md
    └── ...
```
Running `prune-history` on THIS state: N = 43. The "N-1"
marker directory `v042` already exists. Delete every
`history/vK/` where K < N-1 = 42 → nothing to delete (v042 is
the marker, v043 is vN). Replace `v042` contents with a new
marker — redundantly overwriting the existing one with
`{"pruned_range": [1, 42]}` (same value). Effectively a
no-op. But PROPOSAL.md line 986 doesn't say this; it only
addresses unpruned single-version state.

### Motivation

**PROPOSAL.md lines 962-986** (Pruning history):

> Operation:
>
> 1. Identify the current highest version `vN`.
> 2. If `history/v(N-1)/PRUNED_HISTORY.json` exists, read its
>    `pruned_range[0]` value and retain it as `first` for the new
>    marker (carrying the original-earliest version number forward).
>    If no prior marker exists, `first` is the earliest v-directory
>    version number currently in `history/` (typically `1`).
> 3. Delete every `history/vK/` directory where `K < N-1`.
> 4. Replace the contents of `history/v(N-1)/` with a single file:
>    `history/v(N-1)/PRUNED_HISTORY.json`, containing only
>    `{"pruned_range": [first, N-1]}`.
> 5. Leave `history/vN/` fully intact.
>
> Invariants:
>
> ...
> - Running `prune-history` on a project with only `v001`
>   (nothing to prune) is a no-op.

Step 4 as written would always overwrite `v(N-1)/` with a new
marker, even when the marker already exists with the same
range. The side effects (file mtime update, marker re-write)
are unobservable to users, but strict "no-op" behavior is not
asserted. An implementer may or may not short-circuit the
overwrite.

Two similar edge cases:
- **Already-pruned with only vN + marker:** `prune-history`
  should no-op (no deletions; marker re-write is redundant).
- **Fresh repo (vN=1, no history/v0/):** step 3's "delete every
  vK where K < 0" loop has zero iterations; step 4's "replace
  v0/" creates a new v0 directory with a marker — wrong; v0
  never existed.

### Proposed Changes

- **A. Extend the idempotency rule.** Add: "Running
  `prune-history` on a project where the oldest surviving
  history entry is already `PRUNED_HISTORY.json` (no full
  versions to prune) is a no-op. The existing marker is not
  re-written." Explicit coverage of the repeat-prune case.

- **B. Leave as-is.** Step 4 always rewrites the marker; the
  repeat-prune case is covered implicitly (behaviorally
  identical to the first prune). Costs: a redundant file-mtime
  update per repeat invocation; may confuse git diff readers
  ("why does this commit re-write the marker with no content
  change?"). Minor UX snag.

- **C. Forbid repeat prunes entirely.** The skill checks if
  `history/v(N-1)/PRUNED_HISTORY.json` already exists and
  there are no full versions to prune; returns an informational
  message and exits 0 without writing anything. More explicit
  than A.

Recommended: **A**. The no-op wording parallels the existing
"only v001 = no-op" invariant; picks up the edge case without
adding much prose. B is also acceptable; the mtime-bump is
trivial. C is cleaner behaviorally but adds a check that
complicates the operation description.

---

## Deferred-items impact preview

If items J1-J14 are accepted with the recommended options, the
following `deferred-items.md` updates will be needed:

- **`static-check-semantics`** (continued widening):
  - J4's `finding_class` enumeration (if option A) for retry
    classification.
  - J5's `build_parser` exemption in
    `check-public-api-result-typed`.
  - J11's schema-dataclass pairing walker behavior for
    transitively-referenced types (if option A) or the
    moved-to-dataclasses discipline (if option A via move).
- **`wrapper-input-schemas`**:
  - J6's `author` field extension to `proposal_findings.schema.json`
    or equivalent.
- **`skill-md-prose-authoring`**:
  - J3's template-prompt dispatch prose (runtime resolution via
    Read tool or wrapper helper).
  - J4's retry prose refinement naming the `finding_class`
    discriminator.
- **`task-runner-and-ci-config`**:
  - J10 inverse flag (if option A selected).
  - J11's dataclass moves (if option A).

No item requires a NEW deferred-items entry; all surface
widenings to existing entries.

## Request

Please walk through each item (J1-J14), pick a disposition
option (or propose a different resolution), and indicate
whether any downstream document or deferred-items entry also
needs updating.
