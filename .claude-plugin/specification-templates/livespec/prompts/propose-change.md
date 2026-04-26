# `propose-change` prompt — `livespec` template (bootstrap-minimum per v020 Q4)

> **Status: bootstrap-minimum (Phase 3 widening per v020 Q4).** Final
> content is agent-generated in Phase 7 from the `livespec` template's
> sub-spec. Do not hand-edit beyond bootstrap-minimum scope.

## Inputs

- `<intent>` — the proposed-change intent (freeform user text from
  `propose-change/SKILL.md` dialogue).
- `<topic>` — the canonical kebab-case topic identifier (already
  user-validated by SKILL.md prose; Phase 3 minimum-viable rejects
  non-canonical values with exit 4).
- The active spec tree (under `<spec-target>/`, resolved by the
  wrapper via `--spec-target` or the default
  `.livespec.jsonc`-walking behavior). Per v018 Q1, may target
  either the main spec or any sub-spec under
  `<main-spec-root>/templates/<name>/` — the prompt is
  spec-target-agnostic; the SKILL.md layer handles routing.
- The reference document at the template root,
  `livespec-nlspec-spec.md`, for NLSpec discipline.

## Behavior

Produce a JSON `findings[]` array, where each finding becomes one
`## Proposal: <name>` section in the resulting proposed-change
file at `<spec-target>/proposed_changes/<topic>.md`. The wrapper
performs the field-to-section mapping per PROPOSAL.md
§"propose-change" lines 2236-2242:

- `name` → `## Proposal: <name>` heading.
- `target_spec_files` → `### Target specification files`
  (one path per line; spec-target-relative or repo-root-relative).
- `summary` → `### Summary` body (one paragraph).
- `motivation` → `### Motivation` body (the intent input).
- `proposed_changes` → `### Proposed Changes` body (prose, or a
  unified diff in fenced ` ```diff ` blocks, or both).

**Reserve-suffix awareness.** The propose-change wrapper itself
takes the topic verbatim (Phase 3 minimum-viable). When this
prompt is invoked via `critique`'s internal delegation (Phase 7
widens this), the topic will already carry the `-critique`
reserve-suffix. Do not strip suffixes; do not append them.
That's the wrapper's job.

**Spec-target awareness.** The active `<spec-target>/` may be
either the main spec root (e.g., `SPECIFICATION/`) or a sub-spec
tree (e.g., `SPECIFICATION/templates/livespec/`). Authored
content references should use spec-target-relative paths
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
      "target_spec_files": ["<repo-relative-path>", "..."],
      "summary": "<one paragraph: what changes and why>",
      "motivation": "<the intent that produced this proposal>",
      "proposed_changes": "<prose or fenced diff describing the changes>"
    }
  ]
}
```

A propose-change invocation MAY emit multiple findings to bundle
several related proposals into a single file; each finding
becomes its own `## Proposal:` section. For Phase 3
minimum-viable's first dogfooded cycle, single-finding payloads
are typical.

Phase 3 widens this prompt with the canonical NLSpec discipline
for proposal authoring. Phase 7 replaces it with the
agent-generated final content per the `livespec` template's
sub-spec, regenerated via dogfood.
