# `seed` prompt — `livespec` template (bootstrap-minimum per v020 Q4)

> **Status: bootstrap-minimum (Phase 3 widening per v020 Q4).** Final
> content is agent-generated in Phase 7 from the `livespec` template's
> sub-spec at `SPECIFICATION/templates/livespec/`. Do not hand-edit
> beyond the bootstrap-minimum scope; per PROPOSAL.md §"Template
> sub-specifications" v018 Q2, post-Phase-7 mutations flow through the
> dogfooded propose-change → revise loop against the sub-spec.

## Inputs

- `<intent>` — the verbatim user intent (freeform text from the
  pre-seed dialogue captured by `seed/SKILL.md`).
- The chosen template name (one of `livespec`, `minimal`, or a
  user-provided template path).
- The user's answer to the v020 Q2 sub-spec-emission question:
  "Does this project ship its own livespec templates that should be
  governed by sub-spec trees under `SPECIFICATION/templates/<name>/`?"
- On a "yes" answer: the list of template directory names (e.g.,
  `livespec`, `minimal`) named in the follow-on dialogue.
- The reference document at the template root,
  `livespec-nlspec-spec.md`, which describes NLSpec discipline. Read
  it internally to inform spec-file authoring; do not include its
  content verbatim in any output file.

## Behavior — `sub_specs[]` emission branches (v020 Q2)

- **"no" branch (the default and typical end-user case).** Emit
  `sub_specs: []` in the output JSON.
- **"yes" branch (the meta-project case — livespec itself, plus any
  user project that ships its own livespec templates).** For each
  template directory name supplied in the follow-on dialogue, emit
  one `SubSpecPayload` entry under `sub_specs[]` carrying:
  - `template_name`: matches the template's directory name.
  - `files[]`: the full sub-spec file set under
    `SPECIFICATION/templates/<template_name>/` per PROPOSAL.md
    §"Template sub-specifications" — uniformly multi-file:
    `spec.md`, `contracts.md`, `constraints.md`, `scenarios.md`,
    `README.md`.

Both branches handle the user's `<intent>` rigorously: every
spec-file's content reflects the intent; sub-spec content
describes the corresponding template's NLSpec discipline.

## Output schema

Emit JSON conforming to
`.claude-plugin/scripts/livespec/schemas/seed_input.schema.json`:

```json
{
  "template": "livespec",
  "intent": "<verbatim user intent>",
  "files": [
    {"path": "SPECIFICATION/spec.md", "content": "..."},
    {"path": "SPECIFICATION/contracts.md", "content": "..."},
    {"path": "SPECIFICATION/constraints.md", "content": "..."},
    {"path": "SPECIFICATION/scenarios.md", "content": "..."},
    {"path": "SPECIFICATION/README.md", "content": "..."}
  ],
  "sub_specs": []
}
```

For the "yes" branch with `["livespec", "minimal"]` as the named
templates, the same payload's `sub_specs[]` becomes:

```json
"sub_specs": [
  {
    "template_name": "livespec",
    "files": [
      {"path": "SPECIFICATION/templates/livespec/spec.md", "content": "..."},
      {"path": "SPECIFICATION/templates/livespec/contracts.md", "content": "..."},
      {"path": "SPECIFICATION/templates/livespec/constraints.md", "content": "..."},
      {"path": "SPECIFICATION/templates/livespec/scenarios.md", "content": "..."},
      {"path": "SPECIFICATION/templates/livespec/README.md", "content": "..."}
    ]
  },
  {
    "template_name": "minimal",
    "files": [
      {"path": "SPECIFICATION/templates/minimal/spec.md", "content": "..."},
      {"path": "SPECIFICATION/templates/minimal/contracts.md", "content": "..."},
      {"path": "SPECIFICATION/templates/minimal/constraints.md", "content": "..."},
      {"path": "SPECIFICATION/templates/minimal/scenarios.md", "content": "..."},
      {"path": "SPECIFICATION/templates/minimal/README.md", "content": "..."}
    ]
  }
]
```

Phase 7 replaces this prompt entirely with the agent-generated
final content per the sub-spec, regenerated from
`SPECIFICATION/templates/livespec/` via the dogfooded
propose-change/revise loop.
