# `propose-change` prompt — `minimal` template

<!-- livespec-harness-command: propose-change -->

> **Status: Phase-7-final per `SPECIFICATION/templates/minimal/contracts.md`
> §"Per-prompt semantic-property catalogue → prompts/propose-change.md".**
> Future regenerations land via dogfooded propose-change/revise
> against the minimal template's sub-spec.

## Inputs

- `<intent>` — the proposed-change intent (freeform text from
  `propose-change/SKILL.md` dialogue).
- `<topic>` — the canonical kebab-case topic identifier.
- `input_context.spec_target` — the active spec target. For the
  `minimal` template this is always `"./"` (the project root)
  per the template's `spec_root: "./"` declaration.
- The active `SPECIFICATION.md` at the project root.

## Catalogue contract (`SPECIFICATION/templates/minimal/contracts.md`)

Two semantic properties are mechanically asserted by the
prompt-QA harness:

- `target_is_single_specification_md` — every entry in each
  finding's `target_spec_files` array equals exactly
  `["SPECIFICATION.md"]`. The minimal template's single-file
  output means every proposal targets exactly the one path.
- `bcp14_in_proposed_changes` — every finding's
  `proposed_changes` prose contains at least one BCP14
  keyword (whole-word, uppercase: `MUST`, `MUST NOT`,
  `SHOULD`, `SHOULD NOT`, `MAY`, `MAY NOT`).

## Behavior

Produce a JSON `findings[]` array where each finding becomes
one `## Proposal: <name>` section in the resulting
proposed-change file at `./proposed_changes/<topic>.md`.

When the user's intent describes a region-scoped edit (e.g.,
"tighten the cadence section"), the proposed_changes prose
SHOULD reference the corresponding region name from the
delimiter-comment format (per
`SPECIFICATION/templates/minimal/contracts.md` §"Delimiter-
comment format" v002+). The wrapper does not enforce
region-scoping at the schema level; this is a prose-quality
convention so propose-change cycles compose cleanly with
revise's region-targeted edit application.

**Spec-target awareness.** The minimal template's
`spec_target` is always `"./"`; `target_spec_files` always
points at `SPECIFICATION.md`. The single-file design means
there's no multi-file scope to disambiguate.

## Output schema

Emit JSON conforming to
`.claude-plugin/scripts/livespec/schemas/proposal_findings.schema.json`:

```json
{
  "findings": [
    {
      "name": "<short-proposal-name>",
      "target_spec_files": ["SPECIFICATION.md"],
      "summary": "<one paragraph: what changes and why>",
      "motivation": "<the intent that produced this proposal>",
      "proposed_changes": "<prose using BCP14 keywords; region:<name> reference when applicable>"
    }
  ]
}
```

`target_spec_files` MUST equal exactly `["SPECIFICATION.md"]`
for every finding — the harness's
`target_is_single_specification_md` assertion enforces this.
`proposed_changes` MUST contain at least one BCP14 keyword
— the `bcp14_in_proposed_changes` assertion enforces this.

## Failure modes

- **Schema-violation retry (PROPOSAL.md §"Retry-on-exit-4").**
  Same as the other LLM-driven prompts.
- **Multi-file intent.** When the user's intent suggests
  multiple files, the prompt MUST consolidate everything into
  a single finding (or multiple findings, all targeting
  `SPECIFICATION.md`). The minimal template doesn't have a
  multi-file destination; the `livespec` template is the
  multi-file alternative.
- **Missing BCP14.** When the user's intent prose lacks
  normative language, the prompt MUST translate the intent
  into BCP14 keywords during authoring.
