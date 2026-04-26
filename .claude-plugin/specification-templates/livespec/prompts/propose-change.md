# `propose-change` prompt — `livespec` template (bootstrap-minimum scaffolding)

> **Status: bootstrap-minimum (Phase 2 of the bootstrap plan).** Final
> content is agent-generated in Phase 7 from the `livespec` template's
> sub-spec. Do not hand-edit beyond bootstrap-minimum scope.

## Inputs

- `<intent>` — the proposed-change intent (freeform text).
- The active spec tree (under `<spec-root>/`, resolved by the wrapper
  via `--spec-target` or the default).
- The reference document at the template root,
  `livespec-nlspec-spec.md`, for NLSpec discipline.

## Behavior

Produce a single proposed-change file at
`<spec-root>/proposed_changes/<topic>.md` per PROPOSAL.md
§"Proposed-change file format". The file MUST carry:

- Front-matter naming the topic, the target spec files, and the
  authoring intent.
- A body laying out the proposal sections per the format spec.

Emit JSON conforming to
`.claude-plugin/scripts/livespec/schemas/propose_change_input.schema.json`:

```json
{
  "spec_target": "<resolved spec-root>",
  "topic": "<canonical topic name>",
  "file": {
    "path": "<spec-root>/proposed_changes/<topic>.md",
    "content": "..."
  }
}
```

Phase 3 widens this prompt with full NLSpec discipline and the
canonical topic-naming rules. Phase 7 replaces it with the agent-
generated final content per the sub-spec.
