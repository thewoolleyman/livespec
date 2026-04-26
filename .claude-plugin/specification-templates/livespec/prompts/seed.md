# `seed` prompt — `livespec` template (bootstrap-minimum scaffolding)

> **Status: bootstrap-minimum (Phase 2 of the bootstrap plan).** Final
> content is agent-generated in Phase 7 from the `livespec` template's
> sub-spec at `SPECIFICATION/templates/livespec/`. Do not hand-edit
> beyond the bootstrap-minimum scope; per PROPOSAL.md §"Template
> sub-specifications" v018 Q2, post-Phase-7 mutations flow through the
> dogfooded propose-change → revise loop against the sub-spec.

## Inputs

- `<intent>` — the verbatim user intent (freeform text).
- The template's `specification-template/` starter content (empty
  skeleton at Phase 2; populated agentically in Phase 7).
- The reference document at the template root,
  `livespec-nlspec-spec.md`, which describes NLSpec discipline. Read
  it internally to inform spec-file authoring; do not include its
  content verbatim in any output file.

## Pre-seed dialogue (handled by `seed/SKILL.md` BEFORE invoking this prompt)

`seed/SKILL.md` prose performs the pre-seed template-selection
dialogue and the v020 Q2 sub-spec-emission dialogue question:

> "Does this project ship its own livespec templates that should be
> governed by sub-spec trees under `SPECIFICATION/templates/<name>/`?
> (default: no)"

The user's answer is passed into this prompt as a directive to emit
either an empty `sub_specs[]` list (the typical end-user case) or one
`SubSpecPayload` per template named in the follow-on dialogue (the
meta-project case — livespec itself, and any user project that ships
its own livespec templates).

## Behavior — `sub_specs[]` emission branches

- **"no" branch (default).** Emit `sub_specs: []` in the output JSON.
- **"yes" branch (meta-project case).** For each template directory
  name supplied in the follow-on dialogue, emit one `SubSpecPayload`
  entry under `sub_specs[]` carrying:
  - `template_name`: matches the template's directory name under
    `.claude-plugin/specification-templates/<name>/` (or the
    project-specific equivalent).
  - `files[]`: the full sub-spec file set under
    `SPECIFICATION/templates/<template_name>/` per PROPOSAL.md §"Template
    sub-specifications" — `spec.md`, `contracts.md`, `constraints.md`,
    `scenarios.md`, `README.md`, plus the per-version
    `history/v001/README.md` snapshot.

## Output schema

Emit JSON conforming to
`.claude-plugin/scripts/livespec/schemas/seed_input.schema.json`:

```json
{
  "template": "livespec",
  "files": [
    {"path": "SPECIFICATION/spec.md", "content": "..."},
    {"path": "SPECIFICATION/contracts.md", "content": "..."},
    {"path": "SPECIFICATION/constraints.md", "content": "..."},
    {"path": "SPECIFICATION/scenarios.md", "content": "..."},
    {"path": "SPECIFICATION/README.md", "content": "..."}
  ],
  "intent": "<verbatim user intent>",
  "sub_specs": []
}
```

Phase 3 widens this prompt with full NLSpec authoring discipline,
heading-coverage compliance, and the rigorous per-branch handling of
the `sub_specs[]` emission paths. Phase 7 then replaces this prompt
entirely with the agent-generated final content per the sub-spec.
