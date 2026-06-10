# `critique` prompt — `livespec` template

> **Status: Phase-7-final per `SPECIFICATION/templates/livespec/contracts.md`
> §"Per-prompt semantic-property catalogue → prompts/critique.md".**
> Future regenerations land via dogfooded propose-change/revise
> against the sub-spec, atomically with their catalogue widening
> per Plan §3543-3550.

## Inputs

- The active spec tree (under `<spec-target>/`, resolved by the
  wrapper via `--spec-target` or the default
  `.livespec.jsonc`-walking behavior). Per v018 Q1, may target
  the main spec or any sub-spec.
- `input_context.current_spec_files` — the harness-passed
  enumeration of files that exist in the spec target at
  invocation time (e.g.,
  `["SPECIFICATION/spec.md", "SPECIFICATION/contracts.md", ...]`).
- Optional `<critique-steering-intent>` — user-provided guidance
  scoping the critique (e.g., "focus on contracts.md and
  scenarios.md").
- The reference document at the template root,
  `livespec-nlspec-spec.md`, for NLSpec discipline.

## Catalogue contract (`SPECIFICATION/templates/livespec/contracts.md`)

Two semantic properties are mechanically asserted by the
prompt-QA harness against this prompt's `replayed_response`:

- `findings_grounded_in_spec_target` — every entry in each
  finding's `target_spec_files` array is a path string present
  in `input_context.current_spec_files[]`. Findings referencing
  files outside the target tree are malformed.
- `prioritizes_ambiguity_over_style` — every finding's
  `motivation` field contains at least one ambiguity /
  contradiction lexicon keyword (`ambiguity`, `ambiguous`,
  `contradiction`, `contradicts`, `contradictory`, `unclear`,
  `inconsistent`, `inconsistency`, `silent`, `undefined`) —
  case-insensitive substring match. The lexicon is heuristic
  and intentionally permissive; richer semantic checks live in
  the doctor LLM-driven subjective phase.

The fuzzier dimensions (finding novelty, motivation depth,
proposed-change feasibility) are exercised by the doctor
LLM-driven subjective phase.

## Behavior

`critique` is a delegation surface — it produces
`proposal_findings.schema.json`-conforming output identical in
shape to `propose-change`, but the wrapper file-shapes it under
the topic's `-critique` reserve-suffix. Critique findings flow
through the same propose-change file format and become
`## Proposal: <name>` sections in
`<spec-target>/proposed_changes/<topic>-critique.md`.

The prompt's job is to surface ambiguities and contradictions
the user MIGHT want to address; whether to address each finding
is a downstream decision the user makes in the next
`propose-change` or `revise` cycle.

**Spec-target awareness.** The active `<spec-target>/` may be
main or sub-spec; emitted `target_spec_files` MUST reference
paths from `input_context.current_spec_files[]`.

**Reserve-suffix handling.** The `-critique` suffix is appended
by the wrapper; the prompt does NOT manipulate topic strings.

## Output schema

Same shape as `propose-change`: emit JSON conforming to
`.claude-plugin/scripts/livespec/schemas/proposal_findings.schema.json`:

```json
{
  "findings": [
    {
      "name": "<short-finding-name>",
      "target_spec_files": ["<spec-target-relative-path-from-current-spec-files>", "..."],
      "summary": "<one paragraph: what is ambiguous/contradictory and where>",
      "motivation": "<why this is a critique-worthy finding; MUST contain an ambiguity/contradiction lexicon keyword>",
      "proposed_changes": "<prose suggesting the corrective edit; uses BCP14>"
    }
  ]
}
```

## Failure modes

- **Schema-violation retry.**
  Same as the other LLM-driven prompts.
- **Empty critique** (no findings). When the prompt's review
  surfaces no ambiguities or contradictions, emit
  `findings: []`. The wrapper handles the empty-findings case
  per the propose-change empty-findings rules.
- **Wording-style suggestions.** When the user's
  steering-intent or the prompt's review surfaces
  wording-style suggestions (typos, paragraph organization,
  prose smoothing), the prompt SHOULD defer those to a
  separate cleanup-style propose-change cycle rather than
  emitting them as critique findings. The
  `prioritizes_ambiguity_over_style` assertion's lexicon
  match is the harness-layer enforcement; well-formed
  motivations naturally use the lexicon when describing
  load-bearing critique findings.
