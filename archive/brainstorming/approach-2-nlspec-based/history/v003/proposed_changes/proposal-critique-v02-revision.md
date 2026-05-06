---
proposal: proposal-critique-v02.md
decision: modify
revised_at: 2026-04-21T00:00:00Z
reviser_human: thewoolleyman
reviser_llm: Claude Opus 4.7 (1M context)
---

# Revision: proposal-critique-v02

## Provenance

- **Proposed change:** `proposal-critique-v02.md` (in this directory)
- **Revised by:** thewoolleyman (human) in dialogue with Claude Opus 4.7
  (1M context)
- **Revised at:** 2026-04-21 (UTC)
- **Scope:** v002 PROPOSAL.md → v003 PROPOSAL.md

## Summary of dispositions

| Severity | Count | Accepted | Modified-on-accept | Deferred to v2 | Rejected |
|---|---|---|---|---|---|
| Major (blocks seeding) | 8  | 2 | 6 | 0 | 0 |
| Significant | 10 | 2 | 8 | 0 | 0 |
| Smaller / cleanup | 13 | 9 | 3 | 0 | 1 |

Many items were accepted but heavily reshaped in dialogue — recorded
below as "modified-on-accept." This revision also introduced several
new decisions not in the critique:

- Project delivered as a Claude Code plugin (new plugin scope).
- Template architecture shift to Option 3 (directory of prompts +
  skeleton files; custom templates in-scope for v1).
- Terminology renames: `acknowledgement` → `revision`;
  `freeform text` → `intent` (with `additional-intent` for `revise`).
- Drop of "partition" / "specification partition" domain term in
  favor of "specification file."
- Drop of `vNNN-` prefix on files inside `history/vNNN/`.
- New sub-command: `prune-history`.
- v000 as implicit empty pre-seed state; seed modeled as the proposal
  that transforms v000 → v001.
- jq as a hard runtime dependency.
- New config keys for pre-step and post-step doctor phase skip.

---

## Disposition by item

### Major gaps

**M1. Claude Code skill execution model undefined.**
Decision: **Modified-on-accept.** Resolution substantially expanded
during dialogue:

- Project is delivered as a **Claude Code plugin**, not a bare skill.
  Canonical plugin path `.claude-plugin/skills/livespec/`.
  `.claude-plugin/skills/livespec/` symlinked to `.claude/skills/livespec/`
  for in-repo dogfooding. `plugin.json` defined and populated.
  Marketplace publishing + opencode + pi-mono support deferred to v2.
- Skill packaging: `SKILL.md` + per-sub-command instruction files
  under `commands/`, with shared helper files (template reading,
  doctor invocation) DRYed up. `@`-commands force deterministic
  reading of critical files. Bash scripts used for deterministic
  logic wherever possible.
- Sub-command dispatch: shell parser + routing (a bundled dispatcher
  script tokenizes args and calls per-sub-command logic; LLM is
  instructed after routing).
- User prompting: LLM-mediated prompts with structured-tool fallback.

**M2. Static-phase script form.**
Decision: **Modified-on-accept.**

- Script language: **Bash**. A separate
  `bash-skill-script-style-requirements.md` will be authored as a
  companion, destined for `SPECIFICATION/constraints.md`; includes
  shellcheck + static-analysis compliance via git hooks / CI.
- Output contract: **Structured JSON on stdout.** Human-readable
  output removed (no human audience in the skill flow — LLM consumes
  the Bash tool's output and narrates).
- Check #9 cross-phase handoff: reframed. Drift on the
  working-spec-vs-latest-history comparison is handled by
  **unconditional auto-backfill**, not by prompting. On detection:
  - Skip if the project is not a git repo (no WIP distinction
    possible).
  - Skip if spec files have uncommitted changes (WIP; user is
    mid-edit).
  - Otherwise: auto-create a proposed-change capturing the diff,
    auto-create a revision accepting it, write `history/v(N+1)/`
    with the current working spec content, abort, and tell the user
    to commit the changes and re-run.
  - Fixed author identifier: `livespec-doctor`.
  - Tightens the project-wide git non-goal: livespec MUST NOT *write*
    to git, but MAY *read* git state where needed (only documented
    use is this check).
- Script location: `.claude-plugin/skills/livespec/scripts/doctor-static.sh`.

**M3. `revise` modification mechanism.**
Decision: **Modified-on-accept.** Restructured significantly:

- **Multi-proposal file format.** A single `proposed-change` file MAY
  contain multiple discrete proposals. Each is a flat `## Proposal:
  <name>` section with sub-headings `### Summary`, `### Motivation`,
  `### Target specification files`, `### Proposed Changes`.
  File-level front-matter keeps `topic` / `author` / `created_at`;
  per-proposal target files move into each proposal section.
- **Revise flow:** user is prompted per-proposal (accept / modify /
  reject). A "delegate rest of file to LLM" toggle lets the user
  skip further confirmations within a file; the LLM then auto-
  decides remaining proposals.
- **`modify` authoring:** LLM drafts the modification; user iterates
  in dialogue to convergence, then confirms. Auto-handled when the
  file is delegated.
- **Proposal file preserved byte-identical** when moved to
  `history/v(N+1)/proposed_changes/<topic>.md`. Delta captured in
  the revision file's `## Modifications` section.
- **`## Modifications` format: prose only.** Unified diffs in
  modification records create fragile line-number anchors across
  multi-proposal revises; prose captures intent without brittleness.
  Optional short fenced before/after excerpts permitted.
- **Rename: `acknowledgement` → `revision`** everywhere (file type,
  front-matter field references, prose descriptions). Overloading
  with other "revise" senses is acceptable; git's "commit" analogue.
- **Rename: `<freeform text>` → `<intent>`** for `seed` and
  `propose-change`; **`<revision-steering-intent>`** for `revise`.
  The name discourages — but does not forbid — using the arg to
  inject new spec content without filing a proposed-change first.
  Its primary role is standing guidance on how existing in-flight
  proposals should be decided (e.g., "reject anything touching
  the auth section"). If a user uses it to introduce new intent,
  that's their choice and responsibility.
- **Revise MUST fail hard when `proposed_changes/` is empty**,
  directing the user to run `propose-change` first. No auto-
  create ephemeral proposal file. Blurring responsibility between
  `propose-change` (intent capture) and `revise` (decision
  application) is avoided.

**M4. Progressive-disclosure dangling reference.**
Decision: **Accepted.** Delete the "per the progressive-disclosure
mapping below" clause in the doctor LLM-driven phase section; replace
with "against the full embedded guidelines."

**M5. `critique` → `propose-change` output contract.**
Decision: **Modified-on-accept.**

- Critique prompt emits **structured JSON findings**, not raw markdown.
- Skill parses JSON, wraps each finding into one `## Proposal`
  section (one finding = one proposal).
- Skill adds file-level front-matter and writes the file to
  `proposed_changes/<author>-critique.md`.
- JSON schema for findings: `findings[*]` with fields `id`, `name`,
  `target_specification_files`, `summary`, `motivation`,
  `proposed_change`. Schema ships as part of the spec; LLM validates
  its own output against it before returning.
- `propose-change` has a dual input path: structured JSON findings
  short-circuit the LLM reshape step; raw `<intent>` text runs the
  template's propose-change prompt.

**M6. `openspec` silent-failure path.**
Decision: **Accepted (simplest resolution).** Drop `openspec` from
v1 entirely. Only `livespec` is a valid `template` value in v1;
`openspec` becomes v2 material.

**M7. `seed`'s intent handling.**
Decision: **Modified-on-accept.**

- Intent dereferencing (path references in intent): **dropped as
  non-issue.** LLMs handle path references naturally in-context; no
  skill logic needed.
- Heading-extraction nondeterminism: **dissolved by template
  restructuring.** Under the new template architecture, initial
  content placement is the template's concern, not a proposal-level
  rule.

**M8. `.livespec.jsonc` on-disk defaults.**
Decision: **Accepted.** `seed` creates `.livespec.jsonc` fully
commented — the entire schema block with all fields, defaults, and
inline comments.

### Significant gaps

**S9. Doctor check #10 (BCP 14 well-formedness).**
Decision: **Modified-on-accept.** Original "no lowercase
MUST/SHOULD/etc. outside code blocks" rule is retired as brittle and
semantically undecidable. Replaced with:

- **Static phase (hard fail):**
  1. Misspelled uppercase BCP 14 keywords (`MUSNT`, `SHOLD`, etc. —
     finite list).
  2. Mixed-case BCP 14 keywords (`Must`, `Should`, `May` as
     standalone words).
- **LLM-driven phase (surfaced as findings):**
  3. Sentences mixing uppercase and lowercase BCP 14 tokens —
     context-dependent, LLM judges whether intentional.
  4. General BCP 14 conformance (is a normative sentence using
     UPPERCASE? is advisory prose free of accidental MUST/SHOULD?).

**S10. Gherkin spacing check #11 false-positives.**
Decision: **Accepted.** Scope restricted to lines inside scenario
blocks only. A scenario block starts at a `Scenario:` line and
continues to the next `Scenario:` or end-of-file. Within such
blocks, each Gherkin keyword line MUST be preceded and followed by
a blank line. Prose outside scenario blocks (including sentences
starting with `And` / `But`) is unaffected. Fenced code blocks
containing Gherkin steps remain disallowed (existing rule).

**S11. `reviser` identity resolution.**
Decision: **Accepted, expanded.** Revision file front-matter gets
TWO fields: `reviser_human` (pulled from git `user.name` / `user.email`,
or `unknown`) and `reviser_llm` (pulled from host metadata with
`unknown-llm` fallback). Same identity-detection logic applied to
proposed-change `author` field where appropriate.

**S12. Cross-file reference rule boundaries.**
Decision: **Modified-on-accept (broad scope).** The GitHub-flavored
anchor rule AND doctor check #12 both cover all markdown links in
all `SPECIFICATION/` files: spec files, README.md, proposed-change
files, revision files, within-file anchors.

**S13. `SPECIFICATION/README.md` content contract.**
Decision: **Accepted.** Generated from the template's
`specification-template/SPECIFICATION/README.md` at seed, then
treated as a normal spec file — editable via propose-change /
revise, not touched by the skill after seed.

**S14. Versioning width transition.**
Decision: **Accepted.** Version numbers always parsed and compared
**numerically**, never lexically. New versions zero-padded to
`max(3, width-of-previous-highest)`. Historic files keep their
original widths forever; no retroactive renames. Mixed widths
within `history/` are valid.

**S15. `propose-change <topic> <intent>` shape.**
Decision: **Modified-on-accept.** `propose-change` accepts two input
shapes distinguished by content:

- **Structured findings JSON** (from callers like `critique`) —
  skill skips LLM reshape, wraps findings directly into proposal
  sections.
- **Raw `<intent>` text** (CLI-user input) — skill invokes the
  template's `propose-change` prompt, which may split into one or
  more `## Proposal` sections.

LLM file-reference handling (`@path` or natural-language
references in intent) is free by virtue of LLM capability; no
skill logic.

**S16. Seed input preservation.**
Decision: **Modified-on-accept.** Reframed after rejecting the
"recreatability test" argument (misapplied). Real motivation is
audit-trail and dogfood consistency. Resolution:

- Seed intent is captured as `history/v001/proposed_changes/seed.md`,
  wrapped in the normal proposed-change format (one `## Proposal`
  with `<intent>` as content).
- An auto-created `history/v001/proposed_changes/seed-revision.md`
  pairs with it (`decision: accept`, `reviser_llm: livespec-seed`,
  rationale "auto-accepted during seed").
- This unifies the lifecycle: seed is a proposal transforming
  implicit empty v000 → v001. v000 is conceptual only, never on
  disk. No special-casing in doctor.

New sub-command **`prune-history`**:

- Deletes all history versions older than v(N-1).
- Replaces v(N-1)'s contents with a single `PRUNED_HISTORY.json`
  marker: `{"pruned_range": [first, N-1]}`. No timestamp or SHA
  (fragile under rebase/merge; git metadata already provides
  audit).
- Version counter never resets; previously-used numbers are never
  re-issued.
- Doctor check #6 (contiguity) reads the marker file and applies
  contiguity only to surviving versions.

Parallel structure for `history/vNNN/`:

- `history/vNNN/` mirrors the active `SPECIFICATION/` tree
  structure: contains `README.md`, spec files, and a
  `proposed_changes/` sub-directory.
- **`vNNN-` prefix on files inside `history/vNNN/` is dropped**
  entirely. The parent directory name already conveys the version.
- Files inside `history/vNNN/proposed_changes/` use plain `<topic>.md`
  and `<topic>-revision.md` names. This preserves relative markdown
  links (e.g., `../spec.md#heading` from an archived
  proposed-change resolves to the archived spec, not the current
  working one).
- IDE search pollution on spec file names (multiple `spec.md`
  across versions) is acknowledged as the cost; mitigated by
  `prune-history` when desired.

**S17. Prior-art attribution.**
Decision: **Modified-on-accept (reference-only).** Clarifying
resolution:

- `prior-art/` is a top-level directory in the livespec repo for
  attribution of *this project's* prior art. It is NOT part of any
  user's SPECIFICATION/. The v002 acknowledgement's outstanding
  follow-up item to "move `nlspec-spec.md` into `SPECIFICATION/prior-art/`"
  was wrong and is dropped.
- `nlspec-spec.md` (verbatim upstream copy) will be **deleted from
  the repo**. `prior-art.md`'s existing permalink entry (pinned to
  commit `ed7a531884c456787254d0450d450664e296b75b`) is the sole
  reference.
- `livespec-nlspec-spec.md`'s header updated to point at the
  permalink URL instead of `prior-art/nlspec-spec.md`.

- **New decision on where `livespec-nlspec-spec.md` lives:**
  at the active template's root (peer to `prompts/` and
  `specification-template/`), e.g.,
  `specification-templates/livespec/livespec-nlspec-spec.md`. The
  skill injects its contents as reference context when invoking
  any template prompt. Template authors can ship their own
  discipline doc or skip discipline entirely.

**S18. Doctor LLM-phase termination.**
Decision: **Modified-on-accept.** Reframed after identifying the
root problem (LLM phase finding unwanted subjective issues).
Resolution:

- LLM-phase findings are split into two categories:
  - **Objective checks** (always run): internal contradiction,
    undefined terms, dangling references escaping static #12,
    spec↔history semantic drift, BCP 14 normative-context usage
    (mixed case per S9), Gherkin step semantic validity.
  - **Subjective checks** (skippable): NLSpec conformance beyond
    hard rules, template compliance semantic judgments,
    spec↔implementation drift, prose quality / structural
    suggestions.
- `.livespec.jsonc` adds:
  - `post_step_skip_subjective_checks: false` (default) — if
    `true`, post-step doctor after seed/propose-change/critique/
    revise skips subjective checks; explicit `livespec doctor`
    runs still include both.
  - `pre_step_skip_static_checks: false` (default) — if `true`,
    sub-commands skip the pre-step static check (emergency
    recovery).
- CLI flags `--skip-subjective-checks` and `--skip-pre-check`
  provide per-invocation override. Effective skip = config OR CLI.
- Warning printed whenever pre-step or subjective checks are
  skipped (via either mechanism) so users never silently operate
  in unsafe mode.
- Objective checks that happen to be LLM-driven MUST produce
  deterministic findings; if the LLM fails on an objective check,
  that is a logic error (LLM bug) reportable as such and
  remediable by re-run or different model.
- No dismissal / suppression persistence in v1. Post-step runs
  the full doctor only by default, but subjective noise is
  controlled via the skip flag.

### Smaller issues

**C19. Post-step doctor cascade risk.**
Decision: **Accepted (resolved by design).** After a successful
`revise`, the working tree is reconciled with `history/vNNN/`, so
check #9 doesn't fire during post-step. Cascade risk does not
materialize. No change needed; note in proposal.

**C20. `custom_critique_prompt` path existence check.**
Decision: **Dropped.** `custom_critique_prompt` itself is removed
from `.livespec.jsonc` (prompts live in the template). No path to
check.

**C21. Timestamp precision.**
Decision: **Accepted.** All timestamps in livespec artifacts use
second-precision ISO-8601: `YYYY-MM-DDTHH:MM:SSZ`.

**C22. `propose-change` overwrite confirmation asymmetry.**
Decision: **Accepted (unified).** Both `propose-change` and
`critique` auto-disambiguate on topic collision by appending a
short suffix. No user prompt in either case.

**C23. DoD LLM-driven check category count.**
Decision: **Accepted.** Drop the "four categories" count.
Re-enumerate precisely in the updated proposal (split objective
vs subjective per S18; list the checks that fall into each).

**C24. `scenarios.md` seed-time example.**
Decision: **Accepted.** Add a literal fenced markdown example in
the proposal showing the exact `scenarios.md` stub content that
seed produces.

**C25 / C26. `proposed_changes/` README regeneration.**
Decision: **Modified-on-accept.** The directory READMEs in
`proposed_changes/` and `history/` live at the **skill level**
(hard-coded, not template-owned). The skill writes them at `seed`
time only. The earlier "regenerated on every revise" rule is
dropped entirely.

**C27. Lifecycle diagram coverage of out-of-band flow.**
Decision: **Accepted.** Update the detailed lifecycle diagram to
show check #9's auto-backfill path (drift detection → auto
proposed-change → auto revision → history write → abort & commit
loop).

**C28. Custom template `intent` filename rule.**
Decision: **Modified-on-accept.** Rule is no longer inert because
custom templates are now in v1 scope (see M1 / template
architecture change). Formulation updated: "A custom template
SHOULD NOT use `intent` as a filename. Reason: `intent` is the
skill-level domain term for revision inputs; using it as a file
name in a template creates conceptual drag."

**C29. `scenarios.md` block-rendering contract target.**
Decision: **Accepted (GFM).** The rendering predictability
contract pins to GitHub-Flavored Markdown.

**C30. Meta-test heading-reference mechanism.**
Decision: **Modified-on-accept.** Use a **registry file**
`tests/heading-coverage.json` mapping each heading to the tests
that cover it. Meta-test cross-checks in both directions:

- Uncovered headings (in spec, not in registry) → fail with
  "heading X has no test."
- Orphaned registry entries (heading in registry, not in spec) →
  fail with "registry entry for heading 'OldName' is orphaned.
  Update the registry or the test."

Who writes and updates tests and registry is a livespec
implementation concern, not a proposal-level one.

**C31. Intent taxonomy → sub-command mapping.**
Decision: **Accepted.** Add one sentence: all intent
(observations, critiques, external requirements, implementation
feedback) flows through `propose-change` or `critique`; no other
ingress paths to the spec lifecycle.

---

## New decisions introduced during dialogue (not in the critique)

These were raised in dialogue and resolved alongside the critique
items. Captured here for completeness.

### Template architecture (Option 3)

- A template is a directory: `specification-templates/<name>/`
  with a fixed layout.
- Layout:
  ```
  specification-templates/livespec/
  ├── template.json                   # declares template_format_version only
  ├── livespec-nlspec-spec.md         # template-level discipline doc (optional per template)
  ├── prompts/
  │   ├── seed.md
  │   ├── revise.md
  │   └── critique.md
  └── specification-template/         # mirrors repo-root structure
      └── SPECIFICATION/
          ├── README.md
          ├── spec.md
          ├── contracts.md
          ├── constraints.md
          └── scenarios.md
  ```
- `template.json` contains only
  `{"template_format_version": 1}`. `prompts/` and
  `specification-template/` are fixed-by-convention paths;
  configuration is not permitted.
- `.livespec.jsonc` declares the expected
  `template_format_version` as a belt-and-suspenders sanity check;
  doctor validates both the template's declared version and the
  config's expected version match and are supported by livespec.

### Custom templates are in v1 scope

- The "pluggable template mechanism as a v1 non-goal" is removed.
- `.livespec.jsonc`'s `template` field accepts either a built-in
  name (`livespec`) or a path to a template directory.
- Doctor check #13 is reshaped: validates that the resolved
  template directory has required structure and that
  `template_format_version` is mutually supported.

### Prompts are part of the spec surface

- All skill↔template communication is JSON with schemas defined
  and enforced.
- Each template command prompt has a documented **input schema**
  (variables the skill passes) and **output schema** (what the
  prompt must emit).
- Skill validates output against schema; re-invokes on malformed
  output with error context; aborts after N retries.
- `jq` is a hard runtime dependency. Skill aborts at start with
  OS-appropriate install instructions if missing. LLMs can rely on
  `jq` in their prompts for JSON parsing.
- JSON Schemas are authored per livespec (hard-coded in the
  skill) and per template (ships with each template where
  relevant). The LLM can read and validate against schemas
  in-context.

### Architectural boundary: skill-level vs template-level prompts

**Skill-level** (in `SKILL.md` + per-sub-command files +
bundled scripts): owns sub-command dispatch, file I/O,
versioning, history creation, doctor static-phase invocation,
file-format validation (proposed-change format, revision format,
YAML front-matter schema), the JSON schemas that
template-emitted JSON must conform to, re-prompting on malformed
output, human-in-the-loop prompting.

**Template-level** (in `<template>/prompts/*.md` +
`<template>/specification-template/*`): owns content generation.
The template decides what each command does with its inputs
(intent, proposals, current spec) and produces structured
outputs conforming to skill-defined schemas. It does NOT write
files directly, manage versions, or prompt the user.

### Terminology renames

- `acknowledgement` → `revision` (file type and prose)
- `freeform text` (parameter) → `intent` (for `seed`, `propose-change`)
  and `additional-intent` (for `revise`)
- `partition` / `specification partition` → `specification file`
  (prose); `specification-file` / `specification-files` in JSON keys
- Skeleton terminology retired: the template's
  `specification-template/` dir contains actual starter content,
  not a "skeleton"
- `vNNN-` prefix on files inside `history/vNNN/` is dropped

### New sub-command: `prune-history`

Already documented above in S16's resolution.

### Drop of "openspec"

v002's `openspec` reservation is removed from v1 entirely.

---

## Self-consistency check

Post-revision invariants rechecked (per the embedded guidelines):

- **Two-implementer test:** template-format, skill packaging,
  JSON-schema-enforced communication, `jq` dependency, and
  explicit command contracts together close most remaining
  two-implementer divergences identified in v002.
- **Recreatability:** with this revision, a competent implementer
  can generate the livespec plugin, the `livespec` built-in
  template, and the skill's sub-commands from the updated
  PROPOSAL.md plus `livespec-nlspec-spec.md` alone.
- **Define-once:** consolidated the domain vocabulary (revision,
  intent, specification file) so that each concept is named in
  exactly one place.
- **Definition of Done:** retained and updated to reflect the new
  v1 scope (plugin delivery, custom templates in-scope, prune-history
  sub-command, JSON-schema-enforced skill↔template layer, renames).

## Outstanding follow-ups

Filed as the first batch of `propose-change`s after `seed`:

- Detailed authoring of each template prompt's input/output JSON
  schemas (`prompts/seed.md`, `prompts/revise.md`,
  `prompts/critique.md`) and corresponding schema files.
- Detailed authoring of the `bash-skill-script-style-requirements.md`
  companion (destined for `SPECIFICATION/constraints.md`).
- Migration steps for dogfooding: the brainstorming folder's
  content transformed into the official `SPECIFICATION/` layout
  under the `livespec` template.

## What was rejected

Nothing was rejected outright. Two classes of items were reshaped
during dialogue rather than accepted as written:

- The original "recreatability test" argument for S16 was rejected
  as misapplied; the motivation for seed preservation was
  reframed as audit-trail and lifecycle unification.
- My initial pushback on "v000" was rejected; the user's framing
  (v000 as the implicit empty pre-state) was adopted.
