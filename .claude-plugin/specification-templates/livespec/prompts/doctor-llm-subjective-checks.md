# `doctor` LLM subjective-checks prompt — `livespec` template (bootstrap-minimum stub)

> **Status: bootstrap-minimum stub (Phase 2 of the bootstrap plan).**
> Final content is agent-generated in Phase 7 from the `livespec`
> template's sub-spec. Do not hand-edit beyond bootstrap-minimum
> scope.

## Inputs

- The active spec tree (under `<spec-root>/`).
- The reference document at the template root,
  `livespec-nlspec-spec.md`, for NLSpec discipline.

## Behavior

Run the LLM-driven subjective-checks phase per PROPOSAL.md
§"Doctor — LLM-driven phase". Surface findings against the active
spec tree along subjective dimensions — readability, consistency of
voice, NLSpec adherence beyond what static checks can mechanically
verify, completeness of scenarios coverage, etc.

Emit findings in the structured `Finding` payload shape per
PROPOSAL.md §"Finding payload shape".

Phase 7 widens this prompt with the full subjective-checks dimension
list and the per-dimension scoring rubric, agent-generated from the
sub-spec.
