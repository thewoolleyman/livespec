# Scenarios — `livespec` template

This sub-spec's scenarios enumerate the canonical user-facing flows for the `livespec` template's prompt interview surface. Phase 6 lands one happy-path scenario per REQUIRED prompt plus the v020 Q2 sub-spec-emission branches; Phase 7 widens this to the full edge-case surface.

## Happy-path seed interview — "no" branch (default)

```gherkin
Feature: Seed interview — single-tree project (sub_specs: [])
  As a project author starting a new repository
  I want to seed a SPECIFICATION/ tree from my project intent without sub-specs
  So that the resulting tree is the simple end-user case the v020 Q2 default targets

Scenario: User answers "no" to sub-spec emission
  Given the user has invoked /livespec:seed against an empty repo
  When the seed prompt asks "Which template?"
  And the user answers "livespec"
  And the seed prompt asks "Does this project ship its own livespec templates?"
  And the user answers "no"
  And the seed prompt asks "What is the intent of this project?"
  And the user provides free-text intent
  Then the seed prompt emits seed_input.schema.json-conforming JSON
  And the JSON's sub_specs[] field is the empty list []
  And the JSON's files[] array contains one entry per template-declared spec-file path
  And bin/seed.py materializes only the main spec tree
```

## Happy-path seed interview — "yes" branch (meta-project)

```gherkin
Feature: Seed interview — multi-tree meta-project (sub_specs[] populated)

Scenario: User answers "yes" to sub-spec emission with two named templates
  Given the user has invoked /livespec:seed against an empty repo
  When the seed prompt asks "Which template?"
  And the user answers "livespec"
  And the seed prompt asks "Does this project ship its own livespec templates?"
  And the user answers "yes"
  And the seed prompt asks "Which template directory names should each receive a sub-spec tree?"
  And the user answers "livespec, minimal"
  And the seed prompt asks "What is the intent of this project?"
  And the user provides free-text intent
  Then the seed prompt emits seed_input.schema.json-conforming JSON
  And the JSON's sub_specs[] field contains two SubSpecPayload entries
  And the first SubSpecPayload's template_name is "livespec"
  And the second SubSpecPayload's template_name is "minimal"
  And bin/seed.py materializes the main spec tree AND both sub-spec trees atomically
```

## Happy-path propose-change interview

```gherkin
Feature: Propose-change interview against an existing main spec

Scenario: User describes a clarification to spec.md
  Given the repository has a seeded SPECIFICATION/ tree at v001
  When the user invokes /livespec:propose-change
  And describes a clarification needed in spec.md's "Versioning" section
  Then the propose-change prompt elicits one finding with name, target_spec_files, summary, motivation, proposed_changes
  And the target_spec_files field references "SPECIFICATION/spec.md"
  And the proposed_changes prose uses BCP14 normative language
  And bin/propose_change.py writes SPECIFICATION/proposed_changes/<topic>.md with one ## Proposal section
```

## Happy-path revise interview

```gherkin
Feature: Revise interview accepting all pending proposals

Scenario: User accepts a single pending proposal
  Given the repository has a seeded SPECIFICATION/ tree at v001
  And SPECIFICATION/proposed_changes/<topic>.md exists with one proposal
  When the user invokes /livespec:revise
  And the revise prompt walks the user through the per-proposal accept decision
  And the user accepts the proposal
  Then the revise prompt composes revise_input.schema.json-conforming JSON describing the acceptance and the resulting spec edits
  And bin/revise.py applies the spec edits to the live spec files
  And writes SPECIFICATION/proposed_changes/<topic>-revision.md
  And moves both files atomically into SPECIFICATION/history/v002/proposed_changes/
  And snapshots the post-revise live spec into SPECIFICATION/history/v002/
```

## Happy-path critique interview

```gherkin
Feature: Critique interview surfacing ambiguities

Scenario: User asks for a critique of constraints.md
  Given the repository has a seeded SPECIFICATION/ tree at v001
  When the user invokes /livespec:critique
  And the critique prompt reads SPECIFICATION/constraints.md
  And surfaces ambiguities in the file
  Then the critique prompt emits proposal_findings.schema.json-conforming JSON
  And each finding's target_spec_files references "SPECIFICATION/constraints.md"
  And findings prioritize ambiguities and contradictions over wording-style suggestions
```

## Edge case — seed against non-empty SPECIFICATION/

```gherkin
Scenario: Seed refuses when SPECIFICATION/ already has content
  Given the repository has SPECIFICATION/spec.md containing arbitrary content
  When the user invokes /livespec:seed
  Then bin/seed.py exits 3 (PreconditionError)
  And stderr carries the idempotency-refusal diagnostic naming the conflicting file
  And no files are written
```
