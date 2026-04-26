# `critique` prompt — `minimal` template (bootstrap-minimum scaffolding)

> **Status: bootstrap-minimum (Phase 2 of the bootstrap plan).** Final
> content is agent-generated in Phase 7. Hardcoded delimiter markers
> below are placeholders; final format is codified in
> `SPECIFICATION/templates/minimal/contracts.md` (Phase 7).

## Inputs

- The active `SPECIFICATION.md` at the repo root, OR a single pending
  proposal under `./proposed_changes/<topic>.md`.

## Behavior

Walk the spec (or proposal) and surface findings. For each actionable
finding, internally invoke `propose-change` to land a proposed-change
file under `./proposed_changes/`; the wrapper forwards `--spec-target`
uniformly.

Note: the `gherkin-blank-line-format` doctor-static check is
conditional on the `livespec` template per PROPOSAL.md §"Static-phase
checks" and does NOT apply when the active template is `minimal`.

<!-- LIVESPEC-MOCK-DELIMITER:BEGIN critique-wrapper-invocation -->
<!-- LIVESPEC-MOCK-DELIMITER:wrapper bin/critique.py -->
<!-- LIVESPEC-MOCK-DELIMITER:input-payload-shape critique_input.schema.json -->
<!-- LIVESPEC-MOCK-DELIMITER:END critique-wrapper-invocation -->
