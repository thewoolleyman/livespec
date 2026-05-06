---
topic: proposal-critique-v03
author: Claude Opus 4.7 (1M context)
created_at: 2026-04-22T00:00:00Z
---

## Proposal: M1-schemas-directory-missing-from-skill-layout

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **malformation** (self-contradiction between the layout
diagram and later prose). The skill layout tree does not list a
`schemas/` subdirectory, yet later prose refers to schemas shipping at
`.claude-plugin/skills/livespec/schemas/`.

### Motivation

§"Skill layout inside the plugin" shows no `schemas/` subdirectory.
§"Skill↔template communication layer" says "Schemas for the JSON
contracts ship as part of the skill in
`.claude-plugin/skills/livespec/schemas/`." §"critique" names "the
findings schema (skill-owned; under
`.claude-plugin/skills/livespec/schemas/critique-findings.json`)." Two
implementers building from the layout tree alone will not create
`schemas/`, producing a skill that cannot validate template JSON
output. Recreatability test fails at this point.

### Proposed Changes

Insert `schemas/` into the skill-layout tree, adjacent to `scripts/`,
with the currently-named representative file:

```diff
  ├── scripts/
  │   └── doctor-static.sh               # doctor's static phase (bash)
+ ├── schemas/                           # JSON schemas for skill↔template I/O
+ │   └── critique-findings.json         # additional schemas added by post-seed propose-change
  ├── livespec-nlspec-spec.md            # embedded grounding guidelines
```

---

## Proposal: M2-livespec-nlspec-spec-location-contradiction

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **malformation** (three conflicting statements of where
`livespec-nlspec-spec.md` lives) plus **ambiguity** (skill-root copy's
purpose is unstated).

### Motivation

Three inconsistent placements:

1. §"Skill layout inside the plugin" places `livespec-nlspec-spec.md`
   directly under `.claude-plugin/skills/livespec/` (skill root) AND
   under `specification-templates/livespec/` (template root).
2. §"Templates — Template directory layout (MUST)" places it at the
   template root only (OPTIONAL).
3. §"Built-in template: `livespec`" says "The template's
   `prompts/livespec-nlspec-spec.md` at the template root…" — the
   path `prompts/livespec-nlspec-spec.md` and the phrase "at the
   template root" are mutually exclusive because `prompts/` is a
   subdirectory.

The skill-root copy has no stated purpose anywhere. Two implementers
will make three different decisions (skill-root only / template-root
only / both). Prompt-context injection is well-defined for the
template-root copy; the skill-root copy is an accidental artifact of
the layout diagram.

### Proposed Changes

Canonicalize on a single location (template root) and eliminate the
contradictions:

- In §"Skill layout inside the plugin", remove the
  `livespec-nlspec-spec.md` line at the skill root.
- In §"Built-in template: `livespec`", change "The template's
  `prompts/livespec-nlspec-spec.md` at the template root" to "The
  template's `livespec-nlspec-spec.md` at its root".
- Leave the Templates section (template-root OPTIONAL) unchanged.

If a skill-level guideline doc is wanted for a distinct purpose (e.g.,
`SKILL.md`'s own reading), state that purpose explicitly; otherwise
accept the single-location cleanup above.

---

## Proposal: M3-sub-command-dispatch-script-unnamed

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **incompleteness**. The sub-command dispatcher is
described as "a bundled shell parser" but no path, filename, or
invocation idiom is specified.

### Motivation

§"Skill layout inside the plugin" lists only `scripts/doctor-static.sh`.
§"Sub-command dispatch" says "a bundled shell parser tokenizes `args`
(POSIX-style) and routes to the relevant `commands/<sub-command>.md`
instruction file." An implementer will place the dispatcher at an
arbitrary location — inline in `SKILL.md`, a new `scripts/dispatch.sh`,
a bash snippet under `shared/`, etc. The same named-file discipline
applied to `doctor-static.sh` must apply here.

### Proposed Changes

Add a concrete path and contract:

- Add `scripts/dispatch.sh` to the skill-layout tree, peer to
  `doctor-static.sh`.
- In §"Sub-command dispatch", change "a bundled shell parser" to
  "the dispatcher script at `scripts/dispatch.sh`".
- Specify the dispatcher contract: "tokenizes `$@` (POSIX-style);
  emits the resolved sub-command name and remaining positional
  arguments on stdout; exits nonzero with a diagnostic on unknown
  sub-command, mismatched args, or missing required args. The LLM
  is instructed on `commands/<sub-command>.md` after routing."

---

## Proposal: M4-bundled-default-propose-change-prompt-location

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **incompleteness**. §"propose-change" refers to "a
bundled default" prompt when the active template lacks
`prompts/propose-change.md`, but the default's path and loading
mechanism are not defined.

### Motivation

§"Template directory layout (MUST)" declares only `prompts/seed.md`,
`prompts/revise.md`, and `prompts/critique.md` as REQUIRED.
`prompts/propose-change.md` is therefore implicitly OPTIONAL, with a
skill-provided fallback. The fallback is unstated:

- Does it live at `shared/default-propose-change-prompt.md`?
- `commands/propose-change.md` itself (mixing dispatch with prompting)?
- Somewhere else?

Two implementers produce distinct file layouts. Worse, a skill-level
propose-change prompt violates the skill↔template responsibility split
(content generation is template-owned).

### Proposed Changes

Promote `prompts/propose-change.md` to REQUIRED in the template layout
and drop the "bundled default" language:

- In §"Template directory layout (MUST)", add
  `prompts/propose-change.md` to the list of REQUIRED files.
- In §"propose-change", remove the "(if present; else a bundled
  default)" clause.
- Templates without propose-change authoring in scope SHOULD fail fast
  (doctor check #2 or #3) rather than silently degrade.

Alternative (if REQUIRED is too strong): explicitly state the fallback
location, e.g., `shared/default-propose-change-prompt.md`, and add it
to the skill layout.

---

## Proposal: M5-critique-to-propose-change-invocation-mode

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **ambiguity**. §"critique" says "The skill then invokes
`propose-change` with topic `<author>-critique`" without stating
whether this is a sub-command invocation (re-running pre-step doctor)
or an internal function call. A sub-command call means doctor runs
recursively; an internal call needs an explicit carve-out from the
"every sub-command MUST run doctor's static phase as its first step"
rule.

### Motivation

If sub-command invocation: `critique` runs pre-step doctor → template
critique prompt → sub-command call → `propose-change` runs its own
pre-step doctor (again) → writes file → runs post-step doctor. Post-
step doctor of critique then runs again on top. Nested runs multiply
side-effects on failure paths and waste work.

If internal call: pre/post doctor does not apply to the inner call and
the overall rule has an implicit exception.

### Proposed Changes

State explicitly in §"critique":

> The skill delegates file-creation to `propose-change`'s internal
> logic (not a sub-command re-invocation). Pre-step and post-step
> doctor run only once, at the outer `critique` invocation. The
> delegation passes the structured findings and topic
> (`<author>-critique`) directly; it does not pass through the
> dispatcher.

Also add to §"livespec skill sub-commands" a one-sentence note that
sub-commands MAY internally delegate to other sub-commands' logic
without re-triggering pre/post doctor, because the outer sub-command's
doctor lifecycle already covers the whole invocation.

---

## Proposal: M6-shared-directory-contents-truncated

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **incompleteness**. The skill-layout tree lists
`shared/template-loading.md` and `shared/lifecycle-invariants.md`
followed by `...`. The `...` is an unenumerated `etc.` — the same
failure-mode as the v001 critique's M7 (doctor inventory ended in
"etc.").

### Motivation

An implementer cannot derive the full `shared/` membership from the
layout tree. Is the list illustrative or prescriptive? Is
implementer-chosen? The ambiguity reintroduces exactly the openness
the v001 critique closed for doctor checks.

### Proposed Changes

Replace the `...` with a non-enumerated prose description. In the
layout tree, collapse to a single representative note:

```
├── shared/                            # reusable prose/logic referenced by commands/
│   └── ...                            # content driven by DRY needs during command authoring
```

and in the surrounding prose: "The `shared/` subdirectory contains
reusable content pulled in via `@`-references from `commands/` files.
Its exact membership is an implementation concern; no specific file is
required by this proposal."

Alternative: enumerate the full REQUIRED set (if known) and remove the
`...` entirely.

---

## Proposal: M7-pre-step-doctor-auto-backfill-blast-radius

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **incorrectness** (likely unintended behavior).
Doctor static check #9 auto-backfills a missing version — creating
`history/v(N+1)/`, proposed-change and revision files authored as
`livespec-doctor`, then aborting — as part of *pre-step* doctor of
any sub-command. This means every sub-command can mutate history
before the user's intended work begins.

### Motivation

A user running `livespec propose-change foo "new intent"` after making
direct spec edits expects the propose-change to use those edits as
context, or to fail with a clear message. Instead, pre-step doctor
auto-captures the edits under a generated topic name
(`out-of-band-edit-<UTC-seconds>`) and cuts a new history version
before the user's propose-change even runs. The user's intended topic
is lost to an auto-generated one, and history is cut behind their
back. This conflicts with the expectation that sub-commands only
mutate the tree along their primary flow.

### Proposed Changes

Move auto-backfill OUT of pre-step doctor. Check #9 fails the pre-step
with a clear, actionable finding:

- New check-#9 behavior: detect out-of-band drift; if detected, emit a
  JSON finding "Out-of-band edits detected. Run
  `livespec propose-change <your-topic> "<description>"` to capture
  them, or `livespec doctor --backfill` to auto-capture." Exit
  nonzero.
- Introduce `livespec doctor --backfill` as the explicit opt-in path
  for the auto-capture flow currently described. Its behavior is
  identical to the current check-#9 auto-backfill, but the user has
  invoked it intentionally.

Alternative (retain current behavior): require the user's outer
sub-command to have been invoked with `--allow-backfill`; without the
flag, pre-step doctor surfaces the drift but does not mutate. Default
is to surface, not mutate.

---

## Proposal: M8-doctor-exit-codes-conflict-with-bash-style-doc

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md

### Summary

Failure mode: **malformation** (cross-document contradiction). The
PROPOSAL.md static-phase contract uses exit `1` for "at least one
check failed"; the companion `bash-skill-script-style-requirements.md`
reserves exit `1` for "script-internal failure (unexpected runtime
error; likely a bug)" and defines exit `3` as "input or precondition
failed". Doctor-static.sh's check-failure path is semantically
precondition-failed (exit `3`), not a script bug.

### Motivation

doctor-static.sh is the canonical example script governed by the
bash-style doc, which is destined for `SPECIFICATION/constraints.md`.
The two documents must agree; as written they do not. An implementer
producing doctor-static.sh following the bash-style doc will exit `3`
on check failure; an implementer following PROPOSAL.md will exit `1`.
The skill's LLM-layer and any caller tooling will misroute on the
wrong code.

### Proposed Changes

Reconcile by changing the PROPOSAL.md static-phase contract to match
the bash-style doc:

- §"Static-phase exit codes" becomes:
  - `0`: all checks pass; LLM-driven phase MAY proceed.
  - `1`: script-internal failure (bug in `doctor-static.sh` itself).
  - `3`: at least one check failed; LLM-driven phase MUST NOT run; the
    invoking sub-command MUST abort.
- Update references elsewhere in PROPOSAL.md (e.g., "nonzero") to
  "exit `3`" where check-failure is specifically meant.

---

## Proposal: S9-plugin-json-schema-undefined

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **incompleteness**. §"Plugin delivery" mandates that
`.claude-plugin/plugin.json` "MUST be present and fully populated
(plugin metadata, skill manifest)" but does not specify the schema,
required fields, or which Claude Code plugin-format version is
targeted.

### Motivation

Without a pinned schema, two implementers produce `plugin.json` files
that diverge in field names and structure. The Claude Code plugin
format may evolve. An implementer does not know whether fields like
`name`, `version`, `skills`, `commands`, etc. are required, optional,
or free-form.

### Proposed Changes

Either:

(a) Pin a specific Claude Code plugin format version and reference it
    normatively: "plugin.json conforms to the Claude Code plugin
    format at [URL] as of [date]. Required fields per that spec
    apply."

(b) Specify a minimal normative schema in PROPOSAL.md itself:
    - REQUIRED: `name`, `version`, `description`,
      `skills[]` (each with `name` and relative path).
    - The skill MUST NOT fail on unknown `plugin.json` fields.

(c) State explicitly that `plugin.json`'s detailed contents are outside
    the scope of this proposal; they track whatever Claude Code's
    current plugin-format release requires at build time, and the
    skill itself does not validate `plugin.json`.

Recommend (c) as the lightest-weight resolution given the
fast-evolving plugin format.

---

## Proposal: S10-check-13-redundant-with-check-2

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **malformation** (define-twice redundancy). Doctor
static check #13 and check #2 describe the same validation (active
template directory has required layout and matching version).

### Motivation

Check #2: "The active template…exists and has the required layout
(`template.json`, `prompts/`, `specification-template/`).
`template.json`'s `template_format_version` matches `.livespec.jsonc`'s
`template_format_version` and is supported by livespec."

Check #13: "The resolved active template directory has the required
layout and matching version (see check #2). Any unresolved or
mismatched template configuration is a static failure naming the
offending field, its value, and the path to `.livespec.jsonc`."

Check #13 adds only a diagnostics requirement (name-the-field-and-path
in the error). That's a refinement of check #2, not a separate check.
Per the embedded guidelines' define-once principle, two checks that
cover the same fact drift over time.

### Proposed Changes

Delete check #13. Fold its diagnostics requirement into check #2:

> 2. The active template (built-in or at the configured path) exists
>    and has the required layout (`template.json`, `prompts/`,
>    `specification-template/`). `template.json`'s
>    `template_format_version` matches `.livespec.jsonc`'s
>    `template_format_version` and is supported by livespec. On any
>    failure, the static finding MUST name the offending field, its
>    value, and the path to `.livespec.jsonc`.

Update DoD item 6 from "13 checks above" to "12 checks above".

---

## Proposal: S11-prune-history-first-semantics-on-repeat-prunes

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **ambiguity**. §"Pruning history" defines
`pruned_range = [first, N-1]` where `first` is "the earliest version
number that existed before this prune". On a second prune, when the
previous marker is being deleted, the definition is ambiguous: does
`first` mean the original earliest version (preserved from the old
marker) or the old marker's own version number?

### Motivation

Example: prune at N=4 produces a marker at v003 with
`pruned_range: [1, 3]`. Later, prune at N=9 deletes v003 (old marker)
through v007 and replaces v008 with a new marker. The new marker's
`first`:

- `1` preserves the original earliest version ever tracked (reading
  the old marker's `pruned_range[0]` before deletion).
- `3` takes the old marker's directory version number as-is.

The two produce different audit trails; the recreatability of the
pre-prune historical range depends on which reading is correct.

### Proposed Changes

Specify preservation: before deleting the existing
`PRUNED_HISTORY.json`, `prune-history` reads its `pruned_range[0]` and
uses it as the new `first`. If no prior marker exists, `first` is the
earliest version number found in `history/`. Add to §"Pruning
history":

> If `history/v(N-1)/PRUNED_HISTORY.json` exists before this prune
> runs, `prune-history` MUST read its `pruned_range[0]` and use that
> value as `first` in the new marker, preserving the earliest
> historically tracked version number across successive prunes.

---

## Proposal: S12-testing-implementation-language-not-pinned

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **ambiguity** (cross-document conflict). §"Testing
approach" says "Implementation language is not pinned by this
proposal" but references test files (`test_spec.*`, etc.) with
unspecified extensions. The companion
`bash-skill-script-style-requirements.md` §"Testing" mandates
`bats-core` for bash scripts, implying `.bats` test files. Since the
skill's scripts are bash, the tests must be `.bats`.

### Motivation

An implementer reading PROPOSAL.md alone concludes the language is
free. An implementer reading the companion concludes it is bash/bats.
Which binds? The companion is destined for
`SPECIFICATION/constraints.md` (per §"Testing approach"), so it will
bind post-seed. But the PROPOSAL.md testing section should already
be consistent.

### Proposed Changes

In §"Testing approach", change:

> Tests live in `<project-root>/tests/`. Implementation language is
> not pinned by this proposal; a companion
> `bash-skill-script-style-requirements.md` …

to:

> Tests live in `tests/` at the skill-repo root (a sibling of
> `.claude-plugin/`). Test runner is `bats-core`; test files use the
> `.bats` extension. Full test-runner contract is documented in the
> companion `bash-skill-script-style-requirements.md`, destined for
> `SPECIFICATION/constraints.md`.

Update file-name references elsewhere from `test_spec.*`,
`test_contracts.*`, `test_constraints.*`, `test_scenarios.*`,
`test_meta_section_drift_prevention.*` to `.bats` extensions
uniformly.

---

## Proposal: S13-propose-change-input-shape-discrimination

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **ambiguity**. §"propose-change" says the skill
distinguishes structured-findings-JSON from raw-intent-text "by
content shape". The exact algorithm is unspecified; edge cases are
unresolved.

### Motivation

Edge cases:

- User literally pastes JSON as `<intent>` that is valid JSON but does
  not conform to the findings schema. Skill falls through to raw-text
  path, or aborts with a validation error?
- User's raw intent text contains the phrase "update the schema to add
  `foo`" — JSON-ish but not parseable. Must be raw text.
- User intentionally wraps their intent in JSON to preserve structure
  but not in findings shape — should this be rejected or parsed?

Two implementers produce different algorithms and different error
semantics.

### Proposed Changes

Specify the algorithm in §"propose-change":

1. Attempt `jq -e . <input>` to detect valid JSON.
2. If valid JSON: attempt validation against
   `schemas/critique-findings.json`. On success, short-circuit to
   findings-to-proposal mapping. On validation failure: abort with
   "input is valid JSON but does not conform to findings schema;
   expected either raw intent text or valid findings JSON."
3. If not valid JSON: treat as raw intent text and invoke the
   template's `prompts/propose-change.md`.

---

## Proposal: S14-revise-file-and-proposal-ordering

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **ambiguity**. §"revise" says "For each `## Proposal`
across all files in `proposed_changes/`, the LLM…proposes an
acceptance decision." Processing order across files and within files
is not stated.

### Motivation

Order matters for: predictable prompt sequence in the interactive
flow; scope of the "delegate remaining proposals in this file" toggle
(which proposals get delegated); and the motivation context the LLM
has when considering later proposals (earlier decisions may inform
later ones).

### Proposed Changes

Specify in §"revise":

> Files in `proposed_changes/` are processed in lexicographic order
> by filename (locale-independent byte comparison). Within each file,
> `## Proposal` sections are processed in document order (top to
> bottom). The "delegate remaining proposals in this file" toggle
> applies only to proposals in the currently-active file; the next
> file prompts the user again unless re-delegated.

---

## Proposal: C15-remove-duplicate-no-open-questions-rule

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **malformation** (define-twice redundancy). The rule "A
proposal MUST NOT contain open questions, alternatives, or 'we should
decide X later' content" is stated in both §"propose-change" and
§"Proposed-change file format".

### Motivation

Per the embedded guidelines' define-once principle, redundant rules
drift when one is revised without the other. The natural home is the
format section, since that is where the proposed-change contract is
defined.

### Proposed Changes

Delete the duplicate from §"propose-change". Retain the statement in
§"Proposed-change file format" where it is structurally aligned with
the rest of the format contract.

---

## Proposal: C16-seed-idempotency-edge-cases

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **ambiguity**. §"seed" says "if any of the
template-declared target files already exist at their target paths,
`seed` MUST refuse". Edge cases are unspecified: what counts as a
"template-declared target file"? Is `.livespec.jsonc` in the set?

### Motivation

Ambiguities:

- If `.livespec.jsonc` is a template-declared target, manually-authored
  configs block seed.
- If `.livespec.jsonc` is not, seed overwrites it silently on second
  invocation (violating the spirit of idempotent-refusal).
- What happens if only `SPECIFICATION/` exists but not the config, or
  vice versa (partial state)?

### Proposed Changes

Tighten §"seed" with explicit rules:

> `.livespec.jsonc` is NOT a template-declared target file. `seed`
> creates `.livespec.jsonc` only if absent; if present, `seed`
> validates it (static-check #1) and reuses it without modification.
>
> Template-declared target files are those produced by walking the
> active template's `specification-template/` directory. If any of
> these target files exists at the corresponding repo-root-relative
> path, `seed` MUST refuse with an error listing the existing files.
>
> Partial state (some target files present, others absent) is also a
> refusal; the user is directed to run `doctor` for diagnosis.

---

## Proposal: C17-history-vnnn-readme-semantics

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **ambiguity** (minor). §"SPECIFICATION directory
structure (livespec template)" shows three `README.md` entries: a
skill-owned top-level `history/README.md` and a per-version
`history/vNNN/README.md` (versioned copy of
`SPECIFICATION/README.md`). The distinction is present in prose but
easy to conflate when scanning the tree.

### Motivation

The skill-owned top-level README is written once (at seed) and not
regenerated; the per-version README is a versioned copy of the user's
spec README. They have different authorities and update rules.

### Proposed Changes

Tighten inline annotations on the tree:

```diff
  └── history/
-     ├── README.md                      (skill-owned; written only at seed)
+     ├── README.md                      (skill-owned; one-paragraph directory description; written only at seed)
      └── vNNN/                      (one directory per version)
-         ├── README.md              (copy of SPECIFICATION/README.md at this version)
+         ├── README.md              (archived copy of SPECIFICATION/README.md at this version; user content, versioned)
```

---

## Proposal: C18-project-root-tests-location

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **ambiguity**. §"Testing approach" says "Tests live in
`<project-root>/tests/`" without clarifying which project. The skill
lives under `.claude-plugin/skills/livespec/`; tests of the skill live
at the skill-repo root, not inside the skill bundle.

### Motivation

A reader may conflate "the livespec skill's project root" with "any
user's SPECIFICATION project root". The latter is out of scope for
livespec (user projects don't get tests automatically).

### Proposed Changes

Change the first sentence of §"Testing approach" to:

> Tests for the `livespec` skill live at the skill-repo root under
> `tests/` (a sibling of `.claude-plugin/`). Tests of a user's own
> SPECIFICATION are out of scope for livespec.

(Combined with S12's language-pinning change; both target the same
section.)

---

## Proposal: C19-revision-steering-intent-content-injection

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **malformation** (latent rule conflict).
§"revise" says `<revision-steering-intent>` "discourages but does not
forbid" using the arg to inject new spec content. §"Template-agnostic
principles" says "All intent (observations, critiques, external
requirements, implementation feedback) flows through `propose-change`
or `critique`. No other ingress paths to the spec lifecycle are
defined." These two rules conflict: the revise arg IS an ingress path
if it can introduce new spec content.

### Motivation

The "no other ingress paths" invariant is load-bearing: it's what
makes the lifecycle auditable and the history file complete. An
ingress path that bypasses proposed-change creates spec content with
no traceable proposal-source.

### Proposed Changes

Tighten §"revise":

> `<revision-steering-intent>` MUST NOT contain new spec content. It
> MUST only steer per-proposal decisions for the current revise
> invocation (e.g., "reject anything touching the auth section"). If
> the user supplies content that expresses new intent rather than
> decision-steering, the skill MUST surface this as a warning and
> direct the user to run `propose-change` first. (Detection is
> best-effort LLM judgment; on ambiguity, the skill proceeds with a
> visible warning.)

---

## Proposal: C20-section-drift-meta-test-naming

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **malformation** (minor naming drift). §"Testing
approach" names the meta-test `test_meta_section_drift_prevention.*`.
DoD item 10 refers to "the meta `section_drift_prevention` test"
without the `test_meta_` prefix.

### Motivation

The two names refer to the same test; uniform naming reduces reader
confusion and helps code search.

### Proposed Changes

Update DoD item 10:

```diff
- 10. The test suite covers every sub-command, both doctor phases,
-     the `prune-history` flow, and the meta
-     `section_drift_prevention` test.
+ 10. The test suite covers every sub-command, both doctor phases,
+     the `prune-history` flow, and the
+     `test_meta_section_drift_prevention.bats` test.
```

(Extension change assumes S12 is accepted; if rejected, leave the
extension unspecified as `.*`.)

---

## Proposal: C21-pre-step-skip-warning-channel

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **ambiguity**. The proposal says "the skill MUST print a
warning" when pre-step static checks are skipped (§"Configuration" and
§"Per-invocation CLI overrides"), without specifying the output
channel (stdout, stderr, LLM narration).

### Motivation

Script-level warnings go to stderr per the bash-style doc. Skill-level
warnings are usually LLM-mediated. Mixing the two produces
inconsistent user experience — a skip warning may appear in the LLM's
output, in stderr, both, or neither depending on the implementer's
guess.

### Proposed Changes

Specify in §"Per-invocation CLI overrides":

> The warning is surfaced through the LLM's user-facing output (the
> skill's natural channel). When the pre-step-skip decision is made
> at the static-phase level, the raw skill-side record is a
> structured JSON finding (`status: "skipped"`,
> `message: "pre-step checks skipped by user config or --skip-pre-check"`)
> which the LLM then narrates. The bash layer MUST NOT print the
> warning to stdout or stderr directly; stdout is reserved for the
> structured-findings contract.

---

## Proposal: G22-bash-boilerplate-missing-from-skill-layout

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **incompleteness** (PROPOSAL.md does not surface a
file mandated by its own companion `bash-skill-script-style-requirements.md`).
The style doc §"Boilerplate requirement" mandates
`scripts/bash-boilerplate.sh` be bundled; PROPOSAL.md's skill layout
tree does not list it.

### Motivation

The boilerplate is load-bearing for every runnable script: it
defines `onexit`, strict mode, trap installation, debug-variable
handling, and the `name() {}` function convention. Every bash script
bundled with the skill sources it. Missing it from PROPOSAL.md's
layout means two implementers build the skill with differently-shaped
(or missing) strict-mode setups.

### Proposed Changes

Add `scripts/bash-boilerplate.sh` to the skill-layout tree:

```diff
  ├── scripts/
+ │   ├── bash-boilerplate.sh            # shared strict-mode + trap boilerplate (sourced by all scripts)
  │   ├── dispatch                       # sub-command dispatcher
  │   └── doctor-static                  # doctor's static phase
```

---

## Proposal: G23-scripts-ci-directory-missing

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **incompleteness**. The style doc §"Enforcement via
git hooks and CI" mandates `scripts/ci/` for small architectural-
check scripts (`check-library-headers`, `check-source-graph`,
etc.). PROPOSAL.md's skill layout tree does not include this
directory.

### Motivation

CI architectural checks are gating; missing them means the
mandated enforcement has nowhere to live. Two implementers will
either omit the checks or place them at divergent paths.

### Proposed Changes

Add `scripts/ci/` to the skill-layout tree, adjacent to the primary
scripts:

```diff
  ├── scripts/
  │   ├── bash-boilerplate.sh
  │   ├── dispatch
  │   ├── doctor-static
+ │   └── ci/                            # architectural-check scripts invoked by CI
+ │       └── ...                        # check-library-headers, check-source-graph, etc.
```

Content-level enumeration of each CI check is governed by the bash
style doc; no per-file enumeration belongs in PROPOSAL.md.

---

## Proposal: G25-strengthen-testing-section-with-bats-assert-and-kcov

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **incompleteness**. The style doc mandates specific
test-tooling invariants not reflected in PROPOSAL.md's §"Testing
approach". Combined with S12's `.bats` extension fix, the section
needs to name the assertion library and the coverage gate.

### Motivation

The style doc requires: (a) `bats-assert` for all assertions
(bare `[[ ... ]]` in `@test` blocks forbidden); (b) `bats-support`
as a dependency; (c) `kcov` for coverage with 100% pure / 80%
overall thresholds; (d) `tests/fixtures/` directory for explicit
fixtures; (e) `BATS_TEST_TMPDIR` for test-local filesystem state.
None of this is surfaced in PROPOSAL.md.

### Proposed Changes

Update PROPOSAL.md §"Testing approach" (combined with S12) to add:

- Test runner: `bats-core`; assertions: `bats-assert` (with
  `bats-support`); extension: `.bats`.
- Fixtures under `tests/fixtures/`; test-local state under
  `BATS_TEST_TMPDIR`.
- Coverage measured by `kcov`; pure libraries 100%; overall
  ≥ 80%. Full coverage and tooling contract documented in the
  companion bash style doc.
- DoD item 10 updated accordingly.

---

## Proposal: G26-tests-fixtures-directory-structure

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **incompleteness**. The style doc references
`tests/fixtures/` as the canonical location for explicit test
fixtures; PROPOSAL.md's testing section does not show the `tests/`
directory structure.

### Motivation

Without a shape for `tests/`, an implementer will place fixtures
arbitrarily, and the style doc's "MUST NOT mutate anything under
`tests/fixtures/`" rule has no anchor in PROPOSAL.md.

### Proposed Changes

Add a concise `tests/` tree to §"Testing approach":

```
tests/
├── CLAUDE.md                          (per existing rule)
├── heading-coverage.json              (registry)
├── fixtures/                          (explicit test fixtures; MUST NOT be mutated by tests)
├── scripts/                           (per-script .bats files, mirroring scripts/ names)
│   ├── dispatch.bats
│   └── doctor-static.bats
└── test_*.bats                        (per-specification-file tests)
```

Exact membership beyond this skeleton is an implementation concern.

