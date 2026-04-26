# `critique` prompt — `livespec` template (bootstrap-minimum scaffolding)

> **Status: bootstrap-minimum (Phase 2 of the bootstrap plan).** Final
> content is agent-generated in Phase 7 from the `livespec` template's
> sub-spec. Do not hand-edit beyond bootstrap-minimum scope.

## Inputs

- The active spec tree (under `<spec-root>/`, resolved by the wrapper
  via `--spec-target` or the default), OR a single pending proposal
  under `<spec-root>/proposed_changes/<topic>.md`.
- The reference document at the template root,
  `livespec-nlspec-spec.md`, for NLSpec discipline.

## Behavior

Walk the spec (or proposal) and surface findings — ambiguities,
contradictions, missing rules, NLSpec-discipline violations — that
the user can act on. For each actionable finding, internally invoke
`propose-change` to land a proposed-change file under
`<spec-root>/proposed_changes/`; the critique sub-command's wrapper
forwards `--spec-target` uniformly to the propose-change delegation.

Emit one critique session record summarizing the findings raised and
which were acted on as proposed-change files.

Phase 3 widens this prompt with full NLSpec critique discipline and
the actionable-finding-to-proposed-change handoff contract. Phase 7
replaces it with the agent-generated final content per the sub-spec.
