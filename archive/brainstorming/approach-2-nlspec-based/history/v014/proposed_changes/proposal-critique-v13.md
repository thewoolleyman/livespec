---
topic: proposal-critique-v13
author: Claude Opus 4.7 (1M context)
created_at: 2026-04-23T20:00:00Z
---

# Proposal-critique v13

A recreatability-and-integration-gap critique pass over v013
`PROPOSAL.md`, `python-skill-script-style-requirements.md`, and
`deferred-items.md`. Eleven items labelled with the NLSpec
failure-mode framework (ambiguity / malformation / incompleteness /
incorrectness), grouped by impact:

- **Major gap (1 item):** N1 — the largest recreatability /
  self-contradiction blocker.
- **Significant gaps (7 items):** N2–N8 — concrete recreatability /
  contract / self-consistency holes that would produce divergent
  implementations.
- **Smaller cleanup (3 items):** C1–C3 — cross-doc residue and
  drift the v013 careful-review passes did not catch.

The critique is grounded in the recreatability test: could a
competent implementer, reading only these three brainstorming docs
plus `livespec-nlspec-spec.md`, produce the v014 livespec plugin
without being blocked or forced to guess?

## Proposal: N1 — `.livespec.jsonc` absence behavior vs `resolve_template.py` exit-code contract contradict each other

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`

### Summary

**Failure mode: malformation (self-contradiction).**

Two adjacent sections in PROPOSAL.md assert incompatible
behaviors for the case where `.livespec.jsonc` is absent:

- §"Configuration: `.livespec.jsonc` — Absence behavior"
  (lines 887–893): *"If `.livespec.jsonc` is missing, the skill
  MUST behave as if it contained the schema defaults above."*
  The default template is `"livespec"` (built-in), so the skill
  should proceed with the built-in template when the config file
  is absent.
- §"Template resolution contract (`bin/resolve_template.py`) —
  Exit codes" (lines 1068–1072): *"`3` on any of
  {.livespec.jsonc not found above `--project-root`, malformed,
  schema-invalid, resolved path missing, resolved path lacks
  `template.json`}"*. Per this rule, missing `.livespec.jsonc`
  produces exit 3 — the sub-command's SKILL.md prose treats it as
  a precondition failure and aborts.

Per-sub-command SKILL.md prose (per v010 J3, v011 K2, and
§"Per-sub-command SKILL.md body structure" step 4) invokes
`bin/resolve_template.py` via Bash as the FIRST step before any
wrapper invocation. If `resolve_template.py` exits 3 on a missing
`.livespec.jsonc`, every sub-command aborts before sub-command
logic runs — including `seed`, which is the sub-command whose
explicit job is to CREATE `.livespec.jsonc` from defaults.

The two implementations diverge concretely:

- **Implementation A** (follow §"Absence behavior"): missing
  `.livespec.jsonc` → `resolve_template.py` emits the built-in
  `livespec/` template path, exit 0. Sub-commands proceed.
- **Implementation B** (follow §"Template resolution contract"):
  missing `.livespec.jsonc` → exit 3. Sub-commands cannot run,
  including `seed` (which would then be unable to bootstrap a
  new project).

This is never intentional; one of the two rules is wrong.

### Motivation

`.livespec.jsonc`'s absence-behavior rule is load-bearing for
the seed-on-fresh-project workflow (the first thing a user does
is invoke `/livespec:seed`, BEFORE `.livespec.jsonc` exists).
`resolve_template.py`'s exit-3-on-absence makes that workflow
impossible. The contradiction forces an implementer to pick one
side silently, and different picks produce incompatible
implementations.

### Proposed Changes

Three candidate resolutions — the interview will pick one:

**Option A (recommended):** `resolve_template.py` falls back to
default config values (template=`"livespec"`,
`template_format_version=1`) when `.livespec.jsonc` is absent,
emits the built-in template path, exits 0. The exit-code
contract updates to remove "not found" from the exit-3 list;
exit-3 now covers only "malformed / schema-invalid / resolved
path missing / resolved path lacks `template.json`". Matches
§"Absence behavior" which is the older and more fundamental
rule. (Reason recommended: preserves the seed-on-fresh-project
workflow without special-casing `seed`.)

**Option B:** `resolve_template.py` exits 3 on missing
`.livespec.jsonc`; every sub-command except `seed` fails fast.
`seed`'s SKILL.md prose skips the `resolve_template.py` step
entirely and uses a hard-coded built-in `livespec/` path at
seed-time only. §"Absence behavior" narrows to "applies once
`.livespec.jsonc` has been seeded". Forces a seed-specific
escape hatch in SKILL.md prose.

**Option C:** `resolve_template.py` exits 3 on missing
`.livespec.jsonc`; `seed`'s wrapper is special-cased to NOT
invoke `resolve_template.py` and instead load built-in defaults
internally. Every other sub-command still fails fast on missing
config. Slightly cleaner than Option B but introduces seed-
wrapper bootstrap asymmetry.

---

## Proposal: N2 — `schemas/dataclasses/finding.py` vs three-way `check-schema-dataclass-pairing` contradict implementer-choice on `finding.schema.json`

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`

### Summary

**Failure mode: malformation (self-contradiction).**

v010 J11 moved `Finding` from `doctor/finding.py` into
`schemas/dataclasses/finding.py` with the note that "Implementer
choice whether `finding.schema.json` is a standalone schema OR
the `Finding` shape is embedded as the `items` schema of
`doctor_findings.schema.json`'s `findings` array (either is
acceptable; check must pass either way)." — codified in the
v013 `deferred-items.md` `static-check-semantics` entry around
line 480-490.

v013 M6 widened `check-schema-dataclass-pairing` to a strictly
three-way walker: *"for every `schemas/*.schema.json`, verifies
a paired dataclass at `schemas/dataclasses/<name>.py` … AND a
paired validator at `validate/<name>.py` exists; … `check-
schema-dataclass-pairing` enforces drift-free pairing in all
three directions … every dataclass has matching schema +
validator"* (style doc, lines 277–285).

These are incompatible:

- If the implementer chooses "embedded" (no standalone
  `finding.schema.json`), then `schemas/dataclasses/finding.py`
  has no paired schema at `schemas/finding.schema.json` and no
  paired validator at `validate/finding.py`. The three-way
  walker's "dataclass without schema or validator" branch
  fails.
- If the implementer chooses "standalone", then three artifacts
  (`finding.schema.json`, `schemas/dataclasses/finding.py`,
  `validate/finding.py`) must all exist and pair — doable, but
  now implementer "choice" collapses to only one option.

Either the three-way check's strict symmetry must carry an
explicit exemption for `Finding`, OR the implementer-choice on
`finding.schema.json` must be closed (standalone mandatory), OR
`Finding` must move out of the `schemas/dataclasses/` walked
tree.

### Motivation

`Finding` is a load-bearing payload type — every doctor-static
check emits one. v010 J11 deliberately chose to co-locate it
with `DoctorFindings` under `schemas/dataclasses/` so the
pairing check could enforce one discipline across both. v013
M6 tightened the pairing check to three-way without revisiting
the J11 implementer-choice on the `Finding` schema. The
interaction creates either a stale allowance or a stale strict
rule; which side repairs depends on v014.

### Proposed Changes

Three candidate resolutions:

**Option A (recommended):** Close the implementer choice:
`schemas/finding.schema.json` and `validate/finding.py` are
both REQUIRED in v1. The three-way pairing check's symmetry
remains strict. Deferred-entry `static-check-semantics`
§`check-schema-dataclass-pairing` drops the "Implementer
choice" language. Rationale: the symmetry is the load-bearing
guardrail; one concrete choice is cleaner than an
exemption. (Reason recommended: keeps check-semantics
monotonic, avoids carving out the single "special" dataclass.)

**Option B:** Exempt `finding.py` from the three-way check
when `finding.schema.json` is absent AND the `Finding` shape
is embedded in `doctor_findings.schema.json`'s `items`. The
check gains a specific allowlist-by-name exemption. Preserves
v010 J11's implementer choice. Costs: one more narrow
exemption in the check source.

**Option C:** Move `Finding` out of
`schemas/dataclasses/finding.py` into `livespec/doctor/
finding.py` or `livespec/schemas/finding.py` (outside the
`dataclasses/` walked tree). The three-way check's scope no
longer covers `Finding`, so the "dataclass without schema"
branch doesn't fire. Costs: re-opens the v010 J11
co-location decision.

---

## Proposal: N3 — Doctor-static orchestrator bootstrap when `.livespec.jsonc` is malformed or absent is not codified

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`

### Summary

**Failure mode: incompleteness.**

PROPOSAL.md §"doctor — Static-phase structure" describes the
doctor-static orchestrator as running every registered check
against a `DoctorContext`. The `DoctorContext` dataclass (style
doc §"Context dataclasses", lines 326–340) has a `config:
LivespecConfig` field populated from the parsed and
schema-validated `.livespec.jsonc`, and a `template_root: Path`
field populated from the resolved template path.

But the very first doctor-static check is `livespec-jsonc-valid`,
whose entire job is to report on `.livespec.jsonc`'s validity.
Per the v011 K10 domain-failure-to-fail-Finding discipline,
when `.livespec.jsonc` is malformed or schema-invalid, the
check MUST emit `IOSuccess(Finding(status="fail", ...))` rather
than `IOFailure(err)`, so doctor-static preserves its invariant
of "never exit 4" and surfaces the issue through the Findings
channel.

Neither PROPOSAL.md nor the style doc codifies how the
orchestrator builds `DoctorContext` on a malformed or absent
`.livespec.jsonc` so that `livespec-jsonc-valid` can run AT ALL.
Two plausible implementations diverge:

- **Implementation A:** Orchestrator loads `.livespec.jsonc`
  strictly before building `DoctorContext`. If loading fails,
  the orchestrator emits `IOFailure(PreconditionError)`,
  exiting 3 with no Findings. `livespec-jsonc-valid` never
  runs as a check — its error becomes an opaque
  precondition-error abort.
- **Implementation B:** Orchestrator loads `.livespec.jsonc`
  leniently, falls back to defaults when absent or malformed,
  builds `DoctorContext` with a partially-populated config
  (plus a flag indicating the fallback), runs all checks
  including `livespec-jsonc-valid`, which now emits a fail
  Finding citing the specific schema violation or parse error.
  Exit 3 via the supervisor's fail-Finding path.

Both implementations pass `just check`; neither is pinned by
the brainstorming docs. The difference materially affects
user-visible output (opaque stderr structlog line vs
structured JSON Finding on stdout).

Separately, the same question applies to template-root
resolution: if `template.json` is malformed, does the
orchestrator fail early or does `template-exists` get to
emit a fail Finding?

### Motivation

The fail-Finding discipline is the v011 K10 invariant — it
codifies that domain-meaningful failures (validation,
missing file, permission-denied) surface as structured Findings
rather than supervisor-level `IOFailure`. A doctor-static
orchestrator that can't build its own `DoctorContext` without
successfully loading every subsequent-check input defeats the
invariant for the bootstrap-critical inputs.

This is a recreatability blocker for `livespec-jsonc-valid`
and `template-exists` specifically.

### Proposed Changes

Two candidate resolutions:

**Option A (recommended):** Codify the lenient-bootstrap
discipline in PROPOSAL.md §"Static-phase structure" (near
lines 1586–1610): the orchestrator MUST construct
`DoctorContext` with best-effort defaults when
`.livespec.jsonc` is absent, malformed, or schema-invalid, so
that `livespec-jsonc-valid` can run and emit a fail Finding
rather than aborting the orchestrator. Same discipline
applies to `template.json` → `template-exists`. A new
DoctorContext field (e.g., `config_load_status: Literal["ok",
"absent", "malformed", "schema_invalid"]`) preserves the
fallback reason for the check. Add a `static-check-semantics`
deferred-entry subsection codifying the bootstrap semantics.
(Reason recommended: preserves K10 invariant; gives every
check a fair chance to emit a Finding.)

**Option B:** Codify the strict-bootstrap discipline: if
`.livespec.jsonc` cannot be parsed and schema-validated, the
orchestrator emits `IOFailure(PreconditionError)` and exits
3 with a structured-error stderr line that names the file
and the parse/validation failure. The `livespec-jsonc-valid`
check exists for the case where `.livespec.jsonc` IS valid
but the user wants to confirm it; malformed cases are
reported through the supervisor's error channel. `template-
exists` follows the same pattern. K10's fail-Finding
discipline applies only to non-bootstrap checks. Drops a
small amount of user-output uniformity.

---

## Proposal: N4 — `template-exists` check does not validate `template.json`-declared prompt file existence

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`

### Summary

**Failure mode: incompleteness.**

PROPOSAL.md §"Static-phase checks — `template-exists`"
(lines 1674–1680) states: *"The active template (built-in or
at the configured path) exists and has the required layout
(`template.json`, `prompts/`, `specification-template/`).
`template.json`'s `template_format_version` matches
`.livespec.jsonc`'s `template_format_version` and is supported
by livespec."*

The check validates directory-layout presence (`prompts/`,
`specification-template/`), but not the REQUIRED per-prompt
files inside `prompts/`:

- Per §"Template directory layout (MUST)" (lines 957–1011):
  *"`prompts/seed.md`, `prompts/propose-change.md`,
  `prompts/revise.md`, and `prompts/critique.md` are
  REQUIRED."*
- Per §"Template resolution contract" and v011 K5:
  `template.json` MAY declare
  `doctor_llm_objective_checks_prompt: string | null` and
  `doctor_llm_subjective_checks_prompt: string | null`. When
  the template declares a non-null path, the prompt file
  MUST exist at that path.
- Per v011 K5: `template.json` MAY declare
  `doctor_static_check_modules: list[string]`. Each listed
  path MUST resolve to a loadable Python module.

None of these file-existence invariants are enforced by any
doctor-static check. A missing prompt file or module manifests
only at LLM-runtime (Read tool errors) or at doctor-static
orchestrator load-time (`importlib` failure), well after
doctor-static has already reported "pass" for this template.

### Motivation

`template-exists` is the user's first line of defense against
"template is broken" errors. A user who adopts a custom template
with a mis-typed path in `template.json` gets a pass from
`template-exists` (the directory structure looks fine), then
sees an LLM-runtime error several sub-commands later. The
static check should catch this immediately.

### Proposed Changes

Two candidate resolutions:

**Option A (recommended):** Widen `template-exists` to check
all four required prompt files (`prompts/seed.md`, `prompts/
propose-change.md`, `prompts/revise.md`, `prompts/critique.md`)
and, when `template.json` declares non-null values for
`doctor_llm_*_checks_prompt` or non-empty list for
`doctor_static_check_modules`, verify each referenced path
exists. A missing file is a fail Finding naming the offending
`template.json` field and the missing path. (Reason
recommended: preserves doctor-static's "catch it early" value
proposition; load is trivially fast; diagnostics are
actionable.)

**Option B:** Keep `template-exists` scope narrow. Add a new
doctor-static check `template-files-referenced` specifically
for the `template.json`-declared file paths. Slightly more
modular but creates two checks where one would do.

**Option C:** Leave file-existence check to LLM-runtime
(skill prose's Read tool) and orchestrator-load-time
(`importlib` module load). User discovers broken paths
sub-command by sub-command. Not recommended — violates the
"static phase catches what can be caught statically"
principle.

---

## Proposal: N5 — Author identifier form / sanitization is not codified, breaking filename safety

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`

### Summary

**Failure mode: ambiguity.**

The resolved `author_llm` value — per the unified precedence
CLI → env var → payload → `"unknown-llm"` — flows into two
filesystem-visible surfaces:

1. **Critique topic slug.** PROPOSAL.md §"critique" (lines
   1438–1440, 1442, 1447): *"The resolved author value is used
   … as the topic suffix. … internally to `propose_change`'s
   Python logic with topic `<resolved-author>-critique`"* and
   *"If a file with topic `<resolved-author>-critique` already
   exists, …"*. The topic becomes the filename at
   `SPECIFICATION/proposed_changes/<resolved-author>-critique.md`.
2. **Front-matter `author_llm` / `author` field.** YAML
   front-matter values, parsed by the restricted-YAML parser
   (`parse/front_matter.py`) as JSON-compatible scalars; the
   value propagates into `history/vNNN/proposed_changes/…`
   files and is queryable for audit.

The LLM's self-declared `author` (e.g., `Claude Opus 4.7 (1M
context)`, `claude-opus-4-7`, `GPT-5.2`, `some-user@example.com`,
`Human: Alice`, …) is unconstrained. There is no schema
pattern, wrapper normalization, or recommended shape codified
beyond the `livespec-` convention-only-prefix (v011 K9). Two
concrete implementation-divergence points:

- **Filesystem safety.** An LLM that self-declares `Claude
  Opus 4.7 (1M context)` creates a file at
  `SPECIFICATION/proposed_changes/Claude Opus 4.7 (1M context)-
  critique.md`. Spaces, parens, dots are legal on Unix but
  hostile to markdown links, URL encoding, and the
  `anchor-reference-resolution` check's slug algorithm.
- **Consistency across runs.** The same LLM may self-declare
  `Claude Opus 4.7` on one invocation, `claude-opus-4-7` on the
  next, producing divergent `author_llm` values for
  semantically identical authors. Audit-trail continuity
  suffers.

### Motivation

The topic-slug-from-author path is a NewType-level
boundary: `Author` (free-form string) flows into `TopicSlug`
(filesystem-safe kebab-case identifier). The `livespec/
types.py` L8 NewType discipline makes this distinction
explicit but does not codify the conversion rule.

This is recreatability-blocking for `critique`'s filename-
generation logic.

### Proposed Changes

Three candidate resolutions:

**Option A (recommended):** Codify an author-identifier
normalization rule in PROPOSAL.md §"propose-change → Author
identifier resolution" applying uniformly across
propose-change / critique / revise: the resolved author is
transformed to a filesystem-safe slug for filename use
(topic suffix), while the original form is preserved in
front-matter. The transformation rule: lowercase; non-
[a-z0-9] chars replaced with single hyphens; leading/
trailing hyphens stripped; collapse multi-hyphens; truncate
to 64 chars. Implemented in `livespec.commands.propose_change`.
Codify the same rule in `deferred-items.md`'s
`static-check-semantics` entry so the topic-derivation
semantics are testable. (Reason recommended: maps naturally
onto GFM's slug algorithm already used elsewhere in
livespec; minimal new surface area.)

**Option B:** Restrict LLM self-declaration to a schema
pattern matching `^[a-z0-9][a-z0-9-]*[a-z0-9]$` (kebab-case
only). `proposal_findings.schema.json` and
`revise_input.schema.json` reject payloads with
non-matching `author` fields via schema validation (exit 4,
retryable). Delegates normalization to the LLM. Tighter but
increases retry frequency.

**Option C:** Leave form unconstrained; require LLM
discipline via SKILL.md prose to produce kebab-case.
Weakest guardrail — relies on LLM instruction-following.

---

## Proposal: N6 — Topic collision disambiguation suffix is not codified

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`

### Summary

**Failure mode: ambiguity.**

PROPOSAL.md §"propose-change" (lines 1408–1411) and §"critique"
(lines 1447–1449) both state: *"If a file with topic `<topic>`
already exists, the skill MUST auto-disambiguate by appending a
short suffix. No user prompt for collision."*

"A short suffix" is not codified. Three plausible
implementations produce visibly different filenames for the
same user action:

- `foo.md`, `foo-1.md`, `foo-2.md` (monotonic counter).
- `foo.md`, `foo-20260423T200000Z.md` (UTC timestamp).
- `foo.md`, `foo-5k3j.md` (short hash / random suffix).

Each is implementable, each is "short" by some reading, each
produces a different on-disk artifact for the same flow. Two
implementations of livespec produce different audit trails for
the same observable sub-command sequence.

This cascades to `revise`-time ordering semantics: §"revise"
(lines 1466–1470) says proposals are processed in YAML
`created_at` front-matter order with "lexicographic filename
as fallback on tie." A counter-suffix and a timestamp-suffix
place different files first in the tie-breaker path.

### Motivation

Small surface gap, but it's load-bearing for: git diff
reproducibility (users committing the same sequence of
`propose-change` invocations produce different commits); the
`revise`-order tie-breaker; and heading-coverage-registry
entries keyed on filenames.

### Proposed Changes

Two candidate resolutions:

**Option A (recommended):** Codify a UTC-timestamp suffix:
`<topic>-<UTC-ISO-8601-seconds>.md` (e.g.,
`foo-20260423T200000Z.md`). Human-readable; monotonically
ordered by time; filesystem-safe; does not carry implicit
counters that couple to prior invocations. PROPOSAL.md's
`propose-change` and `critique` sections are updated to
codify the exact form. (Reason recommended: matches the
existing ISO-8601 timestamp convention used elsewhere in
livespec — `created_at` YAML front-matter, `out-of-band-edit-
<UTC-seconds>.md` filename form in the `out-of-band-edits`
check at lines 1734–1735.)

**Option B:** Codify a monotonic counter: `foo.md`,
`foo-1.md`, `foo-2.md`. Compact, human-friendly. But requires
the wrapper to scan existing files to determine the next
counter value, which is a race condition if two
`propose-change` invocations interleave. livespec is
single-process sync so this is mostly theoretical, but the
UTC timestamp sidesteps it entirely.

---

## Proposal: N7 — Post-step doctor-static failure recovery after `seed` is a dead-end

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`

### Summary

**Failure mode: incompleteness.**

PROPOSAL.md §"Sub-command lifecycle orchestration — Wrapper-side:
deterministic lifecycle" (lines 544–553): *"On any `status:
'fail'` finding from post-step, the wrapper aborts with exit 3
after sub-command logic has already mutated on-disk state (the
user is instructed via findings to commit the partial state and
proceed)."*

For `seed`, this specific recovery path is a dead-end:

1. `seed` is exempt from pre-step but runs post-step doctor-
   static (lines 555–561).
2. `seed`'s sub-command logic writes template-declared files
   and creates `history/v001/`.
3. Post-step doctor-static runs against the just-written
   state; one or more checks emit `status: "fail"` (e.g.,
   `bcp14-keyword-wellformedness` finds a typo in the LLM's
   generated spec content; `gherkin-blank-line-format` finds
   a malformed scenario block; `anchor-reference-resolution`
   finds a dangling link).
4. Wrapper exits 3. `SPECIFICATION/` and `history/v001/` are
   on disk but in a state that fails doctor-static.
5. User is told: "commit the partial state and proceed."
   Proceed to what?
   - Re-running `seed` — blocked by seed's idempotency refusal
     (lines 1338–1344: "if any template-declared target file
     already exists at its target path, `seed` MUST refuse").
   - Running `propose-change` or `critique` — requires pre-
     step doctor-static to pass, which it doesn't.
   - Manually editing `SPECIFICATION/` — sidesteps the
     governance the skill exists to provide; falls into
     `out-of-band-edits` backfill territory.

The user is stuck. There is no codified recovery path from
"seed wrote files, post-step failed."

The same dead-end partially affects `propose-change` and
`critique` (which can fail post-step after writing a
proposed-change file), but those have a recovery path:
delete the offending file and re-run. `seed`'s write set is
broad enough that deletion isn't a single-file operation.

### Motivation

seed's failure mode is load-bearing: it's the bootstrap
sub-command and its output is the foundation for every
subsequent invocation. "commit the partial state and proceed"
papers over a real recovery-path gap.

### Proposed Changes

Three candidate resolutions:

**Option A (recommended):** Document a seed-specific recovery
mechanism: if `seed`'s post-step fails, the user MAY run
`/livespec:revise` against the auto-created `history/v001/
proposed_changes/seed.md` (which already exists post-seed) to
iterate the seed content through a normal proposed-change →
revision cycle, cutting `v002` with the corrected content.
PROPOSAL.md §"seed" gains a "post-step failure recovery"
subsection explaining this. Requires `revise` to accept
being invoked when `SPECIFICATION/proposed_changes/` is empty
BUT the prior `seed.md` proposal is already in
`history/v001/proposed_changes/`, which it normally doesn't
— so this option also relaxes `revise`'s "empty proposed_
changes → fail hard" rule to: "fail hard only when both
`SPECIFICATION/proposed_changes/` is empty AND
`history/v001/proposed_changes/seed.md` has NOT been through
a prior revise iteration." (Reason recommended: reuses
existing machinery; preserves governance discipline; gives
seed-failure a natural next step.)

**Option B:** Add a `seed`-specific "force" flag (`--force-
reseed`) that bypasses idempotency refusal and overwrites
existing files. Destructive; requires user confirmation; sets
`disable-model-invocation: true`-like semantics on the flag.
Simpler but reintroduces re-seed's "obliterate prior state"
risk that the idempotency rule exists to prevent.

**Option C:** Narrow post-step doctor-static's scope after
`seed` to only the SET of checks that would pass on
template-generated content. Checks like `bcp14-keyword-
wellformedness` and `gherkin-blank-line-format` (which
inspect LLM-generated content) are SKIPPED on post-step
after seed. User gets a pass-Finding even with malformed
content; the issue surfaces only on the next `doctor`
invocation. Less safe; silently defers quality gates.

---

## Proposal: N8 — `prune-history` argument contract contradicts pre-step skip flags

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`

### Summary

**Failure mode: malformation (self-contradiction).**

PROPOSAL.md §"prune-history" (lines 1539–1548) states:
*"Accepts no arguments in v1."*

PROPOSAL.md §"Sub-command lifecycle orchestration — Pre-step
skip control" (lines 594–601) states: *"The wrapper accepts a
mutually-exclusive `--skip-pre-check` / `--run-pre-check` flag
pair for sub-commands that have a pre-step (`propose-change`,
`critique`, `revise`, `prune-history`)."*

`prune-history` is in both lists. If §"prune-history" means
`bin/prune_history.py` accepts no arguments, the `--skip-pre-
check` / `--run-pre-check` flag pair mentioned in §"Pre-step
skip control" cannot be accepted. Conversely, if the flag pair
is accepted, §"prune-history" is wrong.

### Motivation

prune-history is destructive (`disable-model-invocation:
true`). Its pre-step skip behavior is concretely important —
a user whose config has `pre_step_skip_static_checks: true`
may want to force `--run-pre-check` before pruning to
double-check the pre-prune state. The flag pair needs to work
for prune-history.

### Proposed Changes

One candidate resolution (others are inferior):

**Option A (recommended):** Update PROPOSAL.md §"prune-
history" line 1543 from "Accepts no arguments in v1" to
"Accepts only the mutually-exclusive `--skip-pre-check` /
`--run-pre-check` flag pair per §"Pre-step skip control"; no
other arguments in v1." Resolves the contradiction in favor
of §"Pre-step skip control" (which is the more recent and
fully-specified discipline). (Reason recommended: the flag
pair is architecturally uniform across pre-step-having
sub-commands; removing prune-history from that uniformity
would be a regression.)

---

## Proposal: N9 — No end-to-end / harness-level integration test requirement (added mid-interview)

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`

### Summary

**Failure mode: incompleteness.**

Surfaced mid-interview during the N1 discussion, once the user
confirmed that a second built-in template (`minimal`) would be
brought into v1 scope. With two built-ins and a single-file
`minimal` template as a deliberate minimal-example shape, the
natural use of `minimal` is as the target of the top-of-
the-testing-pyramid end-to-end integration test.

The current proposal has NO such test requirement. §"Testing
approach" (PROPOSAL.md lines 2026–2202) and style doc §"Testing"
(lines 991–1128) cover:

- `tmp_path`-scoped per-module contract tests.
- Per-spec-file rule-coverage tests (rules stated in spec files
  end-to-end *at the Python-code level*).
- Property-based tests on `parse/` and `validate/` via Hypothesis.
- Mutation testing via mutmut as release-gate.
- Meta-tests: wrapper-shape, heading-coverage-drift.
- 100% line + branch coverage across the Python surface.

None of these exercise livespec as a USER sees it: Claude Code
loading the plugin, invoking a SKILL.md, the LLM interpreting
prose, the wrapper chain writing to disk, doctor running
pre/post. The wrapper chain is tested in isolation
(`tests/bin/test_<cmd>.py`) but never as a full user workflow.

DoD #14 mentions *"livespec dogfoods itself: `<project-root>/
SPECIFICATION/` exists, was generated by `livespec seed`, has
been revised at least once … and passes `livespec doctor`
cleanly"* — a one-time bootstrap criterion for livespec's own
state, not an automated, reproducible, CI-gated test.

The gap is a classic "integration-level failure-mode blind
spot": per-module tests can all pass while harness-level
invocation breaks (SKILL.md prose mis-matches wrapper argv;
template prompts produce JSON that fails schema validation in
ways unit tests don't catch; the dogfood symlink breaks on a
fresh clone; skill discovery doesn't see the plugin;
`resolve_template.py`'s stdout is consumed wrong by SKILL.md
prose). The `minimal` template from N1 is the natural test
shape — single-file spec, minimal prompts, fast to exercise.

### Motivation

A required passing end-to-end integration test closes the
harness-level gap and gives dogfooding a mechanical gate.
Without it, every cross-layer behavior (SKILL.md prose ↔
wrapper ↔ template prompt ↔ LLM ↔ doctor) is verified only by
manual use.

### Proposed Changes

N9's shape depends on four interacting design dimensions, each
resolved via a separate interview turn:

**Dimension 1: LLM determinism.**

- **D1-a (stub/replay):** LLM layer is stubbed or replayed.
  Pre-canned JSON payloads stand in for LLM output. Fully
  deterministic; fits per-commit cadence; doesn't test the
  real prompt→JSON pipeline end-to-end.
- **D1-b (live, release-gate only):** Real LLM invocation via
  Claude Code against real API. Nondeterministic; requires
  LLM credentials in CI. Assertions scoped to structural
  invariants (file existence, schema validity, exit codes)
  rather than content details. Release-gate cadence (like
  `check-mutation`).
- **D1-c (hybrid):** Deterministic stub/replay tier at
  per-commit cadence AND live-LLM tier at release-gate
  cadence. Most coverage but most machinery.

**Dimension 2: Harness scope.**

- **D2-a (Claude Code only for v1):** The test invokes
  Claude Code as the sole harness. Matches the v1 plugin
  scope (PROPOSAL.md §"Runtime and packaging — Plugin
  delivery" v1 is Claude-Code-only).
- **D2-b (generic harness interface):** Define a harness-
  abstraction test layer so v2+ harnesses (opencode,
  pi-mono) drop in. More scope for v1; matches the
  "forward-looking rationale" pattern already used for
  scenarios.md holdouts.

**Dimension 3: Cadence.**

- **D3-a (per-commit, deterministic only):** E2E test runs
  on every commit but only in deterministic mode. Pairs
  with D1-a or D1-c.
- **D3-b (release-gate only):** E2E test runs only on
  release-tag CI (like `check-mutation`). Pairs with D1-b.
- **D3-c (both):** Per-commit deterministic tier + release-
  tag live-LLM tier. Pairs with D1-c.

**Dimension 4: Coverage surface (what the E2E test drives).**

- **D4-a (happy path only):** `seed → propose-change →
  critique → revise → doctor → prune-history` against the
  `minimal` template. Asserts on structural invariants at
  each step (expected files present, schemas valid, exit
  codes correct). Doesn't test error-recovery paths.
- **D4-b (happy path + key error paths):** Happy path
  plus: retry-on-exit-4 (schema-invalid LLM payload);
  doctor-static fail-then-fix; prune-history idempotency.
  Broader but more fixtures to maintain.
- **D4-c (full matrix):** Happy path × both built-in
  templates (`livespec` + `minimal`) × both harness modes
  (D1). Maximal coverage; most expensive.

Resolution codifies all four dimensions in PROPOSAL.md
§"Testing approach" plus a new deferred-items entry
`end-to-end-integration-test` capturing the fixture authoring,
stub/replay machinery (if any), and harness-specific
invocation detail.

---

## Proposal: C1 — Short-form `scripts/_vendor/` paths in PROPOSAL.md (residual from v013 C5 canonicalization)

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`

### Summary

**Failure mode: incorrectness (drift).**

v013 C5 (canonicalize scope wording on full-path form
`.claude-plugin/scripts/livespec/**` etc. throughout the style
doc) applied the sweep-replace rule to
`python-skill-script-style-requirements.md`. PROPOSAL.md was
not explicitly in C5's scope, but the same full-path
canonicalization is used throughout the file — with three
residual short-form occurrences at:

- **Line 880**: *"Validation uses the vendored `fastjsonschema`
  library from `scripts/_vendor/fastjsonschema/` via the
  factory-shape validator pattern …"*
- **Line 2051**: *"Vendored third-party libraries under
  `scripts/_vendor/` are excluded from the coverage
  measurement …"*
- **Line 2501**: *"… vendored libraries under
  `scripts/_vendor/`, `bin/*.py` shebang wrappers + `bin/_
  bootstrap.py`, …"*

Every other `_vendor/` reference in PROPOSAL.md uses
`.claude-plugin/scripts/_vendor/…` or the plain `_vendor/`
within a layout tree that carries the full-path context.

### Motivation

Low-stakes but consistent-wording cleanup; the style-doc
canonicalization is more useful when PROPOSAL.md matches the
same form.

### Proposed Changes

One candidate resolution:

**Option A (recommended):** Sweep-replace
`scripts/_vendor/` → `.claude-plugin/scripts/_vendor/` at
lines 880, 2051, 2501 in PROPOSAL.md. (Reason recommended:
purely mechanical drift fix; zero semantic impact; makes
v013 C5 canonicalization complete.)

---

## Proposal: C2 — Sub-command section headings imply positional CLI arguments that the wrappers do not accept

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`

### Summary

**Failure mode: ambiguity.**

Several sub-command section headings in PROPOSAL.md use
positional-argument notation:

- `### seed <intent>` (line 1276)
- `### propose-change <topic> <intent>` (line 1346)
- `### revise <revision-steering-intent>` (line 1453)

Readers familiar with CLI conventions interpret these as
wrapper signatures: `bin/seed.py <intent>`,
`bin/propose_change.py <topic> <intent>`, etc. But the
wrappers actually accept:

- `bin/seed.py --seed-json <path>` (no positional).
- `bin/propose_change.py --findings-json <path> <topic>
  [--author <id>]` (one positional: `<topic>`).
- `bin/revise.py --revise-json <path> [--author <id>]`
  (no positional).

The `<intent>` / `<revision-steering-intent>` arguments are
consumed by the LLM in SKILL.md prose and never reach the
wrapper. The headings describe the user-facing conceptual
interface (as dialogue input to the skill), not the wrapper
argv.

The ambiguity costs a competent implementer an extra cycle of
reading through §"Inputs" in the SKILL.md body structure
before discovering the split. Not a blocker, but not
zero-cost either.

### Motivation

The headings set early context for each sub-command's spec;
getting the user-facing-vs-wrapper split right in the heading
is cheap and reduces the re-reading burden.

### Proposed Changes

Two candidate resolutions:

**Option A (recommended):** Keep the existing headings as
they describe the user-facing dialogue surface, but add a
short parenthetical to each section's opening paragraph
explicitly noting "the LLM consumes `<intent>` /
`<revision-steering-intent>` in SKILL.md prose; the wrapper's
CLI accepts `--seed-json` / `--findings-json` / `--revise-
json` with the freeform text already consumed into the JSON
payload." (Reason recommended: preserves the reader-friendly
heading form; adds a one-sentence crib at the place a reader
first lands.)

**Option B:** Rewrite headings to reflect wrapper-CLI shape:
`### seed (/livespec:seed)`, `### propose-change <topic>
(/livespec:propose-change)`, etc. Drops the conceptual-
surface signals from the heading; less readable but more
CLI-accurate.

---

## Proposal: C3 — Template-extension module load failure error routing is not codified

### Target specification files

- `brainstorming/approach-2-nlspec-based/deferred-items.md`
- `brainstorming/approach-2-nlspec-based/python-skill-script-script-style-requirements.md` (NOTE: style doc; see below)

### Summary

**Failure mode: incompleteness.**

v011 K5 + v012 L15b codified the template-extension
`doctor_static_check_modules` mechanism: `template.json`
declares paths, `livespec/doctor/run_static.py` loads each
via `importlib.util.spec_from_file_location(...)` +
`module_from_spec(...)` + `loader.exec_module(...)`.
Extension-loaded modules are OUT of scope for livespec's
enforcement suite (L15b principle).

But several failure modes during module load are not routed
to any specific outcome:

- **File missing at the declared path** (the user's
  `template.json` references a module that doesn't exist):
  `spec_from_file_location` returns `None` or `FileNotFound
  Error` depending on Python version.
- **Syntax error in the module**: `exec_module` raises
  `SyntaxError`.
- **Import error in the module** (e.g., imports a package
  the user's system lacks): `exec_module` raises
  `ImportError`.
- **Module loads but doesn't export
  `TEMPLATE_CHECKS`**: registry assembly can detect this;
  v011 K5 says "rejects duplicates at registry-assembly time
  with an IOFailure" but doesn't say anything about
  missing-export.

Without codification, two implementations diverge:

- **Implementation A** wraps each load with `@impure_safe
  (exceptions=(FileNotFoundError, SyntaxError, ImportError,
  AttributeError))`, emits an `IOFailure(Precondition
  Error)` with the template + module path, exits 3.
- **Implementation B** lets syntax/import errors propagate
  as raised exceptions (they're "bugs" in the extension
  author's code), hits the supervisor bug-catcher, exits 1.
- **Implementation C** treats missing file as fail Finding
  (via `template-exists` widening per N4), other errors as
  IOFailure(PreconditionError) → exit 3.

The domain-vs-bugs discipline (`livespec-nlspec-spec.md`
§"Error Handling Discipline") says bugs propagate as
exceptions. But an extension author's syntax error isn't
livespec's bug — it's the extension author's bug, at
livespec's I/O boundary. The right classification isn't
self-evident.

### Motivation

Template-extension failure is a user-visible path — both
built-in and custom templates load through the same
mechanism. The error channel matters for extension authors
(who want actionable diagnostics) and for end users (who
want to know what broke).

### Proposed Changes

Three candidate resolutions:

**Option A (recommended):** Route all module-load failures
(missing file, syntax error, import error, missing
`TEMPLATE_CHECKS` export) through the domain-error channel
as `IOFailure(PreconditionError)` with exit 3. The template-
extension module load is at livespec's I/O boundary per the
domain-error discipline; errors there are "expected
failures" from livespec's perspective (a retry with a fixed
extension module resolves them) even if the cause is the
extension author's code. Codify in `deferred-items.md`'s
`static-check-semantics` §"Template-extension doctor-static
check loading" subsection (v011 K5). Add per-failure-mode
error-message forms for actionable diagnostics. (Reason
recommended: preserves the domain-error / bug split at
livespec's boundary; gives extension authors actionable
exit-3 diagnostics; keeps bug-class exit 1 reserved for
livespec's own code.)

**Option B:** Treat syntax / import errors as bugs (exit 1)
because the extension code failed to import correctly;
missing file as domain error (exit 3) because the template
configuration is wrong. Two-channel split; reflects the
error-type ontology more literally but fragments the
diagnostic channel.

**Option C:** Leave module-load errors implementer choice.
Not recommended — this is exactly the kind of boundary-
behavior divergence the codified error discipline exists to
prevent.

---

## Summary table

| Item | Impact | Failure mode | Touches |
|---|---|---|---|
| N1 | major | malformation | PROPOSAL.md §"Absence behavior" vs §"Template resolution contract" |
| N2 | significant | malformation | finding.py pairing vs three-way check-schema-dataclass-pairing |
| N3 | significant | incompleteness | doctor-static bootstrap on malformed .livespec.jsonc / template.json |
| N4 | significant | incompleteness | template-exists doesn't validate template.json-declared files |
| N5 | significant | ambiguity | author_llm form / sanitization / topic derivation |
| N6 | significant | ambiguity | topic collision suffix form |
| N7 | significant | incompleteness | post-step fail recovery after seed |
| N8 | significant | malformation | prune-history "no arguments" vs pre-step flag pair |
| N9 | significant | incompleteness | no end-to-end / harness-level integration test requirement (added mid-interview) |
| C1 | smaller | incorrectness | residual short-form scripts/_vendor/ paths |
| C2 | smaller | ambiguity | sub-command headings imply positional wrapper args |
| C3 | smaller | incompleteness | template-extension module load failure routing |
