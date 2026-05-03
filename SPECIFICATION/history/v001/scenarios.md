# Scenarios — `livespec`

This file enumerates the canonical user-facing scenarios for `livespec`. Per the plan's Phase-6 scope, scenarios cover the happy-path seed/propose-change/revise/doctor flow plus the three error paths v014 N9 enumerates and the recovery paths from PROPOSAL.md §"seed", §"doctor", and §"Pruning history".

## Happy-path seed

```gherkin
Feature: Seeding a fresh livespec spec
  As a project author starting a new repository
  I want to seed a SPECIFICATION/ tree from my project intent
  So that subsequent changes flow through the governed propose-change/revise loop

Scenario: Seed a single-tree project with the livespec template
  Given the repository has no `.livespec.jsonc` and no `SPECIFICATION/` tree
  And the user has the `livespec` plugin installed
  When the user invokes `/livespec:seed`
  And answers `livespec` to the template-selection question
  And answers `no` to the sub-spec-emission question
  And provides a free-text seed intent
  Then the seed wrapper writes `.livespec.jsonc` at the repo root
  And writes the main spec files at the template-declared paths
  And writes `<spec-root>/history/v001/` containing frozen copies of every main-spec file
  And writes `<spec-root>/history/v001/proposed_changes/seed.md` capturing the intent
  And writes `<spec-root>/history/v001/proposed_changes/seed-revision.md` recording the seed acceptance
  And the post-step doctor static phase emits zero `fail` findings
  And the wrapper exits 0
```

## Happy-path propose-change

```gherkin
Feature: Filing a propose-change against an existing spec tree

Scenario: Propose a change against the main spec
  Given the repository has a seeded SPECIFICATION/ tree at v001
  When the user invokes `/livespec:propose-change`
  And the SKILL.md prose composes a `proposal_findings.schema.json`-conforming JSON payload from the user's described change
  And invokes `bin/propose_change.py --findings-json <tempfile> <topic>`
  Then the wrapper writes `<spec-target>/proposed_changes/<topic>.md` containing one or more `## Proposal: <name>` sections
  And the post-step doctor static phase emits zero `fail` findings
  And the wrapper exits 0
```

## Happy-path revise

```gherkin
Feature: Revising the spec by accepting/rejecting proposals

Scenario: Revise after a single-proposal propose-change
  Given the repository has a seeded SPECIFICATION/ tree at v001
  And `<spec-target>/proposed_changes/<topic>.md` exists with one proposal
  When the user invokes `/livespec:revise`
  And the SKILL.md prose walks the user through the per-proposal accept/reject decision
  And composes a `revise_input.schema.json`-conforming JSON payload
  And invokes `bin/revise.py --revise-input <tempfile>`
  Then the wrapper applies the accepted proposals to the live spec files
  And writes `<spec-target>/proposed_changes/<topic>-revision.md` recording the per-proposal disposition
  And moves both files atomically into `<spec-target>/history/v002/proposed_changes/`
  And snapshots the post-revise live spec into `<spec-target>/history/v002/`
  And the post-step doctor static phase emits zero `fail` findings
  And the wrapper exits 0
```

## Happy-path doctor

```gherkin
Feature: Running doctor static checks against every spec tree

Scenario: Doctor static phase against a multi-tree project
  Given the repository has a main spec at SPECIFICATION/ AND sub-spec trees at SPECIFICATION/templates/livespec/ AND SPECIFICATION/templates/minimal/
  When the user invokes `/livespec:doctor`
  Then the wrapper enumerates all three spec trees
  And runs the static-check registry against each tree
  And emits `{"findings": [...]}` JSON to stdout with one entry per check per tree
  And the wrapper exits 0 if every finding is `pass`
  And exits non-zero if any finding is `fail`
```

## Error path 1 — propose-change against a non-existent spec target

```gherkin
Scenario: Propose-change with --spec-target pointing at a missing directory
  Given the user invokes `bin/propose_change.py --findings-json <path> --spec-target /nonexistent topic`
  When the wrapper runs
  Then the wrapper exits 3 (PreconditionError)
  And stderr carries a structured diagnostic naming the missing `<spec-target>` path
```

## Error path 2 — schema-violation in inbound seed payload

```gherkin
Scenario: Seed with a malformed seed-input JSON payload
  Given a tempfile contains JSON that fails the seed_input.schema.json validation
  When the user invokes `bin/seed.py --seed-json <tempfile>`
  Then the wrapper exits 4 (ValidationError)
  And stderr carries the `fastjsonschema` validation error pointing at the offending field
  And the SKILL.md retry-on-exit-4 contract MAY re-invoke the seed prompt with the error context to repair the payload
```

## Error path 3 — version-contiguity gap in history

```gherkin
Scenario: Doctor catches a missing version directory
  Given the repository has `<spec-target>/history/v001/`, `<spec-target>/history/v003/`, but no `v002/`
  When the user invokes `/livespec:doctor`
  Then the static-check `version-contiguity` emits a `fail` finding referencing the gap at `v002`
  And the wrapper exits non-zero
  And the recovery path is to invoke `/livespec:revise` to land the missing `v002` (impossible if v003 was hand-edited; otherwise the user MUST restore the `v002/` from git history or back out the offending commit)
```

## Recovery path — pruning history before a long retention horizon

```gherkin
Scenario: Prune history down to the most recent 5 versions
  Given the repository has 20 history versions at `<spec-target>/history/v001/` through `v020/`
  When the user invokes `/livespec:prune-history` with a retention horizon of 5
  Then the wrapper removes `v001/` through `v015/`
  And `v016/` through `v020/` remain unchanged
  And the contiguous-version invariant holds for the remaining tail
  And the wrapper exits 0
```
