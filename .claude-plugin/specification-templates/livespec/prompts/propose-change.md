# `propose-change` prompt — `livespec` template

> **Status: Phase-7-final per `SPECIFICATION/templates/livespec/contracts.md`
> §"Per-prompt semantic-property catalogue → prompts/propose-change.md".**
> Future regenerations land via dogfooded propose-change/revise
> against the sub-spec, atomically with their catalogue widening
> per Plan §3543-3550.

## Inputs

- `<intent>` — the proposed-change intent (freeform user text from
  `propose-change/SKILL.md` dialogue).
- `<topic>` — the canonical kebab-case topic identifier (already
  user-validated by SKILL.md prose).
- `input_context.spec_target` — the active spec tree path (under
  `<spec-target>/`, resolved by the wrapper via `--spec-target`
  or the default `.livespec.jsonc`-walking behavior). Per v018 Q1,
  may target either the main spec or any sub-spec under
  `<main-spec-root>/templates/<name>/` — the prompt is
  spec-target-agnostic; the SKILL.md layer handles routing.
- The reference document at the template root,
  `livespec-nlspec-spec.md`, for NLSpec discipline.

## Catalogue contract (`SPECIFICATION/templates/livespec/contracts.md`)

Two semantic properties are mechanically asserted by the
prompt-QA harness against this prompt's `replayed_response`:

- `target_files_within_spec_target` — every entry in each
  finding's `target_spec_files` array is a path string whose
  prefix matches `input_context.spec_target` (treating both as
  POSIX-relative paths). Findings referencing paths outside the
  spec target are malformed.
- `bcp14_in_proposed_changes` — every finding's `proposed_changes`
  string contains at least one BCP14 keyword (whole-word,
  uppercase: `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY`,
  `MAY NOT`). The proposed-change prose flows into the spec under
  the same normative-language discipline as the spec itself, so
  the prompt SHOULD apply BCP14 in proposed-change authoring.

The fuzzier dimensions (proposal-name informativeness, motivation
groundedness, summary coverage of the changes) are exercised by
the `prompts/critique.md` and `prompts/doctor-llm-subjective-checks.md`
phases.

## Behavior

Produce a JSON `findings[]` array, where each finding becomes one
`## Proposal: <name>` section in the resulting proposed-change
file at `<spec-target>/proposed_changes/<topic>.md`. The wrapper
performs the field-to-section mapping per PROPOSAL.md
§"propose-change" lines 2236-2242:

- `name` → `## Proposal: <name>` heading.
- `target_spec_files` → `### Target specification files`
  (one path per line; the prompt MUST emit paths under
  `input_context.spec_target`).
- `summary` → `### Summary` body (one paragraph stating what
  changes and why).
- `motivation` → `### Motivation` body (the intent input that
  produced this finding).
- `proposed_changes` → `### Proposed Changes` body (prose, or a
  unified diff in fenced ` ```diff ` blocks, or both — using
  BCP14 normative language).

**Reserve-suffix awareness.** The wrapper takes the topic
verbatim. When this prompt is invoked via `critique`'s internal
delegation, the topic will already carry the `-critique`
reserve-suffix. Do not strip suffixes; do not append them. That
is the wrapper's job.

**Spec-target awareness.** The active `<spec-target>/` may be
either the main spec root (e.g., `SPECIFICATION/`) or a sub-spec
tree (e.g., `SPECIFICATION/templates/livespec/`). Authored
content references MUST use spec-target-relative paths
consistently; the wrapper does not rewrite paths between
contexts.

## Output schema

Emit JSON conforming to
`.claude-plugin/scripts/livespec/schemas/proposal_findings.schema.json`:

```json
{
  "findings": [
    {
      "name": "<short-proposal-name>",
      "target_spec_files": ["<spec-target-relative-path>", "..."],
      "summary": "<one paragraph: what changes and why>",
      "motivation": "<the intent that produced this proposal>",
      "proposed_changes": "<prose or fenced diff describing the changes; MUST use BCP14 keywords>"
    }
  ]
}
```

A propose-change invocation MAY emit multiple findings to bundle
several related proposals into a single file; each finding
becomes its own `## Proposal:` section. Single-finding payloads
are typical for narrow changes; multi-finding payloads are typical
for broader cycles like full feature parity widening (e.g., the
6.a prune-history-full-feature-parity propose-change bundled three
related findings).

## Failure modes

- **Schema-violation retry.**
  When the wrapper exits 4 with a `fastjsonschema` validation
  error, the SKILL.md prose re-invokes this prompt with the
  error context appended; the LLM repairs the offending field.
- **Out-of-scope target paths.** When the user's intent
  references files outside `input_context.spec_target`, the
  prompt SHOULD scope the proposal to just the in-target files
  and surface the out-of-target reference in the `motivation`
  body (rather than emitting a malformed `target_spec_files`
  array). The `target_files_within_spec_target` assertion
  catches malformed payloads at the harness layer; this
  guidance avoids emitting them.
- **Missing BCP14.** When the user's intent prose lacks
  normative language, the prompt MUST translate the intent into
  BCP14 keywords during authoring (e.g., user "we should add
  X" becomes "the system MUST emit X" or "the system SHOULD
  emit X" depending on context). The `bcp14_in_proposed_changes`
  assertion catches all-prose-no-keywords payloads at the
  harness layer.
