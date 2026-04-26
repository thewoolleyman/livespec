# `propose-change` prompt — `minimal` template (bootstrap-minimum scaffolding)

> **Status: bootstrap-minimum (Phase 2 of the bootstrap plan).** Final
> content is agent-generated in Phase 7. Hardcoded delimiter markers
> below are placeholders; final format is codified in
> `SPECIFICATION/templates/minimal/contracts.md` (Phase 7).

## Inputs

- `<intent>` — the proposed-change intent (freeform text).
- The active `SPECIFICATION.md` at the repo root (since
  `spec_root: "./"`).

## Behavior

Produce a single proposed-change file at
`./proposed_changes/<topic>.md` per PROPOSAL.md §"Proposed-change
file format".

Emit JSON conforming to
`.claude-plugin/scripts/livespec/schemas/propose_change_input.schema.json`:

```json
{
  "spec_target": ".",
  "topic": "<canonical topic name>",
  "file": {
    "path": "./proposed_changes/<topic>.md",
    "content": "..."
  }
}
```

<!-- LIVESPEC-MOCK-DELIMITER:BEGIN propose-change-wrapper-invocation -->
<!-- LIVESPEC-MOCK-DELIMITER:wrapper bin/propose_change.py -->
<!-- LIVESPEC-MOCK-DELIMITER:input-payload-shape propose_change_input.schema.json -->
<!-- LIVESPEC-MOCK-DELIMITER:END propose-change-wrapper-invocation -->
