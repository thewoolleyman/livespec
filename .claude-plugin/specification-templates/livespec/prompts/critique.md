# `critique` prompt — `livespec` template (bootstrap-minimum per v020 Q4)

> **Status: bootstrap-minimum (Phase 3 widening per v020 Q4).** Final
> content is agent-generated in Phase 7 from the `livespec` template's
> sub-spec. Do not hand-edit beyond bootstrap-minimum scope.

## Inputs

- `<target>` — what the user wants critiqued: the active spec tree
  (under `<spec-target>/`), a specific spec file, or a single
  pending proposal under `<spec-target>/proposed_changes/<topic>.md`.
- The active spec tree (under `<spec-target>/`, resolved by the
  wrapper via `--spec-target` or the default).
- The reference document at the template root,
  `livespec-nlspec-spec.md`, for NLSpec discipline.

## Behavior

Walk the critique target and surface findings — ambiguities,
contradictions, missing rules, NLSpec-discipline violations,
inconsistencies between target_spec_files. Emit findings in the
SAME shape as `propose-change` (the wrapper internally delegates to
`propose-change` with the `-critique` reserve-suffix appended to
the topic).

Each finding describes a corrective action the user could take to
remediate the spec issue. Phase 3 minimum-viable: emit findings
that the Phase 7 widening cycle can act on; the
`critique-as-internal-delegation` mechanic at the wrapper layer
turns each finding into a section in the resulting
`<spec-target>/proposed_changes/<topic>-critique.md` file.

**Spec-target awareness.** Same as `propose-change`'s prompt —
the active `<spec-target>/` may be the main spec root or any
sub-spec tree. Use spec-target-relative paths consistently in
emitted `target_spec_files`.

## Output schema

Emit JSON conforming to
`.claude-plugin/scripts/livespec/schemas/proposal_findings.schema.json`
(same schema `propose-change` uses; the wrapper layer routes the
delegation):

```json
{
  "findings": [
    {
      "name": "<short-finding-name>",
      "target_spec_files": ["<repo-relative-path>", "..."],
      "summary": "<one paragraph: what's wrong and the proposed correction>",
      "motivation": "<NLSpec-discipline rule or inconsistency that surfaces this>",
      "proposed_changes": "<prose or fenced diff describing the corrective action>"
    }
  ]
}
```

A critique invocation MAY emit multiple findings — one per
distinct issue surfaced. The wrapper bundles them into a single
proposed-change file at
`<spec-target>/proposed_changes/<topic>-critique.md`.

Phase 3 minimum-viable does not run a separate "critique" file
format; the critique flow IS a propose-change flow with the
`-critique` reserve-suffix per v016 P3. Phase 7 may widen this
to support standalone critique-record artifacts if the dogfood
cycle surfaces the need.

Phase 3 widens this prompt with full NLSpec critique discipline.
Phase 7 replaces it with the agent-generated final content per
the sub-spec.
