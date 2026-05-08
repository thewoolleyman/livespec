# `revise` prompt — `livespec` template

> **Status: Phase-7-final per `SPECIFICATION/templates/livespec/contracts.md`
> §"Per-prompt semantic-property catalogue → prompts/revise.md".**
> Future regenerations land via dogfooded propose-change/revise
> against the sub-spec, atomically with their catalogue widening
> per Plan §3543-3550.

## Inputs

- The active spec tree (under `<spec-target>/`, resolved by the
  wrapper via `--spec-target` or the default
  `.livespec.jsonc`-walking behavior). Per v018 Q1, may target
  the main spec or any sub-spec.
- `input_context.pending_proposals` — every pending proposal
  under `<spec-target>/proposed_changes/*.md` (the skill prose
  filters out `README.md` and any `-revision.md` siblings).
- Optional `<revision-steering-intent>` — user-provided guidance
  for the per-proposal decisions (e.g., "reject anything
  touching the auth section"). When provided, MUST only steer
  per-proposal decisions for the current invocation; MUST NOT
  contain new spec content.
- The reference document at the template root,
  `livespec-nlspec-spec.md`, for NLSpec discipline.

## Catalogue contract (`SPECIFICATION/templates/livespec/contracts.md`)

Two semantic properties are mechanically asserted by the
prompt-QA harness against this prompt's `replayed_response`:

- `decisions_reference_pending_proposals` — every topic in
  `replayed_response.decisions[].proposal_topic` is a member
  of the topic-stem set extracted from
  `input_context.pending_proposals[]` (filename stems from
  each path). The prompt MAY emit decisions for any subset of
  pending proposals (selective revise per
  `SPECIFICATION/spec.md` (v052) §"Sub-command lifecycle"
  revise lifecycle clause (h)); pending proposals not covered
  by decisions are tolerated. Extras — decisions whose topic
  is NOT in pending — indicate stale or typo'd topic
  references and fail the assertion.
- `per_proposal_disposition_with_rationale` — every decision
  in `replayed_response.decisions[]` has `decision` in
  `{"accept", "modify", "reject"}` AND a non-empty
  whitespace-stripped `rationale`. Schema validation already
  enforces field presence + the enum; this assertion
  strengthens the rationale check (whitespace-only rationales
  fail).

## Behavior

Process each pending proposal in `created_at` front-matter order
(oldest first; lexicographic filename fallback on tie). For each
proposal, emit one decision entry under `decisions[]`:

- **`accept`** — the proposal lands as-is. Include
  `resulting_files[]` carrying the post-update content of every
  spec file the proposal touches (`target_spec_files` from the
  proposal's `## Proposal: <name>` sections).
- **`modify`** — the proposal lands with modifications drafted
  by the LLM. Include the `modifications` field describing the
  changes. Include `resulting_files[]` with the modified
  content.
- **`reject`** — the proposal is recorded as rejected. Omit
  `resulting_files[]` (or emit an empty array). The audit trail
  preserves the proposed-change file in
  `<spec-target>/history/v<N+1>/proposed_changes/` even on
  reject.

The wrapper performs all deterministic file shaping: cuts a new
`<spec-target>/history/v<N+1>/`, moves processed proposed-change
files byte-identical, writes paired `<topic>-revision.md` files,
applies `resulting_files[]` to working spec files in place, and
snapshots post-update spec files into the new vNNN/.

**Audit-trail invariant** ( Statement B,
codified in v038 D1). Even when ALL decisions are `reject`, the
wrapper cuts a new `v<N+1>/` with the rejected proposed-change
files moved into history and rejection-revision files paired
with each. Byte-identical-to-prior spec files when no decision
is `accept` or `modify`. Cut-on-every-successful-revise is the
contract.

**Spec-target awareness.** The active `<spec-target>/` may be
main or sub-spec; emitted paths in `resulting_files[]` should
be spec-target-relative consistently with the `propose-change`
prompt's path discipline.

**Topic-vs-filename-stem note (v014 N6).** Under collision
disambiguation, a propose-change filename stem may carry a `-N`
suffix (e.g., `quiet-flag-2.md`) while the front-matter `topic:`
field stays canonical (`quiet-flag`). The
`decisions_reference_pending_proposals` assertion's
filename-stem extraction is a structural approximation that
holds in the collision-free common case; the prompt's
`decisions[].proposal_topic` MUST emit the canonical topic from
front-matter even when the filename has a collision suffix. In
the collision case the canonical topic is not in the
filename-stem set, so the harness's emitted-in-pending check
would fail on a legitimate `-N`-collision-disambiguated topic;
the harness or fixture authoring MUST account for this when
the collision case arises.

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
      "rationale": "<why this decision; one paragraph (non-empty)>",
      "resulting_files": [
        {"path": "<spec-target-relative path>", "content": "..."}
      ]
    },
    {
      "proposal_topic": "<canonical-topic>",
      "decision": "modify",
      "rationale": "<why modified; one paragraph>",
      "modifications": "<what was modified relative to the proposal>",
      "resulting_files": [
        {"path": "<spec-target-relative path>", "content": "..."}
      ]
    },
    {
      "proposal_topic": "<canonical-topic>",
      "decision": "reject",
      "rationale": "<why rejected; one paragraph>"
    }
  ]
}
```

`proposal_topic` matches the canonical-topic value in each
proposed-change file's front-matter `topic:` field (NOT the
filename stem when the stem carries a `-N` collision suffix).

## Failure modes

- **Schema-violation retry.**
  Same as the other LLM-driven prompts.
- **Empty proposed_changes/.** When zero in-flight proposals
  exist (only `README.md` is present), revise's wrapper exits
  3 with `PreconditionError`. The prompt does not run in this
  case; the SKILL.md prose surfaces the precondition failure.
- **Mid-stream LLM truncation.** If the LLM truncates output
  before covering the user's intended subset of pending
  proposals, the user surfaces the gap during normal review
  (the `decisions_reference_pending_proposals` assertion does
  NOT catch under-coverage; selective revise is permitted by
  contract). The retry-on-exit-4 path is the recovery:
  re-invoke with the same input context.
