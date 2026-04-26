# `revise` prompt — `minimal` template (bootstrap-minimum scaffolding)

> **Status: bootstrap-minimum (Phase 2 of the bootstrap plan).** Final
> content is agent-generated in Phase 7. Hardcoded delimiter markers
> below are placeholders; final format is codified in
> `SPECIFICATION/templates/minimal/contracts.md` (Phase 7).

## Inputs

- The active `SPECIFICATION.md` at the repo root.
- Every pending proposal under `./proposed_changes/`.

## Behavior

For each pending proposal, walk the user through accept / reject /
modify decisions. A `revise` invocation that finds zero pending
proposals MUST fail hard. A `revise` invocation that processes
proposals but rejects all of them MUST still cut a new version
(audit-trail invariant per PROPOSAL.md §"Versioning").

Snapshot the result as a new `./history/v<N+1>/` directory.

Emit JSON conforming to
`.claude-plugin/scripts/livespec/schemas/revise_input.schema.json`:

```json
{
  "spec_target": ".",
  "next_version": "<vNNN>",
  "files": [
    {"path": "SPECIFICATION.md", "content": "..."},
    {"path": "./history/<vNNN>/revision-<topic>.md", "content": "..."}
  ]
}
```

<!-- LIVESPEC-MOCK-DELIMITER:BEGIN revise-wrapper-invocation -->
<!-- LIVESPEC-MOCK-DELIMITER:wrapper bin/revise.py -->
<!-- LIVESPEC-MOCK-DELIMITER:input-payload-shape revise_input.schema.json -->
<!-- LIVESPEC-MOCK-DELIMITER:END revise-wrapper-invocation -->
