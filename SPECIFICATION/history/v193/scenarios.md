# Scenarios — `livespec`

This file enumerates the canonical user-facing scenarios for `livespec`: the happy-path flows, policy and wrapper error paths, recovery paths, and cross-cutting integrity scenarios.

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

Scenario: Complete upstream authoring input avoids redundant propose-change dialogue
  Given `spec_governance.propose_change_mode` resolves to `batch`
  And an upstream envelope supplies non-empty intent and topic
  And every surfaced compatible in-flight item has an explicit relationship
  When the propose-change operation runs
  Then it consumes the supplied intent, topic, and relationships without re-asking them
  And it appends a digest-only policy-journal event before invoking the mutation wrapper

Scenario: Complete upstream critique input avoids repeating the target question
  Given `spec_governance.critique_mode` resolves to `batch`
  And an upstream envelope supplies a non-empty critique target
  When the critique operation runs
  Then it consumes the target without asking `Capture critique target`
  And the deterministic critique wrapper receives no input envelope

Scenario: Default alignment consumes a compatible in-flight relationship
  Given `spec_governance.in_flight_alignment` resolves to `default-align`
  And the new work is compatible with a surfaced in-flight item
  When the propose-change operation resolves the relationship
  Then it aligns without repeating the relationship question
  And it does not treat semantic conflict or supersession as alignment
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
  And invokes `bin/revise.py --revise-json <tempfile>`
  Then the wrapper applies the accepted proposals to the live spec files
  And writes `<spec-target>/proposed_changes/<topic>-revision.md` recording the per-proposal disposition
  And moves both files atomically into `<spec-target>/history/v002/proposed_changes/`
  And snapshots the post-revise live spec into `<spec-target>/history/v002/`
  And the post-step doctor static phase emits zero `fail` findings
  And the wrapper exits 0

Scenario: Manual-spawn ratification review authorizes exact final bytes
  Given an accepted proposal has final `resulting_files[]` bytes assembled
  And a separately spawned designated reviewer returns `NO BLOCKERS` for those exact bytes
  When the revise payload is applied
  Then matching ratification-review evidence is validated before mutation
  And the revision record preserves the evidence

Scenario: Auto-spawn still enforces the independent-review floor
  Given `spec_governance.ratification_review` resolves to `auto-spawn`
  And the designated reviewer model is available
  When revise reaches an accept decision
  Then the operation spawns the separate read-only reviewer automatically
  And it does not mutate until matching `NO BLOCKERS` evidence exists

Scenario: Per-proposal manual review overrides global auto-spawn
  Given global ratification review resolves to `auto-spawn`
  And the proposal front matter sets `ratification_review_policy: manual-spawn`
  When revise resolves review ownership
  Then the attended session must initiate the review
  And the independent-review floor remains active

Scenario: Modified proposal content is reviewed after convergence
  Given a proposal decision is `modify`
  And the modification dialogue has converged on final proposal and resulting-file bytes
  When ratification review runs
  Then it reviews the converged bytes rather than the originally filed text
  And only evidence matching the converged content digest permits mutation

Scenario Outline: Global automated revise mode requires complete independent authority
  Given global `spec_governance.revise_decision_mode` is `<mode>`
  And no design-record, ratification-blocker, or drift-origin floor applies
  And the separate adversarial review result is `<review_result>` for the exact final bytes
  And delegated or consensus decision authority is `<decision_authority>` for those bytes
  When revise resolves decision ownership
  Then `requires_revise_decision_input` is `<requires_input>`
  And mutation is permitted only when the result is `false`

  Examples:
    | mode      | review_result | decision_authority         | requires_input |
    | delegated | NO BLOCKERS   | delegated decider accepts  | false          |
    | delegated | BLOCKERS      | delegated decider accepts  | true           |
    | delegated | NO BLOCKERS   | delegated decider rejects  | true           |
    | consensus | NO BLOCKERS   | consensus tier unavailable | true           |

Scenario Outline: Per-proposal manual decision policy overrides automated global policy
  Given global `spec_governance.revise_decision_mode` resolves to `<global_mode>`
  And the proposal front matter sets `decision_policy: manual`
  When revise resolves decision ownership for that proposal
  Then `requires_revise_decision_input` is true
  And the maintainer must explicitly confirm its decision

  Examples:
    | global_mode |
    | delegated   |
    | consensus   |

Scenario Outline: Revise decision hard floors win before every configured value
  Given `spec_governance.revise_decision_mode` resolves to `delegated`
  And the proposal front matter sets `decision_policy: consensus`
  And the proposal has `<floor>`
  When `effective_revise_decision_mode` resolves
  Then the proposal requires a human decision
  And neither configured value is considered

  Examples:
    | floor                                 |
    | a cited design-record contradiction   |
    | no cited or reachable design record   |
    | a ratification-review blocker         |
    | drift origin                          |

Scenario: Revise decision defaults arm nothing
  Given `revise_decision_mode` and `decision_policy` are absent, malformed, unknown, or wrong-typed
  When revise resolves decision ownership
  Then the effective mode is `manual`
  And `requires_revise_decision_input` is true
  And no unattended decision is armed

Scenario: Revise owns a deferred heading-coverage test
  Given an accepted proposal adds a `##` heading whose covering test cannot land yet
  When the revise flow assembles the resulting `tests/heading-coverage.json` entry with `test: "TODO"`
  Then it files a covering-test work-item through the configured work-item capture seam
  And stamps the returned id into the entry's non-empty `work_item` field
  And an unowned TODO entry is rejected before it can land on master
```

## Happy-path doctor

```gherkin
Feature: Running doctor static checks against every spec tree

Scenario: Doctor static phase against a multi-tree project
  Given a project with a main spec at SPECIFICATION/ AND a sub-spec tree at SPECIFICATION/templates/<name>/
  When the user invokes `/livespec:doctor`
  Then the wrapper enumerates every spec tree (the main spec plus each sub-spec)
  And runs the static-check registry against each tree
  And emits `{"findings": [...]}` JSON to stdout with one entry per check per tree
  And the wrapper exits 0 if every finding is `pass`
  And exits non-zero if any finding is `fail`

Scenario: A mapped executable doctor verb owns the finding
  Given `doctor_dispositions` maps a canonical finding check id to an available verb
  And no hard floor applies
  When doctor resolves the finding disposition
  Then `requires_doctor_disposition_input` is false
  And the selected verb executes only after its structured audit event is appended

Scenario: A mapped capture verb retains downstream consent
  Given `doctor_dispositions` maps a finding to `capture-as-work-item`
  And the active orchestrator supplies the required invocation-scoped store-write consent
  When doctor disposes the finding
  Then it invokes the orchestrator's published capture front end
  And the finding identity remains present in the captured work item

Scenario: Invocation disposition overrides the global map
  Given no hard floor applies to a doctor finding
  And the global map selects `defer`
  And the invocation envelope selects `fix-now`
  When doctor resolves the disposition
  Then the valid invocation selection wins
  And the journal names the effective invocation source
```

## Error path — authoring batch input requires attention

```gherkin
Feature: Authoring automation fails safely toward human attention

Scenario: Incomplete or conflicting batch authoring does not mutate
  Given an authoring mode resolves to `batch`
  And its envelope is incomplete, ambiguous, internally contradictory, or conflicts with a cited design record
  When the operation resolves required input
  Then it requires human attention before invoking a mutating wrapper
  And the spec tree remains unchanged

Scenario: Invalid settings and journal failure preserve interactive safety
  Given authoring policy is missing, malformed, unknown, or wrong-typed
  When effective policy is resolved
  Then interactive dialogue remains the safe default
  And if the policy journal cannot be written no batch mutation occurs
```

## Error path — doctor disposition requires attention

```gherkin
Feature: Doctor automation never disposes a finding without an executable safe choice

Scenario: Unmapped or failed disposition reaches a human
  Given a doctor finding is unmapped, invalid, unavailable, or its selected action fails
  When `effective_doctor_disposition` resolves
  Then `requires_doctor_disposition_input` is true
  And no alternate verb executes silently

Scenario: Missing consent or journal failure prevents automatic disposition
  Given a mapped verb needs downstream store-write consent or a policy-journal append
  And the required consent is absent or the journal append fails
  When doctor attempts the disposition
  Then the finding requires human input
  And no spec or work-item state is mutated

Scenario: Empty defaults arm no doctor action
  Given `spec_governance.doctor_dispositions` is absent
  When a non-pass finding is surfaced
  Then the effective map is empty
  And the canonical five-option dialogue is presented
```

## Error path — ratification review blocks mutation

```gherkin
Feature: Independent ratification review is a structural mutation floor

Scenario: Blocking or invalid review evidence prevents ratification
  Given an accept or modify decision has a blocking verdict, unavailable or undesignated reviewer, stale or malformed digest, or journal failure
  When revise validates ratification-review evidence
  Then it requires maintainer input
  And it does not mutate the spec or history tree

Scenario: All-defaults behavior retains manual independent review
  Given the `spec_governance` block is absent
  When revise resolves ratification-review policy
  Then the effective mode is `manual-spawn`
  And no proposal can be ratified without matching `NO BLOCKERS` evidence
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

## Recovery path — pruning history

```gherkin
Scenario: Prune history collapses old versions into a single marker
  Given the repository has 20 history versions at `<spec-target>/history/v001/` through `v020/`
  When the user invokes `/livespec:prune-history`
  Then the wrapper deletes `v001/` through `v018/`
  And `v019/` contains only `PRUNED_HISTORY.json` with `{"pruned_range": [1, 19]}`
  And `v020/` remains unchanged
  And the contiguous-version invariant holds via the `version-directories-complete` pruned-marker exemption
  And the wrapper exits 0
```

## Behavior clause lacking a scenario link is surfaced

```gherkin
Feature: The behavior_scenario_link check surfaces unlinked behavior clauses

Scenario: An unlinked behavior clause is surfaced, severity selected by the lever
  Given a behavior-bearing core spec file carries a `MUST`/`SHOULD` clause
  And that clause's gap-id has no `clauses[]` link to a live `scenarios.md` H2 section in `tests/heading-coverage.json`
  When the `behavior_scenario_link` check runs
  Then in `warn` mode (the default) it emits a `behavior-scenario-link-unlinked` warning for the clause and exits 0
  And in `fail` mode (`LIVESPEC_BEHAVIOR_SCENARIO_LINK=fail`) it emits a `behavior-scenario-link-unlinked` error for the clause and exits non-zero
  And a clause whose gap-id IS linked to a live scenario is not surfaced
```

## Conflicting ratified statements resolve toward the cited design record

```gherkin
Feature: Intent preservation — the cited design record is the tiebreaker
  As a maintainer whose recorded design decisions must outlive any one session
  I want conflicts between ratified statements resolved toward the cited design record
  So that a contradiction is never silently resolved toward whatever the implementation already does

Scenario: Critique surfaces a conflict together with the design record's position
  Given a ratified spec tree carries two statements that contradict each other
  And the load-bearing semantic definition involved cites a reachable design record
  When the user invokes the critique operation
  Then the critique finding states the conflict and the cited design record's position on it
  And the finding does not treat the shipped implementation's side as the presumed resolution

Scenario: Revise does not ratify a resolution that contradicts a cited design record
  Given a pending proposed change resolves a conflict against the cited design record's position
  When the user invokes the revise operation
  And the maintainer's decision does not explicitly acknowledge the contradiction
  Then the resolution is not ratified as filed
  And the cited design record's position is surfaced for the maintainer's explicit decision

Scenario: A conflict with no reachable design record is escalated, never self-resolved
  Given a ratified spec tree carries two statements that contradict each other
  And no design record is cited or reachable for either statement
  When any lifecycle operation detects the conflict
  Then the missing design record is surfaced to the maintainer as a finding alongside the conflict
  And the conflict is not self-resolved in either direction

Scenario: A doctor mapping cannot dismiss a design-record finding
  Given `doctor_dispositions` maps a design-record contradiction finding to `dismiss`
  When doctor resolves the finding disposition
  Then the hard floor wins before the mapping
  And the finding still requires human input

Scenario: Ratification review cannot waive a cited-design-record contradiction
  Given a proposal contradicts its cited design record
  When the independent adversarial reviewer evaluates the final bytes
  Then it returns a blocker
  And neither manual-spawn nor auto-spawn may ratify the proposal without maintainer acknowledgment
```
