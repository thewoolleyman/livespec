---
topic: delegated-commit-time-gate
author: claude-opus-5-5
created_at: 2026-10-24T01:43:30Z
---

## Proposal: Delegated commit-time gate execution

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/contracts.md

### Summary

Extend Delegated gate execution from the pre-push gate to the two commit-time gates: the pre-commit check aggregate (`just check-pre-commit`) and the test runs the commit-msg replay gate (`just check-red-green-replay`) makes. A repository MAY opt in to this separately from pre-push delegation. When it does, the gates run on the executor against the STAGED tree, under every rule the pre-push delegation already carries (host, set, authority, credential, verdict). The pushing host keeps its role as the place where replay trailers are written and judged.

### Motivation

Measured on the shared VPS 2026-10-24 01:34-01:45Z: 18 cores, mpstat 95.8% busy, PSI cpu some avg60 69%, load 78. A large share of the gate load comes from commit-time gates, which no delegation mechanism covers. In livespec-dev-tooling, which already delegates its pre-push gate, two worktrees were running the full `pytest -q` under the commit-msg hook `check-red-green-replay` on a chore commit, on the VPS. v229 ratified delegation for the pre-push gate only (`non-functional-requirements.md` §"Enforcement-suite invocation", **Delegated gate execution**; `contracts.md` §"Pre-commit step ordering"). As a result every commit in every repository, opted-in or not, runs its heaviest gates on the committing host. Coordinator gitops-fleet-capacity-monitoring directed (2026-10-24 01:4xZ) that delegating the commit-time aggregate be routed through the spec path. It sits outside plan livespec-dev-tooling-mvalxq's Definition of Done. The proposal reuses every v229 property instead of restating a second delegation design, so the two paths cannot drift.

### Proposed Changes

In `non-functional-requirements.md` §"Enforcement-suite invocation":

1. Replace the **Invocation surfaces** bullet `Pre-commit and pre-push (hook)` with: "**Pre-commit and pre-push (hook):** `lefthook.yml` runs the repository's gate recipes. Each runs on the committing or pushing host unless that repository has delegated that gate per **Delegated gate execution** (pre-push) or **Delegated commit-time gate execution** (pre-commit and commit-msg) below."

2. Insert a new paragraph immediately after the **Delegated gate execution** paragraph group (after *The verdict*):

"**Delegated commit-time gate execution.** A repository MAY delegate its commit-time gates to the same remote executor. The commit-time gates are the pre-commit check aggregate (`just check-pre-commit`) and the test runs the commit-msg replay gate (`just check-red-green-replay`) performs. The opt-in MUST be separate from pre-push delegation and MUST be carried in the repository's version-controlled configuration. A repository MAY opt in to either, both, or neither. Every property of **Delegated gate execution** — *The host*, *The set*, *The authority*, *The credential* and *The verdict* — MUST apply to a delegated commit-time gate, read with 'push' as 'commit' and 'the pushed tree' as the tree defined below. Delegation MUST change WHERE a commit-time gate runs and MUST NOT change WHAT it verifies.

*The tree, for a commit.* A delegated commit-time gate MUST run against the exact STAGED tree: the tree `git write-tree` names for the index at the moment the hook runs, NOT the tree of `HEAD` or of the working directory. The committing host MUST verify that identity before honouring the verdict, and a verdict for any other tree is an absent verdict. For the commit-msg replay gate's amend leg, the staged tree is the tree of the amended commit as staged.

*The replay judgement stays on the committing host.* The executor MUST report the replay gate's test OUTCOME — passed, failed, or no verdict — together with the output the replay gate checksums. It MUST NOT decide the replay gate's verdict. The committing host MUST judge that outcome against the leg's expectation: a Red leg requires a failing test, and a Green leg requires the same test, byte-identical, now passing. It MUST record the replay trailers from the executor's reported outcome and output exactly as it would from a local run. An absent verdict MUST NOT be read as a failing test. A Red leg MUST NOT be accepted on an absent verdict, because an executor that could not run the test has not shown that the test fails.

*Refusal, not fall-through.* A commit whose delegated commit-time gate returns no verdict MUST be refused unless a run of that gate on the committing host, invoked as an explicit act, authorizes it. That is the same rule *The verdict* states for a push. A committing host that *The host* makes non-delegating — a factory sandbox, for example — runs its commit-time gates locally and MUST report that it gated locally."

In `contracts.md` §"Pre-commit step ordering":

3. Amend the `03-check-pre-commit` description to read: "`03-check-pre-commit` (delegates to `just check-pre-commit`; the heavy check aggregate, Red-mode-aware per v036 D1; where the repository has delegated its commit-time gates per `non-functional-requirements.md` §\"Enforcement-suite invocation\" and the commit is from a delegating host, that recipe obtains the same aggregate's verdict from the executor against the staged tree, and runs on the committing host the members that read an authorization held outside the tree)".

4. Amend the commit-msg sentence for `just check-red-green-replay {1}` to append: "; where the repository has delegated its commit-time gates and the commit is from a delegating host, the replay gate's test runs MUST be obtained from the executor against the staged tree, and the Red/Green judgement and trailer recording MUST remain on the committing host".

The zero-`.py` doc-only subset of `check-pre-commit` MUST remain a local developer-speed optimization. Delegation MUST NOT widen or narrow it.

## Proposal: Scenarios for delegated commit-time gates

### Target specification files

- SPECIFICATION/scenarios.md

### Summary

Add Gherkin scenarios that carry the load-bearing behavior of the new clause, so the clause is not carried by prose alone (authoring split (i)). They cover: the staged tree is what is gated; a Red leg is refused on an absent verdict; the replay judgement and trailers stay on the committing host; and a non-delegating host gates locally and says so.

### Motivation

The clause adds observable behavior: what a commit does when the executor answers, fails, or does not answer. Each case needs a scenario so the revise pass can bind exercising tests and the heading-coverage map stays honest.

### Proposed Changes

Add to `scenarios.md` the following scenarios. Each MUST be bound in `tests/heading-coverage.json` by the revise pass that accepts this proposal, with `test` MAY be `"TODO"` and a non-empty `reason` until an exercising test lands.

```gherkin
Scenario: a delegated commit-time gate runs against the staged tree
  Given a repository opted in to delegated commit-time gates
  And a committing host that holds the executor credential
  And a working directory whose unstaged edits differ from the index
  When the developer commits
  Then the executor MUST gate the tree `git write-tree` names for the index
  And the committing host MUST verify that tree identity before honouring the verdict

Scenario: a Red leg is refused when the executor returns no verdict
  Given a repository opted in to delegated commit-time gates
  And a staged tree carrying a new test and no implementation
  When the developer makes the Red commit and the executor returns no verdict
  Then the commit MUST be refused
  And the refusal MUST report the verdict as absent, not as a failing test
  And no TDD-Red trailers MUST be written

Scenario: the replay judgement and trailers stay on the committing host
  Given a repository opted in to delegated commit-time gates
  When the executor reports the replay gate's test as failed with its output for a Red leg
  Then the committing host MUST judge the Red expectation from that reported outcome
  And the committing host MUST write the TDD-Red trailers from the executor's reported output

Scenario: a non-delegating host gates its commits locally and says so
  Given a repository opted in to delegated commit-time gates
  And a committing host that holds no executor credential
  When the developer commits
  Then the commit-time gates MUST run on the committing host
  And the hook MUST report that it gated locally
```
