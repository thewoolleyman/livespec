# `seed` prompt — `minimal` template

<!-- livespec-harness-command: seed -->

> **Status: Phase-7-final per `SPECIFICATION/templates/minimal/contracts.md`
> §"Per-prompt semantic-property catalogue → prompts/seed.md".**
> Future regenerations land via dogfooded propose-change/revise
> against the minimal template's sub-spec, atomically with their
> catalogue widening per Plan §3543-3550.

## Inputs

- `<intent>` — the verbatim user intent (freeform text from the
  pre-seed dialogue).
- The chosen template name (always `"minimal"` for this prompt;
  the skill resolves which template's prompt to load before
  invoking the LLM).

The `minimal` template does NOT consume the v020 Q2 sub-spec
emission question — its catalogue contract pins
`sub_specs: []` regardless of any pre-seed dialogue input.

## Catalogue contract (`SPECIFICATION/templates/minimal/contracts.md`)

Two semantic properties are mechanically asserted by the
prompt-QA harness against this prompt's `replayed_response`:

- `sub_specs_always_empty` — `replayed_response.sub_specs` is
  the empty list `[]` regardless of any pre-seed dialogue
  input. The `minimal` template implements the v020 Q2 opt-out;
  its single-file output has no sub-spec dimension.
- `single_specification_md_file` — `replayed_response.files[]`
  is exactly one entry whose `path` field equals
  `"SPECIFICATION.md"`. The `minimal` template's `template.json`
  declares `spec_root: "./"`; the single file lands at the
  project root rather than under a `SPECIFICATION/` subdirectory.

## Behavior — single-file at project root

The `minimal` template emits `SPECIFICATION.md` directly at the
project root. The file body uses HTML-comment delimiter markers
to define named regions per `SPECIFICATION/templates/minimal/
contracts.md` §"Delimiter-comment format" (concrete syntax:
`<!-- region:<name> -->` open + `<!-- /region:<name> -->`
close); subsequent propose-change/revise cycles target regions
precisely rather than rewriting the whole file.

The H1 reflects the user's intent (per the
`headings_derived_from_intent` discipline shared with the
livespec template). Region content is intent-derived; a typical
single-file output carries 3-5 regions covering project intent,
constraints, and any user-provided cadence/governance rules.

## Authoring guidance

Within the single `SPECIFICATION.md` file, recommended regions
(authored as `<!-- region:<name> -->` ... `<!-- /region:<name> -->`
pairs):

- `project-intent` — what the project is and what problem it
  solves (always present).
- `cadence` — review cadence + escalation rules (when the user's
  intent describes operational rhythm).
- `dod` — Definition of Done for changes (always present, even
  if initially minimal).
- Additional regions named after the user's intent vocabulary
  (e.g., `release-policy`, `platform-support`, ...).

Region names MUST be kebab-case alphanumeric per the contracts.md
delimiter-comment format invariants.

## Output schema

Emit JSON conforming to
`.claude-plugin/scripts/livespec/schemas/seed_input.schema.json`:

```json
{
  "template": "minimal",
  "intent": "<verbatim user intent>",
  "files": [
    {
      "path": "SPECIFICATION.md",
      "content": "# `<intent-derived-title>`\n\n<!-- region:project-intent -->\n\n...\n\n<!-- /region:project-intent -->\n\n<!-- region:dod -->\n\n...\n\n<!-- /region:dod -->\n"
    }
  ],
  "sub_specs": []
}
```

`files[]` MUST have exactly one entry; `sub_specs[]` MUST be the
empty list. The harness's `single_specification_md_file` and
`sub_specs_always_empty` assertions enforce both at the
fixture-evaluation layer.

## Failure modes

- **Schema-violation retry.**
  Same as the other LLM-driven prompts.
- **Thin intent.** When `<intent>` is too sparse to populate
  meaningful regions, the SKILL.md prose handles re-prompting
  via the pre-seed dialogue rather than the prompt emitting a
  malformed payload.
- **Multi-file intent.** When the user's intent suggests
  multiple files (e.g., "spec.md plus a contracts.md"), the
  prompt MUST consolidate everything into the single
  `SPECIFICATION.md` (with regions per topic). The user can
  switch to the `livespec` template via re-seed if a
  multi-file structure is required.
