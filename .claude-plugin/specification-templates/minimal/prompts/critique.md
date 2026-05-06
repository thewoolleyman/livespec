# `critique` prompt — `minimal` template

> **Status: Phase-7-final per `SPECIFICATION/templates/minimal/contracts.md`
> §"Per-prompt semantic-property catalogue → prompts/critique.md".**

## Inputs

- The active `SPECIFICATION.md` at the project root.
- `input_context.spec_target` — always `"./"` for the minimal
  template (per `spec_root: "./"`).
- Optional `<critique-steering-intent>` — user-provided
  guidance scoping the critique.

## Catalogue contract (`SPECIFICATION/templates/minimal/contracts.md`)

Two semantic properties are mechanically asserted by the
prompt-QA harness:

- `target_is_single_specification_md` — every entry in each
  finding's `target_spec_files` array equals exactly
  `["SPECIFICATION.md"]`. The minimal template's single-file
  output means every critique finding targets exactly one
  path. (Same registry function as the propose-change
  catalogue's identically-named property.)
- `prioritizes_ambiguity_over_style` — every finding's
  `motivation` field contains at least one ambiguity /
  contradiction lexicon keyword (`ambiguity`, `ambiguous`,
  `contradiction`, `contradicts`, `contradictory`, `unclear`,
  `inconsistent`, `inconsistency`, `silent`, `undefined`) —
  case-insensitive substring match.

## Behavior

`critique` is a delegation surface for the minimal template
(same shape as the livespec-template critique). Surface
findings about ambiguities and contradictions in
`SPECIFICATION.md`; each finding becomes one `## Proposal:
<name>` section in
`./proposed_changes/<topic>-critique.md` after the wrapper
processes it.

Note: the `gherkin-blank-line-format` doctor-static check is
conditional on the `livespec` template per PROPOSAL.md
§"Static-phase checks" and does NOT apply when the active
template is `minimal`. Critique findings about Gherkin
formatting in the minimal template's `SPECIFICATION.md` are
out of scope (the minimal template doesn't ship Gherkin
scenarios).

**Region-targeted findings.** When a critique finding is
scoped to a specific region (per the
`<!-- region:<name> -->` delimiter format from
`SPECIFICATION/templates/minimal/contracts.md` §"Delimiter-
comment format"), the finding's `summary` and
`proposed_changes` SHOULD reference the region name so the
downstream propose-change/revise cycle can apply targeted
edits.

## Output schema

Same shape as `propose-change` — emit JSON conforming to
`.claude-plugin/scripts/livespec/schemas/proposal_findings.schema.json`:

```json
{
  "findings": [
    {
      "name": "<short-finding-name>",
      "target_spec_files": ["SPECIFICATION.md"],
      "summary": "<one paragraph: what is ambiguous/contradictory and where>",
      "motivation": "<MUST contain ambiguity/contradiction lexicon keyword>",
      "proposed_changes": "<prose suggesting the corrective edit; uses BCP14>"
    }
  ]
}
```

## Failure modes

- **Schema-violation retry (PROPOSAL.md §"Retry-on-exit-4").**
- **Empty critique** (no findings). Emit `findings: []`. The
  wrapper handles the empty case.
- **Wording-style suggestions.** Defer to a separate
  cleanup-style propose-change cycle; the
  `prioritizes_ambiguity_over_style` lexicon match enforces
  this at the harness layer.
