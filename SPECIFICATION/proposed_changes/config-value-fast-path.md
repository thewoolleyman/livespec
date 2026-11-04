---
topic: config-value-fast-path
author: claude:ci-runtime-and-cost
created_at: 2026-11-04T19:00:22Z
---

## Proposal: Config-value fast path under PR gate ≡ master gate

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/scenarios.md

### Summary

Admit exactly one declared changeset class to a reduced gate: a change whose every changed line is the VALUE of a key on the committed config-value fast-path list runs schema and parse validation of the changed files only, with no test suites, at pre-commit, pre-push and in CI. The reduction applies identically on the pull request and on the push to master of the same change, so PR gate ≡ master gate still holds.

### Motivation

Maintainer direction recorded verbatim on livespec-dev-tooling-6tgd2z (2026-11-04 ~18:4xZ): "why does it takes a whole PR just to make the change. Even if the file is committed, it should be a short circuit, no-tests change to change the wip or cap values. NO TEST SHOULD BE TIED TO CONFIG VALUE ACTUAL VALUES. IF any of this is the case, fix it." Today a one-number capacity edit (a WIP cap, a churn-slot cap, a stall timeout) pays the full pre-commit, pre-push and CI aggregate: a 20-40 minute pull-request run for a change no test suite can say anything about beyond its schema. The current §"CI as a merge gate (branch protection)" text forbids conditioning any `just check` target on a changeset predicate, so the fast path cannot ship at pre-push or in CI without this change.

### Proposed Changes

In `non-functional-requirements.md` §"CI as a merge gate (branch protection)", after the **PR gate ≡ master gate.** paragraph, add a paragraph **Config-value fast path.** with these rules:

- `livespec-dev-tooling` MUST ship ONE committed config-value fast-path list. It names each qualifying key by file pattern and key path: capacity, cap, timeout and quota keys such as `.livespec.jsonc` `dispatcher.wip_cap` and `stall_timeout_seconds`, ansible host_vars `max_concurrent_runs`, `ci-runner` profile `ADMISSION_CAPACITY_C`, and factory quota values. A governed repository MAY extend the list only through its own committed configuration.
- A change is a CONFIG-VALUE change when every line it changes is the value of a key on that list, in a file of the pattern that list names. Adding, removing or renaming a listed key, or changing any other line, makes it NOT a config-value change.
- For a config-value change, the pre-commit gate, the pre-push gate and the CI gate job MUST run schema and parse validation of every changed file, and MUST run no test suite. A value that fails that validation MUST fail the gate, and the failure MUST name the file and the key.
- The config-value classification MUST be computed from the change's diff alone, with the same result on the `pull_request` and on the `push` to `master` of the same change. The two MUST run the same reduced set, so the PR gate is still never a subset of the master gate.
- `ci_gate_parity` MUST continue to fail any gating job conditioned so that it runs on a `push` to `master` but is skipped or reduced on a `pull_request`. The config-value class is the ONE changeset predicate it admits, and it admits that predicate only when the predicate is read from the committed list and applied identically on both events.
- Every other change MUST run the full aggregate exactly as before.

Also add a companion rule, **No test is tied to a committed config value.** A test MUST NOT assert the literal committed value of a key on the config-value fast-path list. A test of such a key MUST assert the value's shape or its derivation, or MUST exercise behaviour against a fixture value the test writes itself. Without this rule a config-value change could pass the reduced gate and redden the full aggregate on the next ordinary change.

In `scenarios.md`, add:

## A capacity value change passes on schema validation alone

Given a governed repository whose committed config-value fast-path list names `.livespec.jsonc` `dispatcher.wip_cap`
When a pull request changes only the value of `dispatcher.wip_cap` from 4 to 6
Then its pre-push gate and its CI gate job run schema and parse validation of `.livespec.jsonc` and no test suite
And the push to master of the same change runs the same reduced set
And a pull request that changes `dispatcher.wip_cap` to a value the schema rejects fails, naming the file and the key
And a pull request that also changes any other line runs the full aggregate
