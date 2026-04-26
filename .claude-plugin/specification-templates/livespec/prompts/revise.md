# `revise` prompt — `livespec` template (bootstrap-minimum scaffolding)

> **Status: bootstrap-minimum (Phase 2 of the bootstrap plan).** Final
> content is agent-generated in Phase 7 from the `livespec` template's
> sub-spec. Do not hand-edit beyond bootstrap-minimum scope.

## Inputs

- The active spec tree (under `<spec-root>/`, resolved by the wrapper
  via `--spec-target` or the default).
- Every pending proposal under `<spec-root>/proposed_changes/`.
- The reference document at the template root,
  `livespec-nlspec-spec.md`, for NLSpec discipline.

## Behavior

For each pending proposal, walk the user through accept / reject /
modify decisions per PROPOSAL.md §"`revise`". A `revise` invocation
that finds zero pending proposals MUST fail hard. A `revise`
invocation that processes proposals but rejects all of them MUST
still cut a new version (audit-trail invariant).

Snapshot the result as a new `<spec-root>/history/v<N+1>/` directory
containing:

- The revised spec files.
- The proposed-change files (carried forward from
  `proposed_changes/`).
- The per-proposal `revision.md` files documenting the per-proposal
  decision and rationale.

Emit JSON conforming to
`.claude-plugin/scripts/livespec/schemas/revise_input.schema.json`:

```json
{
  "spec_target": "<resolved spec-root>",
  "next_version": "<vNNN>",
  "files": [
    {"path": "<spec-root>/spec.md", "content": "..."},
    {"path": "<spec-root>/history/<vNNN>/revision-<topic>.md", "content": "..."}
  ]
}
```

Phase 3 widens this prompt with full NLSpec discipline, the per-
proposal accept/reject/modify decision flow, and the version-cutting
contract. Phase 7 replaces it with the agent-generated final content.
