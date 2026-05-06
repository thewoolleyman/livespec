# `doctor` LLM subjective-checks prompt — `livespec` template

> **Status: Phase-7-final per `SPECIFICATION/templates/livespec/contracts.md`
> §"Doctor-LLM-subjective-checks prompt".** Future regenerations
> land via dogfooded propose-change/revise against the sub-spec.

## Inputs

- The active spec tree (under `<spec-root>/`, resolved per the
  doctor wrapper's enumeration of main + sub-spec trees).
- The reference document at the template root,
  `livespec-nlspec-spec.md`, for NLSpec discipline. Read it
  internally to inform conformance evaluation; do not include
  its content verbatim in any output finding.
- The repo's source code surrounding the spec tree (for the
  spec↔implementation drift dimension). The doctor SKILL.md
  prose orchestrates which paths the LLM has read access to;
  this prompt assumes those reads have already happened.

## Behavior

Run the LLM-driven subjective-checks phase per PROPOSAL.md
§"LLM-driven subjective checks" (lines 2975-2998) and
SPECIFICATION/contracts.md §"Doctor-LLM-subjective-checks
prompt". Walk every file in the spec tree and emit findings
along each of the dimensions below. Each dimension is
non-deterministic — a "fail" finding here is a candidate for
the user's attention via the doctor SKILL.md per-finding
dialogue (Step 11), NOT a hard stop.

### Dimensions

For the built-in `livespec` template, the subjective-checks
prompt covers four dimensions, two skill-baked + two
template-extension (per):

1. **Spec↔implementation drift** (skill-baked). Compare the
   spec tree's stated contracts and constraints to the
   surrounding repo's source code. Surface meaningful
   divergences as findings — e.g., contracts.md says the
   wrapper accepts `--quiet` but the wrapper code doesn't
   implement it; constraints.md mandates Python 3.10+ but
   pyproject.toml's `requires-python` says `>=3.9`. Boilerplate
   divergences (renamed but-equivalent fields, harmless prose
   updates) are NOT findings.

2. **Prose quality and structural suggestions** (skill-baked).
   Suggest edits that improve spec readability:
   paragraphs that should be split, headings that should be
   merged or renamed, sentences whose BCP14 keyword is missing
   or weak (e.g., "should" lowercase where uppercase MUST or
   SHOULD applies). Stylistic edits unrelated to readability
   (e.g., comma-splice corrections) are deferred to a separate
   cleanup cycle.

3. **NLSpec conformance** (template-extension; livespec only).
   Evaluate the spec against the NLSpec discipline document at
   `../livespec-nlspec-spec.md`. Surface findings along three
   sub-dimensions:
   - **Economy**: prose says no more than necessary; redundant
     paragraphs, restated rules, or boilerplate examples are
     candidates for trimming.
   - **Conceptual fidelity**: every named concept is grounded
     in the spec's vocabulary; introduced terms are defined
     before use; analogies don't fight the underlying domain.
   - **Spec readability**: the reading order makes sense for a
     new contributor; cross-references resolve cleanly;
     section ordering supports the spec's argument.

4. **Template-compliance semantic judgments** (template-extension;
   livespec only). Verify that each spec file's content matches
   its semantic role per the `livespec` template's
   contracts/constraints/scenarios convention:
   - `spec.md` content addresses project intent and high-level
     architecture; contracts and constraints content does NOT
     leak in.
   - `contracts.md` content is wire-level / CLI-level; does NOT
     contain implementation prose or constraint declarations.
   - `constraints.md` content is architecture-level constraints;
     does NOT contain user-facing scenarios or wire-format
     specifics.
   - `scenarios.md` content is Gherkin scenarios with the
     blank-line-delimited format; does NOT contain prose
     paragraphs outside scenario blocks.

### Per-dimension scoring

For each finding, emit:

- `dimension`: one of `spec-impl-drift`, `prose-quality`,
  `nlspec-conformance`, `template-compliance`. Recorded inside
  the finding's `message` field as a structured prefix (e.g.,
  `[nlspec-conformance: economy] ...`) since the
  `doctor_findings.schema.json` does NOT carry a separate
  `dimension` field at v1. Future schema widening MAY split
  the dimension into its own field.
- `severity`: a qualitative `low` / `medium` / `high`
  judgment encoded inside the `message` field's structured
  prefix (e.g., `[severity: medium] ...`). The doctor static
  phase's `pass`/`fail`/`skipped` enum doesn't have a severity
  axis; the LLM-driven phase encodes severity prose-side for
  the per-finding user dialogue at the SKILL.md layer.

## Output schema

Emit JSON conforming to
`.claude-plugin/scripts/livespec/schemas/doctor_findings.schema.json`:

```json
{
  "findings": [
    {
      "check_id": "doctor-llm-subjective-<dimension>",
      "status": "fail",
      "message": "[severity: <low|medium|high>] <one-sentence finding>",
      "path": "<spec-root-relative path or ''>",
      "line": <line number or 0>,
      "spec_root": "<spec_root path>"
    }
  ]
}
```

`status` is always `fail` for surfaced findings — the
LLM-driven subjective phase emits findings only when something
warrants the user's attention. Empty findings (no issues)
results in a `findings: []` payload.

`check_id` uses the `doctor-llm-subjective-` prefix to
distinguish from the static-phase check IDs; the dimension
suffix scopes per-dimension.

## Failure modes

- **Schema-violation retry.**
  Same as the other LLM-driven prompts. The doctor SKILL.md
  re-invokes with the error context.
- **Long-running review.** When the spec tree is large enough
  that exhaustive review would exceed reasonable LLM context,
  the prompt SHOULD emit findings for the highest-severity
  issues encountered + a summary finding noting the partial
  coverage (e.g., `[severity: low] Reviewed spec.md and
  contracts.md exhaustively; constraints.md and scenarios.md
  reviewed at high level only — re-run for deep coverage`).
- **Empty / well-formed spec.** When the prompt's review
  surfaces no issues, emit `findings: []`. The doctor SKILL.md
  surfaces this as "all subjective checks passed" without
  per-finding dialogue.
