# `revise` prompt — `livespec` template (bootstrap-minimum per v020 Q4)

> **Status: bootstrap-minimum (Phase 3 widening per v020 Q4).** Final
> content is agent-generated in Phase 7 from the `livespec` template's
> sub-spec. Do not hand-edit beyond bootstrap-minimum scope.

## Inputs

- The active spec tree (under `<spec-target>/`, resolved by the
  wrapper via `--spec-target` or the default
  `.livespec.jsonc`-walking behavior). Per v018 Q1, may target
  the main spec or any sub-spec.
- Every pending proposal under
  `<spec-target>/proposed_changes/*.md` (skip `README.md` and any
  file ending in `-revision.md`).
- Optional `<revision-steering-intent>` — user-provided guidance
  for the per-proposal decisions (e.g., "reject anything touching
  the auth section"). When provided, MUST only steer per-proposal
  decisions for the current invocation; MUST NOT contain new spec
  content.
- The reference document at the template root,
  `livespec-nlspec-spec.md`, for NLSpec discipline.

## Behavior

Process each pending proposal in `created_at` front-matter order
(oldest first; lexicographic filename fallback on tie). For each
proposal, emit one decision entry under `decisions[]`:

- **`accept`** — the proposal lands as-is. Include
  `resulting_files[]` carrying the post-update content of every
  spec file the proposal touches (`target_spec_files` from the
  proposal's `## Proposal: <name>` sections).
- **`modify`** — the proposal lands with modifications drafted by
  the LLM. Include the `modifications` field describing the
  changes. Include `resulting_files[]` with the modified content.
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

**Audit-trail invariant.** Even when ALL decisions are reject,
the wrapper cuts a new vNNN with the rejected proposed-change
files moved into history and rejection-revision files paired
with each. Phase 3 minimum-viable: rejection-revision content is
just `decision: reject` + `rationale`; Phase 7 widens for richer
audit-trail content.

**Spec-target awareness.** Same as the other LLM-driven prompts
— the active `<spec-target>/` may be main or sub-spec; emitted
paths in `resulting_files[]` should be repo-root-relative.

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
      "rationale": "<why this decision; one paragraph>",
      "resulting_files": [
        {"path": "<repo-relative path>", "content": "..."}
      ]
    },
    {
      "proposal_topic": "<canonical-topic>",
      "decision": "modify",
      "rationale": "<why modified; one paragraph>",
      "modifications": "<what was modified relative to the proposal>",
      "resulting_files": [
        {"path": "<repo-relative path>", "content": "..."}
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
filename stem — under v014 N6, the filename stem may carry a
`-N` suffix for collision disambiguation; the `topic` field
strips it).

Phase 7 replaces this prompt with the agent-generated final
content per the sub-spec.
