# `revise` prompt — `minimal` template

<!-- livespec-harness-command: revise -->

> **Status: Phase-7-final per `SPECIFICATION/templates/minimal/contracts.md`
> §"Per-prompt semantic-property catalogue → prompts/revise.md".**

## Inputs

- The active `SPECIFICATION.md` at the project root (per the
  template's `spec_root: "./"` declaration).
- `input_context.pending_proposals` — every pending proposal
  under `./proposed_changes/*.md` (the skill prose filters out
  `README.md` and `-revision.md` siblings).
- Optional `<revision-steering-intent>` — user-provided
  guidance for the per-proposal decisions.

## Catalogue contract (`SPECIFICATION/templates/minimal/contracts.md`)

Two semantic properties are mechanically asserted by the
prompt-QA harness:

- `walks_every_pending_proposal` — every topic in
  `input_context.pending_proposals[]` (filename-stem extracted)
  appears in `replayed_response.decisions[].proposal_topic`.
  Skipping a pending proposal is a silent-data-loss bug.
- `per_proposal_disposition_with_rationale` — every decision
  has `decision` in `{"accept", "modify", "reject"}` AND a
  non-empty whitespace-stripped `rationale`.

## Behavior

Process each pending proposal in `created_at` front-matter
order (oldest first; lexicographic filename fallback). For
each proposal, emit one decision entry under `decisions[]`:

- **`accept`** — the proposal lands as-is. Include
  `resulting_files[]` with the post-update `SPECIFICATION.md`
  content (replacing the entire file or applying region-
  targeted edits per the delimiter-comment format).
- **`modify`** — the proposal lands with modifications.
  Include the `modifications` field describing the changes +
  `resulting_files[]` with the modified content.
- **`reject`** — the proposal is recorded as rejected. Omit
  `resulting_files[]` (or empty array). The audit trail
  preserves the rejected proposed-change file in
  `./history/v<N+1>/proposed_changes/`.

The wrapper handles all deterministic file shaping: cuts a
new `./history/v<N+1>/`, moves processed proposed-change
files byte-identical, writes paired `<topic>-revision.md`
files, applies `resulting_files[]` to `SPECIFICATION.md` in
place, snapshots into the new vNNN/.

**Audit-trail invariant** (PROPOSAL.md §"Versioning"
Statement B, codified in v038 D1). Even when ALL decisions
are `reject`, the wrapper cuts a new `v<N+1>/` with the
rejected proposed-change files moved into history. Same
contract as the livespec-template revise.

**Region-targeted edits.** When a proposal references a region
(per the `<!-- region:<name> -->` delimiter format from
`SPECIFICATION/templates/minimal/contracts.md` §"Delimiter-
comment format"), the prompt SHOULD emit `resulting_files[]`
with the updated `SPECIFICATION.md` body where only the
named region's content changed. Whole-file replacement is
also valid — the wrapper does not enforce region-targeting.

## Output schema

Emit JSON conforming to
`.claude-plugin/scripts/livespec/schemas/revise_input.schema.json`:

```json
{
  "author": "<LLM self-declaration or 'unknown-llm'>",
  "decisions": [
    {
      "proposal_topic": "<canonical-topic>",
      "decision": "accept",
      "rationale": "<why; non-empty>",
      "resulting_files": [
        {"path": "SPECIFICATION.md", "content": "..."}
      ]
    }
  ]
}
```

`proposal_topic` matches the canonical-topic value in each
proposed-change file's front-matter `topic:` field.

## Failure modes

- **Schema-violation retry (PROPOSAL.md §"Retry-on-exit-4").**
- **Empty proposed_changes/.** Revise's wrapper exits 3
  (PreconditionError); the prompt does not run.
- **Mid-stream LLM truncation.** Same recovery path as the
  livespec-template revise.
