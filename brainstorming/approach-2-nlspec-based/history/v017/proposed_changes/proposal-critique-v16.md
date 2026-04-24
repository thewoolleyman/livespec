---
topic: proposal-critique-v16
author: Claude Opus 4.7 (1M context)
created_at: 2026-04-24T03:30:00Z
---

# Proposal-critique v16

A recreatability-and-cross-doc-consistency critique pass over v016
`PROPOSAL.md`, with targeted checks against `deferred-items.md` and
`python-skill-script-style-requirements.md`.

The critique is grounded in the recreatability test: could a
competent implementer, reading the current brainstorming docs alone
and the v016 PROPOSAL.md, produce a working livespec without being
forced to guess between conflicting rules or invent semantics that
the docs leave unspecified?

v016 was a 5-item cleanup pass (P1-P5) focused on
template-aware walk scoping, wrapper-owned config bootstrap,
reserve-suffix canonicalization, single-canonicalization
invariants, and the shebang-wrapper "6-statement" phrasing. Three
of those additions interact with pre-existing lifecycle and
enforcement rules in ways that produce new recreatability gaps,
which this v16 pass surfaces. Additionally, the v014 N1 `minimal`
template's pre-seed dialogue path (carried forward unchanged
since v014) has never been fully specified at the
template-resolution layer.

Findings in this pass:

- **Major gaps (3 items):** Q1-Q3
- **Significant gaps (2 items):** Q4-Q5
- **Smaller cleanups (4 items):** Q6-Q9

## Proposal: Q1 — Reserve-suffix canonicalization algorithm diverges between PROPOSAL.md and deferred-items.md

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`

### Summary

**Failure mode: malformation (self-contradiction between working
docs) / incompleteness (PROPOSAL.md algorithm is strictly smaller
than deferred-items.md's).**

v016 P3 introduced the `--reserve-suffix <text>` canonicalization
mechanism and said "the exact algorithm is codified in
`deferred-items.md`'s `static-check-semantics` entry." The two
documents now describe algorithmically distinct procedures.

PROPOSAL.md §"propose-change → Reserve-suffix canonicalization"
(lines ~1612-1631):

> canonicalization steps 1-3 (lowercase, non-`[a-z0-9]` → single
> hyphen, strip leading/trailing hyphens) apply to the full
> inbound topic hint AND separately to the supplied `<suffix>`
> string; step 4 truncates the non-suffix portion of the
> canonicalized hint to `64 − len(<canonicalized-suffix>)`
> characters; the canonicalized suffix is then re-appended
> verbatim.

`deferred-items.md` §"Reserve-suffix topic canonicalization"
(lines ~966-1011):

> 1. Canonicalize the inbound topic hint with steps 1-3 … call
>    this `<canonical-hint>`.
> 2. Canonicalize the `<suffix>` string … call this
>    `<canonical-suffix>`.
> 3. **If `<canonical-hint>` already ends in `<canonical-suffix>`,
>    strip the trailing suffix from `<canonical-hint>` before
>    truncation.** (This lets callers pass the hint either with
>    or without the suffix pre-attached.)
> 4. Truncate the resulting non-suffix portion to
>    `64 − len(<canonical-suffix>)` characters; **strip trailing
>    hyphens left behind by the truncation.**
> 5. Re-append `<canonical-suffix>` verbatim. …

Two concrete behaviors present in deferred-items.md but ABSENT
from PROPOSAL.md:

- **Pre-strip step** (deferred-items step 3). If a caller passes
  `"Claude Opus 4.7-critique"` as the hint with suffix
  `"-critique"`, deferred-items strips the trailing `-critique`
  first, producing `claude-opus-4-7` (15 chars) before re-append.
  PROPOSAL.md's description would NOT pre-strip; instead it would
  truncate `claude-opus-4-7-critique` (24 chars, fits in the
  55-char non-suffix budget) and re-append, producing
  `claude-opus-4-7-critique-critique` (33 chars) — a doubled
  suffix.
- **Post-truncation hyphen strip** (deferred-items step 4).
  If truncation lands in the middle of a word-boundary hyphen,
  the suffix would re-attach with a doubled hyphen. PROPOSAL.md
  doesn't specify this clean-up.

The deferred-items worked example at line ~1007:

> Input `"Claude Opus 4.7-critique"`, suffix `"-critique"` (suffix
> was pre-attached by caller) → canonical hint strips trailing
> `-critique` → `claude-opus-4-7` (15 chars) → no truncation →
> output `claude-opus-4-7-critique` (24 chars).

only produces that output under deferred-items's step-3 pre-strip
rule. PROPOSAL.md's text alone yields `claude-opus-4-7-critique-critique`.

A competent implementer reading PROPOSAL.md's bullet without
following the cross-reference to `deferred-items.md` will
implement the simpler algorithm and silently produce doubled
suffixes for any caller that pre-attaches the suffix — which
includes natural language inputs to `/livespec:critique` in
dialogue where the LLM says
"critique from Claude Opus 4.7-critique." This is a recreatability
defect because the doc users trust as authoritative (PROPOSAL.md)
is strictly less complete than the doc it delegates to.

### Motivation

The architecture-vs-mechanism discipline admits cross-doc
delegation: PROPOSAL.md names contracts, `deferred-items.md`
codifies algorithms. But when PROPOSAL.md states an algorithm
sketch at all, the sketch must not misrepresent the canonical
algorithm. Here PROPOSAL.md's sketch is both present AND
misleading.

### Proposed Changes

Pick one:

**Option A (Recommended).** Trim PROPOSAL.md §"propose-change →
Reserve-suffix canonicalization" to a terse architectural-
contract statement that names the invariants without sketching
the algorithm:

> `bin/propose_change.py` accepts an optional
> `--reserve-suffix <text>` flag (also exposed as a keyword-only
> parameter on the Python internal API used by `critique`'s
> internal delegation). When supplied, topic canonicalization
> guarantees that the resulting topic is at most 64 characters
> AND that the caller-supplied suffix is preserved intact at the
> end of the result, even when the inbound hint already ends in
> that suffix or when truncation would otherwise clip it. When
> `--reserve-suffix` is NOT supplied, canonicalization behaves
> exactly as v015 O3 defined. The empty-after-canonicalization
> `UsageError` (exit 2) rule continues to apply to the final
> composed result. The exact algorithm (pre-strip + truncate +
> hyphen-trim + re-append) is codified in `deferred-items.md`'s
> `static-check-semantics` entry.

This matches the architecture-vs-mechanism discipline already
applied to `anchor-reference-resolution` and many other
deferred-to-semantics items.

**Option B.** Expand PROPOSAL.md's description to include the
pre-strip and trailing-hyphen-strip steps verbatim, matching
`deferred-items.md` step-for-step.

Recommended: **A**, because it stops PROPOSAL.md from
duplicating the algorithm (the source of the current drift) and
returns it to the architecture-level discipline. B works but
re-introduces drift risk for future pass that touches one doc
but not the other.

## Proposal: Q2 — Pre-seed template resolution has no documented mechanism

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`

### Summary

**Failure mode: incompleteness.**

v010 J3 established `bin/resolve_template.py` as the
template-resolution seam for every non-seed sub-command, and
v011 K2 froze its contract: the wrapper walks upward from
`--project-root` looking for `.livespec.jsonc` (PROPOSAL.md
lines ~1095-1099). If `.livespec.jsonc` is not found, the
wrapper exits 3 (lines ~1121-1125).

v014 N1 added the pre-seed template-selection dialogue for
`minimal`-vs-`livespec`-vs-custom-path (PROPOSAL.md lines
~1427-1447). v016 P2 clarified that the wrapper (not the
SKILL.md prose) writes `.livespec.jsonc` before post-step
doctor-static.

The gap: in the pre-seed state (normal case), `.livespec.jsonc`
does NOT exist when `seed/SKILL.md` runs. The seed flow
requires the LLM to:

1. Prompt the user for a template choice.
2. Read the chosen template's `prompts/seed.md`.
3. Invoke that prompt to produce the `files[]` payload.
4. Invoke `bin/seed.py --seed-json <tempfile>`.

Step 2 requires the LLM to know the absolute path of the chosen
template's `prompts/seed.md`. `bin/resolve_template.py` CANNOT
be used pre-seed because it requires `.livespec.jsonc` to
exist. For `livespec` and `minimal` built-ins, the path is
`<plugin-bundle>/specification-templates/<name>/prompts/seed.md`,
but PROPOSAL.md never tells the LLM how to find
`<plugin-bundle>`. For a user-provided custom path, the LLM has
the relative path from dialogue, but still needs to resolve it
against the project root.

PROPOSAL.md §"Per-sub-command SKILL.md body structure" step 4
(lines ~240-249) prescribes the two-step `resolve_template.py` →
Read dispatch as THE mechanism for template-prompt invocation,
with no documented exception. `seed`'s SKILL.md prose is named
as a special case for the pre-seed dialogue (lines 1441-1447),
but the prompt-resolution mechanism for the pre-seed special
case is never specified.

This is a recreatability defect: two competent implementers will
not converge. One may extend `resolve_template.py` with a
`--template <value>` flag that bypasses the config-file lookup
(a contract break at the frozen-in-v1 seam). One may hardcode
`<plugin-bundle>` detection in `seed/SKILL.md` prose via a bash
incantation (e.g., `dirname "$(readlink -f "$(which claude)")"`,
or traversal from a known-relative-path anchor) — a fragile,
host-specific approach. One may require the user to manually
supply the template path even for built-ins (degrading the N1
UX).

The `template-exists` check's "non-seed sub-commands get exit 3
on missing config" behavior (PROPOSAL.md line 1446) cleanly
handles the post-seed world but leaves pre-seed unaddressed.

### Motivation

`seed` is the entry point for every new livespec-using project.
A pre-seed flow that relies on undefined behavior fails the
recreatability test at step one. N1 set up the architecture; the
resolution mechanism needs to follow.

### Proposed Changes

Pick one:

**Option A (Recommended).** Extend `bin/resolve_template.py`
with a `--template <value>` flag that, when supplied, bypasses
the `.livespec.jsonc` lookup entirely and resolves the given
value directly (built-in name → `<bundle-root>/specification-
templates/<name>/`; path → relative to `--project-root`). The
other existing flags and exit-code semantics stay unchanged.
`seed/SKILL.md` prose invokes
`bin/resolve_template.py --project-root . --template <chosen>`
and captures stdout per the normal two-step dispatch. The v11 K2
"v2+ extensibility shield" paragraph is extended to cover
`--template`'s stability contract.

This keeps template resolution in exactly one place
(`bin/resolve_template.py`), preserves the two-step dispatch
discipline, and avoids a pre-seed-specific SKILL.md prose
incantation.

**Option B.** Add a second helper wrapper
`bin/resolve_builtin_template.py` (or similar) that takes
`--template <name>` only and resolves built-in names without
touching `.livespec.jsonc`. Custom template paths pre-seed are
resolved directly by `seed/SKILL.md` prose against the
user-supplied relative path. Keeps `resolve_template.py`'s v11
K2 contract strictly unchanged.

**Option C.** Document in PROPOSAL.md that `seed/SKILL.md` prose
has a pre-seed special case where the LLM directly computes the
template path from the chosen value using the Bash tool and host
conventions (plugin-bundle detection via Claude Code's plugin
install directory). No new wrapper; the resolution algorithm
lives in skill prose.

Recommended: **A**, because it extends an existing seam under
its declared v2+ shield, keeps all template resolution in one
executable, and matches the existing two-step dispatch
discipline. B fragments resolution across two wrappers; C makes
template resolution a fragile skill-prose concern.

## Proposal: Q3 — Import-Linter raise-discipline contract over-restricts vs. authoritative English rule

### Target specification files

- `brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md` (see
  `static-check-semantics` §"Import-Linter contract semantics")

### Summary

**Failure mode: malformation (the authoritative English rule is
self-contradictory; the illustrative TOML enforces one
interpretation but the rule states both interpretations).**

The style doc §"Import-Linter contracts (minimum configuration)"
(lines ~612-680) specifies three contracts. The third
(raise-discipline imports) has an illustrative TOML:

```toml
[[tool.importlinter.contracts]]
name = "livespec-errors-raise-discipline-imports"
type = "forbidden"
source_modules = ["livespec"]
forbidden_modules = ["livespec.errors"]
ignore_imports = [
    "livespec.io.* -> livespec.errors",
    "livespec.errors.* -> livespec.errors",
]
```

and three English-language "authoritative rules" (lines
~661-680), rule 3 of which reads:

> 3. `livespec.errors.LivespecError` (and any of its subclasses)
>    MAY be imported only from `livespec.io.*` and
>    `livespec.errors` itself. Other modules must not import
>    `LivespecError` subclasses for raising.

The rule has two incompatible halves:

- **First sentence (absolute import restriction).** "MAY be
  imported only from `livespec.io.*` and `livespec.errors`
  itself." No purpose scoping.
- **Second sentence (purpose-scoped restriction).** "Other
  modules must not import `LivespecError` subclasses
  **for raising**." Importing for *annotating* is implicitly
  permitted.

The illustrative TOML enforces the absolute reading. The second
sentence is the weaker, purpose-scoped reading. Import-Linter
cannot encode "for raising" — its contracts operate on import
statements, not on subsequent usage.

Under the absolute reading:

- `livespec.doctor.run_static::main()` cannot type its final
  return value as `IOResult[FindingsReport, LivespecError]`
  (imports LivespecError).
- Per-check modules under `livespec/doctor/static/*.py` cannot
  declare `run(ctx) -> IOResult[Finding, E]` with `E` bound to
  `LivespecError` (imports LivespecError to declare the TypeVar
  bound, or imports a subclass for `IOResult[Finding,
  GitUnavailableError]`-typed handlers).
- `livespec.commands.*::main()` functions pattern-matching
  against `IOFailure(UsageError)` / `IOFailure(ValidationError)`
  cannot import those classes for the match pattern.

All of these are explicitly required elsewhere in the style doc
and PROPOSAL.md:

- PROPOSAL.md line ~1908: `run(ctx) -> IOResult[Finding, E]
  where E is any LivespecError subclass`.
- Style doc §"Structural pattern matching" HelpRequested example
  (lines ~1275-1291) pattern-matches against `IOFailure(err)`
  where `err` is a `LivespecError` instance; the containing
  module must import LivespecError for the exhaustiveness check
  to type correctly.
- Style doc §"Exit code contract" (lines ~1494-1509) says
  supervisors "emit `err.exit_code`" — access to
  `LivespecError.exit_code` requires the class to be imported
  for the narrowing.

Two competent implementers reading the current rule will
diverge:

- one implements the English rule's first sentence (absolute
  restriction) per the TOML, discovers the type errors above,
  and broadens `ignore_imports` to include
  `livespec.doctor.* -> livespec.errors` +
  `livespec.commands.* -> livespec.errors` +
  `livespec.validate.* -> livespec.errors` — at which point
  the raise-discipline contract restricts almost nothing useful;
- another implements the English rule's second sentence (import-
  for-raising restriction), gives up on Import-Linter for this
  contract, and leans on hand-written `check-no-raise-outside-io`
  to catch raise sites.

The v012 L15a disposition claimed Import-Linter replaces the
"import-surface portion of `check-no-raise-outside-io`." Under
the absolute reading the replacement over-reaches; under the
second-sentence reading Import-Linter isn't a valid replacement
at all and the import-surface portion should remain hand-written.

### Motivation

The three authoritative contracts are the invariants; the
illustrative TOML is one valid encoding. But the third
invariant is internally inconsistent, and the illustration
doesn't match either reading cleanly. This creates drift risk
on the most load-bearing architectural gate (`just
check-imports-architecture`).

### Proposed Changes

Pick one:

**Option A (Recommended).** Rewrite English rule 3 to match
what Import-Linter can actually enforce, and scope it to
"raising access" via the practical proxy of "no raise-statement
execution outside io/* and errors.py," acknowledging that the
import-surface proxy for raise-site checking is inherently
imperfect:

> 3. `LivespecError` raise-sites are restricted to
>    `livespec.io.*` and `livespec.errors` (enforced by the
>    hand-written `check-no-raise-outside-io` raise-site check).
>    `livespec.errors` MAY be imported from any module that
>    needs to reference `LivespecError` or a subclass in a type
>    annotation, `match` pattern, or attribute access (e.g.,
>    `err.exit_code`). No Import-Linter contract is used for
>    the raise-discipline import surface; the L15a
>    "replaces the import-surface portion of
>    check-no-raise-outside-io" claim is retracted.

The raise-discipline contract is removed from the illustrative
TOML (keeping only the purity and layered-architecture
contracts). The hand-written `check-no-raise-outside-io` covers
the raise-site portion fully.

**Option B.** Keep the absolute import restriction, but broaden
`ignore_imports` in the illustrative TOML to cover the known
legitimate import sites (at minimum:
`livespec.commands.* -> livespec.errors`,
`livespec.doctor.* -> livespec.errors`,
`livespec.validate.* -> livespec.errors` for `ValidationError`
returns). Rewrite English rule 3 to match the expanded
ignore-list.

**Option C.** Introduce an intermediate module
`livespec/errors_reexport.py` (under `livespec.io.*` lineage)
that re-exports `LivespecError` and its subclasses; other
modules import error types from the re-export module. The
original `livespec/errors.py` keeps the absolute restriction.

Recommended: **A**, because rule 3 is genuinely not
import-surface-enforceable via Import-Linter under either
reading without substantial ignore-list expansion that leaves
the contract empty of load-bearing work. Dropping the
Import-Linter portion and relying on the hand-written raise-
site check restores contract integrity and matches what the
purpose-scoped second sentence actually says. B preserves
Import-Linter coverage but forces the ignore-list to absorb
every downstream import of errors, which is operationally
equivalent to A in what it forbids (nothing) but noisier. C
adds a module layer whose only purpose is to launder the import
surface.

## Proposal: Q4 — Seed post-step recovery flow doesn't document that propose-change post-step also fails

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`

### Summary

**Failure mode: incompleteness / ambiguity.**

v014 N7 documented the seed post-step-failure recovery path
(PROPOSAL.md lines 1547-1570):

> 1. Review the fail Findings surfaced in stderr / skill-prose
>    narration.
> 2. Run `/livespec:propose-change --skip-pre-check <topic>
>    "<fix description>"` to file a proposed-change…
>    `--skip-pre-check` bypasses the pre-step doctor-static
>    that would otherwise trip the same findings…
> 3. Run `/livespec:revise --skip-pre-check` to process the
>    proposed-change and cut `v002` with the corrections.

The gap: `--skip-pre-check` bypasses ONLY the pre-step, not the
post-step (per §"Pre-step skip control" lines ~604-616 — the
flag pair is called `skip-pre-check` / `run-pre-check`, not
`skip-check`). propose-change's **post-step** doctor-static
still runs on the broken state and fails with the same findings
that tripped seed's post-step. propose-change therefore exits 3
even though its sub-command logic ran successfully (the
proposed-change file IS on disk — per PROPOSAL.md lines 562-566,
wrappers abort with exit 3 "after sub-command logic has already
mutated on-disk state").

This is expected behavior in the spec model, but:

- PROPOSAL.md doesn't tell the user to expect propose-change's
  exit 3 as success-in-context.
- The SKILL.md narration contract for exit 3 (lines ~281-284) is
  "surface the findings from the wrapper's stderr structlog
  line(s) and abort. The user is directed to the corrective
  action the finding describes. NOT retryable via template
  re-prompt." — which instructs the skill to treat exit 3 as an
  abort, not as a pass-through-to-revise signal.
- The N7 recovery flow reads as if propose-change will exit 0
  and the user will then run revise; the actual behavior is
  propose-change exits 3, THEN the user runs revise anyway.

Two competent implementers will diverge:

- one implements the literal recovery flow in SKILL.md prose and
  users hit the exit-3 abort narration, get confused, and
  abandon the recovery before running revise;
- another infers the partial-state-commit-and-proceed intent and
  writes bespoke SKILL.md narration for the propose-change
  post-step-3 case during seed recovery, which is fragile (the
  skill has to recognize the seed-recovery context from the
  caller).

There's also a secondary gap: the user is told to commit
partial state (line 565: "the user is instructed via findings
to commit the partial state and proceed"). `livespec` does not
write to git (line 480-481). Is the user expected to `git commit
-am …` manually between propose-change and revise? If yes, is
that commit required (for `out-of-band-edits` to pass on the
next invocation)? Not specified.

### Motivation

The seed recovery path is the only documented remediation route
for a seed-time post-step failure. If the documented flow
produces an abort-narration confusing enough that users don't
complete the recovery, the recoverability guarantee breaks
down.

### Proposed Changes

Pick one:

**Option A (Recommended).** Extend PROPOSAL.md §"seed →
Post-step doctor-static failure recovery" with an explicit
narration contract for the propose-change exit-3 case during
recovery, plus the git-commit obligation:

> ### Recovery flow narration contract
>
> Propose-change's own post-step doctor-static will trip the
> same findings that tripped seed's post-step, so propose-change
> also exits 3. This is expected: the sub-command logic has
> already written the proposed-change file to
> `<spec-root>/proposed_changes/`, and the partial-state
> commit-and-proceed pattern from §"Wrapper-side: deterministic
> lifecycle" applies. The user MUST:
>
> 1. Commit the partial state (the just-written proposed-change
>    file plus any earlier seed-written files) before running
>    revise, so that the `doctor-out-of-band-edits` check on the
>    next invocation does not trip the pre-backfill guard.
> 2. Run `/livespec:revise --skip-pre-check` to apply the
>    proposed-change and cut `v002`.
>
> Propose-change's SKILL.md prose MUST narrate the exit-3 path
> distinctly when the narrator can detect the
> seed-recovery-in-progress state (heuristic: no `vNNN` beyond
> `v001` exists AND pre-check was skipped). When that state
> cannot be detected, the generic exit-3 narration is used and
> the user is expected to recognize the recovery path from the
> v014 N7 narration seed's SKILL.md emitted earlier.

The `skill-md-prose-authoring` deferred entry is widened to
cover the dual narration contract.

**Option B.** Introduce a separate `--skip-post-check` /
`--run-post-check` flag pair that mirrors pre-step. seed's N7
recovery instruction becomes "propose-change --skip-pre-check
--skip-post-check" and "revise --skip-pre-check". Simpler for
users; but adds a whole new skip-axis that invites misuse.

**Option C.** Document that the recovery path is actually
"hand-author a proposed-change file via Edit, then revise
--skip-pre-check" — skip the propose-change step entirely. The
proposed-change file format is documented (§"Proposed-change
file format"), so a user or an LLM can write one directly.
Closes the ambiguity at the cost of divorcing recovery from
the normal propose-change flow.

Recommended: **A**, because it preserves the v014 N7 flow with
its existing tooling, explicitly names the partial-state-commit
step (which is currently implicit), and adds a narration
contract that helps the user recognize the exit-3-is-expected
case without adding a new flag surface. B's new flag pair is
a larger scope change than the problem warrants. C abandons
propose-change for recovery, which fragments the sub-command's
usage contract.

## Proposal: Q5 — Seed wrapper behavior when `.livespec.jsonc` is present-but-invalid

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`

### Summary

**Failure mode: ambiguity.**

v016 P2 codified that `bin/seed.py` writes `.livespec.jsonc` as
part of its deterministic file-shaping work (PROPOSAL.md lines
~1448-1462). The rule distinguishes two cases:

> The wrapper writes `.livespec.jsonc` BEFORE post-step
> doctor-static runs… If the file is already present and valid
> before the wrapper runs (an unusual but legal state), the
> wrapper reuses it without modification (validating against
> the config schema first) and the payload's `template` value
> MUST match the on-disk `template` value or the wrapper exits
> `2` with a `UsageError` describing the conflict.

Two implicit branches:

- `.livespec.jsonc` absent (the normal pre-seed case): write
  fresh from payload `template`.
- `.livespec.jsonc` present AND valid: reuse (plus
  consistency check).

The unhandled third case: **`.livespec.jsonc` is present but
malformed or schema-invalid.** The PROPOSAL.md text is silent.

Possible implementer interpretations:

1. Treat present-invalid as equivalent to absent and overwrite
   the broken file with a fresh skeleton. Risk: clobbers a user's
   in-progress manual edit.
2. Exit 3 with `PreconditionError`, directing the user to fix
   the config file manually before re-running seed. Preserves
   user intent but adds a failure mode seed's flow doesn't
   otherwise have.
3. Exit 2 with `UsageError` (extending the present-valid
   mismatch case to cover malformed too). Semantically incorrect
   — the user didn't pass a bad flag.

The §"Absence behavior" section at lines 939-946 distinguishes
"missing" (valid default behavior) from "present and malformed"
(doctor fails). But those semantics apply at the doctor layer.
Seed's special bootstrapping role is the unique edge case.

This also interacts with the non-doctor wrapper fail-fast rule
at lines ~1980-1985:

> bootstrap lenience is a doctor-static-only discipline. The
> non-doctor wrappers (`bin/seed.py`, `bin/propose_change.py`,
> etc.) continue to fail-fast on malformed `.livespec.jsonc`
> (exit 3 via `PreconditionError`); fixing the config is the
> user's first step in non-doctor flows…

That rule is directly authoritative for seed's present-invalid
case — but it's placed in doctor's §"Bootstrap lenience"
section rather than in §"seed," so a reader doing the seed
flow walkthrough may miss it.

Two competent implementers will not converge without explicit
seed-section handling.

### Motivation

`.livespec.jsonc` write-or-reuse ordering is the load-bearing
P2 invariant. The edge case must be pinned down in the same
section that documents the normal flow.

### Proposed Changes

Pick one:

**Option A (Recommended).** Add the explicit third-branch
handling to PROPOSAL.md §"seed" directly below the v016 P2
paragraph:

> If `.livespec.jsonc` is present but malformed (JSONC parse
> failure) or schema-invalid (parses but fails
> `livespec_config.schema.json`), the wrapper exits `3` with a
> `PreconditionError` citing the specific parse error or
> schema-violation path. The user's corrective action is to
> fix or delete the broken `.livespec.jsonc` before re-running
> seed; seed's idempotency refusal may also prevent re-running
> if template-declared target files already exist. This
> preserves the non-doctor fail-fast rule (see §"Doctor →
> Bootstrap lenience") and never silently overwrites a user's
> manual edit.

**Option B.** Treat present-invalid as equivalent to absent
and overwrite. The user's prior content is lost; rationale
would be "bootstrap is always wrapper-owned; invalid input is
discarded."

**Option C.** Leave the ambiguity unresolved and delegate to
`deferred-items.md`'s `wrapper-input-schemas` entry.

Recommended: **A**, because it applies the non-doctor fail-fast
rule explicitly in seed's section (where users will look),
avoids silent data loss, and makes the three-branch decision
tree explicit in one place. B's silent overwrite is a data-loss
hazard. C buries a load-bearing behavior in a deferred item.

## Proposal: Q6 — Payload-vs-config `template` mismatch exits `2` (UsageError), but the failure is semantically a precondition conflict (exit `3`)

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`

### Summary

**Failure mode: incorrectness (wrong exit code for the failure
category).**

PROPOSAL.md §"seed" line ~1459-1462 (v016 P2):

> If the file is already present and valid before the wrapper
> runs (an unusual but legal state), the wrapper reuses it
> without modification (validating against the config schema
> first) and the payload's `template` value MUST match the
> on-disk `template` value or the wrapper exits `2` with a
> `UsageError` describing the conflict.

Per the exit-code contract (PROPOSAL.md lines ~2190-2204 and
style doc §"Exit code contract" lines ~1418-1427):

- Exit `2`: "Usage error: bad flag, wrong argument count,
  malformed invocation."
- Exit `3`: "Input or precondition failed: referenced
  file/path/value missing, malformed, or in an incompatible
  state."

A payload-vs-on-disk-config mismatch is not a flag/arg-count
error — the wrapper's invocation was well-formed; the
mismatch is between two well-formed inputs in an incompatible
state relative to each other. That fits exit `3` exactly
("incompatible state").

`UsageError.exit_code = 2` is defined in `errors.py` (style
doc lines ~1449-1450). `PreconditionError.exit_code = 3`
(style doc lines ~1452-1453). The v016 P2 disposition
specifically chose `UsageError`, but the choice appears to
conflate "invocation was invalid" with "invocation was
valid but inputs disagree."

### Motivation

Exit-code discrimination is the LLM-facing classifier that lets
SKILL.md prose route retries-vs-aborts deterministically (per
v010 J4 rationale). Mis-categorizing precondition conflicts as
usage errors blurs the classifier.

### Proposed Changes

Pick one:

**Option A (Recommended).** Change the exit code to `3` and
the error class to `PreconditionError`:

> …the payload's `template` value MUST match the on-disk
> `template` value or the wrapper exits `3` with a
> `PreconditionError` describing the conflict.

**Option B.** Keep exit `2` / `UsageError` on the rationale
that "the payload's `template` field is a caller-supplied
argument, and supplying a value that conflicts with the
on-disk file is a caller error." Treat the payload as
argument-like rather than input-file-like.

Recommended: **A**, because the payload is structurally a
wire-format input (validated against `seed_input.schema.json`),
not a CLI-argument-like surface, and the mismatch is between
two validated inputs — the precondition category.

## Proposal: Q7 — Revision filename pairing is implicit for collision-suffixed proposed-changes

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`

### Summary

**Failure mode: ambiguity.**

§"revise" lines 1864-1867:

> Each processed proposal file is moved **byte-identical** from
> `<spec-root>/proposed_changes/` into
> `<spec-root>/history/vN/proposed_changes/<topic>.md`.
> Relative markdown links preserved.
>
> Each processed proposal gets a paired revision at
> `<spec-root>/history/vN/proposed_changes/<topic>-revision.md`,

`<topic>` is ambiguous when the proposed-change carried a
collision-suffix. For a proposed-change `foo-2.md` (second
collision), two readings of `<topic>-revision.md`:

- **Filename-stem reading.** `<topic>` = the full filename
  stem including collision suffix = `foo-2`. Revision file:
  `foo-2-revision.md`.
- **Canonical-topic reading.** `<topic>` = the canonical topic
  from front-matter (which v015 O3 + v016 P4 defines as
  excluding the `-N` collision suffix; see PROPOSAL.md lines
  ~2324-2331). Revision file: `foo-revision.md` (which would
  collide with the first-collision's revision).

The filename-stem reading is the only workable one (otherwise
multiple revisions collide), but it's not explicitly stated.

The `revision-to-proposed-change-pairing` doctor-static check
(line ~2089-2092) says "with the same topic in the same
directory" — which uses the word `topic` ambiguously again
(front-matter `topic` field value, or filename stem?).

### Motivation

Two implementers who read only the `<topic>-revision.md`
filename template will not agree on the pairing semantics when
collisions occur. The `proposed-change-topic-format` and
`revision-to-proposed-change-pairing` checks' enforcement rules
depend on the same disambiguation.

### Proposed Changes

Pick one:

**Option A (Recommended).** Add an explicit clarification in
PROPOSAL.md §"revise" and §"Proposed-change file format":

> Under collision disambiguation, the proposed-change filename
> stem includes the `-N` suffix (`foo-2.md`, `foo-3.md`, …).
> The paired revision's filename uses the full filename stem:
> `foo-2-revision.md`, `foo-3-revision.md`. This is distinct
> from the front-matter `topic` field, which carries the
> canonical topic WITHOUT the `-N` suffix (the suffix is
> filename-level disambiguation only).

Widen `deferred-items.md`'s `static-check-semantics` entry to
codify that `revision-to-proposed-change-pairing` walks
filename stems (not front-matter `topic` values) for pairing.

**Option B.** Restructure the filename convention so that
`-revision` always comes before the `-N` collision suffix:
`foo-revision-2.md`, `foo-revision-3.md`. Keeps the front-matter
`topic` ↔ filename-stem-before-revision alignment. But requires
more complex parsing for the pairing check and changes v014
N6's established "`foo-2.md`, `foo-3.md`" cadence mid-version.

Recommended: **A**, because it pins down the existing natural
reading without changing any user-visible filename convention
and clarifies that front-matter `topic` and filename stem are
related but distinct. B is a visible convention shift for
minor notational gain.

## Proposal: Q8 — Grammatical malformation at PROPOSAL.md line 853

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`

### Summary

**Failure mode: malformation (grammar typo).**

PROPOSAL.md line 853:

> The every doctor-static check's path references parameterize
> against `DoctorContext.spec_root` (per v009 I7)…

"The every" is not grammatical. This appears to be a residual
from a prior edit that combined "The" and "Every" without
removing one.

### Motivation

Pure cleanup. No semantic change; the intent is obvious. But
leaving it present makes future grep-based audits noisier.

### Proposed Changes

Pick one:

**Option A (Recommended).** Rewrite as:

> Every doctor-static check's path references are parameterized
> against `DoctorContext.spec_root` (per v009 I7)…

**Option B.** Leave as-is; accept the minor grammatical
imperfection.

Recommended: **A**. Trivial fix; no reason to leave it.

## Proposal: Q9 — `bin/doctor_static.py`'s project-root detection is not documented

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`

### Summary

**Failure mode: incompleteness.**

`bin/resolve_template.py` documents `--project-root <path>`
with default `Path.cwd()` (PROPOSAL.md lines ~1095-1099).
`bin/doctor_static.py` does not document how it detects the
project root in any of the following sections:

- §"doctor" (lines ~1886-1946);
- §"Pre-step skip control" (lines ~604-630, where
  `--skip-pre-check`/`--run-pre-check` handling is specified);
- §"Bootstrap lenience" (lines ~1948-1985).

`DoctorContext.project_root: Path` is listed among the required
fields (style doc §"Context dataclasses" lines ~340-348) but
the population mechanism is not specified. Implicitly it is
probably `Path.cwd()` with upward-walk to find
`.livespec.jsonc` (mirroring `resolve_template.py`), but
nothing pins this down.

Seed's wrapper has the same question and the same implicit
answer. Non-doctor wrappers (`propose_change.py`, `critique.py`,
`revise.py`, `prune_history.py`) similarly have no documented
project-root detection.

Two competent implementers will diverge:

- one implements `--project-root` on every wrapper matching
  `resolve_template.py`'s flag (explicit and uniform);
- another hardcodes `Path.cwd()` into every wrapper (silent;
  fails when the wrapper is invoked from a sibling directory);
- another invokes `resolve_template.py` first to get the
  project root transitively (adds an extra process hop per
  wrapper invocation).

### Motivation

Every wrapper that reads spec state needs to know the project
root. Leaving the detection mechanism unspecified means every
wrapper implements it slightly differently.

### Proposed Changes

Pick one:

**Option A (Recommended).** Add a project-root detection
contract to §"Sub-command dispatch and invocation chain" that
applies to every wrapper uniformly:

> Every wrapper that operates on project state
> (`bin/seed.py`, `bin/propose_change.py`, `bin/critique.py`,
> `bin/revise.py`, `bin/prune_history.py`,
> `bin/doctor_static.py`, `bin/resolve_template.py`) accepts
> `--project-root <path>` as an optional CLI flag with default
> `Path.cwd()`. The project root is used (a) to anchor
> `<spec-root>/` resolution and (b) by those wrappers that
> walk upward from it to find `.livespec.jsonc` (all of them
> except `bin/seed.py`, which does not yet have a
> `.livespec.jsonc` when it runs). The flag is uniform; the
> upward-walk logic lives in `livespec.io.fs`.

**Option B.** Leave the detection mechanism as implementer
choice, and add a note to §"seed" / §"doctor" / etc. stating
that project-root detection is a wrapper-internal
implementation detail.

**Option C.** Only document `--project-root` on
`bin/resolve_template.py` (the frozen-in-v1 surface) and have
every other wrapper invoke `resolve_template.py` transitively
to obtain the project root. Costly but maximally uniform.

Recommended: **A**, because it matches the v2+-extensibility
pattern already applied to `resolve_template.py` and gives
users a consistent flag surface across every wrapper.
Duplication of the flag declaration is minor compared to the
clarity gain. B leaves silent divergence risk; C is
architecturally pure but adds a process-per-invocation cost
that v016's careful-review passes have not budgeted.
