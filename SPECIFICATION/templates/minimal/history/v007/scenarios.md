# Scenarios — `minimal` template

This sub-spec's scenarios outline the structural shape of `tests/e2e/`'s end-to-end integration test (Phase 9 work). Phase 6 lands the structural outline; Phase 9 fills in the test fixtures and harness invocations.

## End-to-end seed retry-on-exit-4

```gherkin
Feature: e2e — seed prompt retries on schema-validation failure
  As a project author seeding a minimal-template-rooted spec
  I want the seed prompt to recover from malformed JSON output
  So that a single bad prompt response doesn't waste the user's interaction

Scenario: First seed-prompt response fails schema validation
  Given a fresh fixture repo with no SPECIFICATION.md
  And the test harness's fake-claude responds to the seed prompt with malformed JSON on the first turn
  When the user invokes /livespec:seed against the fixture
  Then bin/seed.py exits 4 (ValidationError) on the first invocation
  And the seed SKILL.md's retry-on-exit-4 contract surfaces the validation error to the prompt
  And the fake-claude's second response repairs the payload
  And the second bin/seed.py invocation exits 0
  And SPECIFICATION.md is written with the intended content
```

## End-to-end doctor-static-fail-then-fix recovery

```gherkin
Feature: e2e — doctor static phase catches a fault, propose-change/revise repairs it

Scenario: Version-contiguity gap repaired via revise
  Given the fixture repo has SPECIFICATION.md and history/v001/, history/v003/ but no v002/
  When the user invokes /livespec:doctor
  Then the doctor static-phase version-contiguity check emits a fail finding referencing the v002 gap
  And the wrapper exits non-zero
  When the user invokes /livespec:propose-change to record the contiguity-repair intent
  And invokes /livespec:revise to apply the repair (which restores the missing v002 from git)
  Then the post-revise doctor static phase emits zero fail findings
  And the wrapper exits 0
```

## End-to-end prune-history no-op

```gherkin
Feature: e2e — prune-history is a no-op when retention horizon exceeds available versions

Scenario: Prune with retention horizon larger than available versions
  Given the fixture repo has history/v001/ only
  When the user invokes /livespec:prune-history with retention horizon 5
  Then no version directories are removed
  And the wrapper exits 0
  And the post-step doctor static phase emits zero fail findings
```

## End-to-end propose-change/revise round-trip

```gherkin
Feature: e2e — propose-change → revise round-trip against a single-file spec

Scenario: User clarifies a spec section via propose-change/revise
  Given the fixture repo has SPECIFICATION.md at v001 with a defined heading "Authentication"
  When the user invokes /livespec:propose-change describing a clarification to "Authentication"
  And the propose-change prompt composes the proposal_findings.schema.json payload
  And bin/propose_change.py writes proposed_changes/auth-clarification.md
  And the user invokes /livespec:revise accepting the proposal
  And bin/revise.py applies the spec edit to SPECIFICATION.md
  Then SPECIFICATION.md's "Authentication" section reflects the clarification
  And history/v002/ contains a snapshot of the post-revise SPECIFICATION.md
  And history/v002/proposed_changes/ contains both auth-clarification.md and auth-clarification-revision.md
```

## End-to-end critique → propose-change handoff

```gherkin
Feature: e2e — critique findings flow into a propose-change cycle

Scenario: User runs critique then handles findings via propose-change
  Given the fixture repo has SPECIFICATION.md at v001 with a known ambiguity
  When the user invokes /livespec:critique
  And the critique prompt surfaces the ambiguity as a proposal_findings.schema.json finding
  And the user pipes the findings into /livespec:propose-change
  And /livespec:propose-change writes proposed_changes/<topic>.md
  And the user invokes /livespec:revise accepting the proposal
  Then SPECIFICATION.md's ambiguity is resolved
  And history/v002/ records the propose-change/revise cycle
```

## Test harness contract

`tests/e2e/fake_claude.py` MUST implement the mock Claude Code surface the e2e tests drive. The harness MUST support deterministic per-prompt response sequences (so retry-on-exit-4 can be tested by scripting the first response as malformed and the second as well-formed). The harness MUST capture wrapper exit codes, stdout, and stderr for assertion in the e2e test cases. Phase 5 lands the placeholder; Phase 9 fills in the operational implementation.
