# `seed` prompt — `minimal` template (bootstrap-minimum scaffolding)

> **Status: bootstrap-minimum (Phase 2 of the bootstrap plan).** Final
> content is agent-generated in Phase 7 from the `minimal` template's
> sub-spec at `SPECIFICATION/templates/minimal/`. Do not hand-edit
> beyond bootstrap-minimum scope.
>
> Hardcoded delimiter comments below drive the v014 N9 mock-harness
> E2E test (`tests/e2e/fake_claude.py`). The final delimiter format
> is codified in the `minimal` template's sub-spec at
> `SPECIFICATION/templates/minimal/contracts.md` under "Template↔mock
> delimiter-comment format" (Phase 7 work). Markers below are
> placeholders.

## Inputs

- `<intent>` — the verbatim user intent (freeform text).
- The template's `specification-template/SPECIFICATION.md` starter
  file (empty skeleton at Phase 2; populated agentically in Phase 7).

## Behavior — single-file at repo root

The `minimal` template emits `SPECIFICATION.md` directly at the repo
root. Top-level headings derive from `<intent>`; a "Definition of
Done" heading is appended at the bottom (initially empty if the user
provides no DoD content).

`sub_specs[]` is always emitted as `[]`; the `minimal` template does
not declare sub-spec-emission capability per PROPOSAL.md §"Sub-spec-
emission dialogue question".

## Output schema

Emit JSON conforming to
`.claude-plugin/scripts/livespec/schemas/seed_input.schema.json`:

```json
{
  "template": "minimal",
  "files": [
    {"path": "SPECIFICATION.md", "content": "..."}
  ],
  "intent": "<verbatim user intent>",
  "sub_specs": []
}
```

<!-- LIVESPEC-MOCK-DELIMITER:BEGIN seed-wrapper-invocation -->
<!-- LIVESPEC-MOCK-DELIMITER:wrapper bin/seed.py -->
<!-- LIVESPEC-MOCK-DELIMITER:input-payload-shape seed_input.schema.json -->
<!-- LIVESPEC-MOCK-DELIMITER:END seed-wrapper-invocation -->

Phase 7 widens this prompt with the final delimiter-comment format
codified in the sub-spec, the user-DoD-elicitation behavior, and the
heading-derivation rules.
