---
topic: tests-that-run-a-real
author: claude-opus-5-5:fleet-flaky-tests
created_at: 2026-11-13T13:18:22Z
---

## Proposal: Tests that run a real script wait under one shared hang guard, never a tighter fixed bound

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

State the load-independent concurrency-wait rule for this repository's tests: a wait for something the code under test must do is unbounded or under one repository-wide hang guard of at least 120 seconds whose expiry fails the test naming what it waited for; expected-expiry waits and kill-teardown waits are excluded. Scoped to livespec's own tests. The livespec-dev-tooling bullet's exclusion of `tests/spec/test_homelab_worker_*.py` is specific to that repository and is dropped here.

### Motivation

A test that runs a real script or program as a child process under a fixed subprocess timeout fails on a loaded host though nothing is wrong. Measured in livespec-dev-tooling on 2026-11-13: tests/spec/test_homelab_worker_prove_vxlan_offload.py takes 28.9 s alone and 120.1 s inside a 68-minute loaded full suite, a 4.2x slowdown, so it hit its 120 s bound (orchestrator gate 20261113T112114Z-2445619, output.log lines 1484-1560). livespec-dev-tooling is ratifying this same rule as the "Load-independent concurrency waits" bullet of its v211 (draft livespec-dev-tooling#4518), and its spec-first sentence names the script-driving subprocess timeouts among the breaking sites. legacy-coordinator-agent ruled on 2026-11-13 that the rule is ratified fleet-wide rather than released item by item. The fleet-flaky-tests plan (epic livespec-dev-tooling-zwveqp) filed one carrier per repository; each carrier's filing-time spec-change tier record found the rule unstated and links this topic, `tests-that-run-a-real`. The carriers set their hang guard to max(900 s, 5x the slowest such test's isolated runtime), which meets this rule's 120-second floor. The two exclusions are named explicitly so a carrier does not stretch a wait whose expiry is the expected outcome, such as a controlled-clock advance delay, or a teardown wait that falls through to a forced kill.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md`, `## Spec` → `### Testing approach`, insert one new paragraph immediately after the paragraph that begins "Tests MUST NOT mutate files under `tests/fixtures/`" and before the paragraph that begins "The meta-test `tests/test_meta_section_drift_prevention.py`". No heading is added, removed or renamed, so `tests/heading-coverage.json` needs no co-edit. The paragraph reads exactly:

```markdown
**Load-independent concurrency waits.** A test's verdict MUST NOT depend on how fast the host runs it. When a test waits for something the code under test is required to do — a worker thread or child process to finish, or a barrier, event or condition to be reached — it MUST wait either without a wall-clock bound or under a hang guard. A hang guard is one value the repository defines once for every such wait, MUST be no shorter than 120 seconds, and its expiry MUST fail the test as a hang that names what the test was waiting for. A test MUST NOT bound such a wait more tightly, as `join(3)` followed by `assert not worker.is_alive()`, `Barrier(2).wait(timeout=3)` or `assert event.wait(timeout=2)` do. An exception raised in a test's worker thread MUST fail that test, and the failure report MUST name that exception, never surface only as a missing or short result. Two kinds of wait are outside this rule: a teardown wait whose expiry falls through to a forced stop and decides no verdict, and a wait whose expiry is the outcome the test expects, such as a check that a blocked party has not yet proceeded. The rule applies to this repository's tests. This paragraph is spec-first: tests in this repository still bound such waits with a fixed per-call value instead of the shared hang guard, namely the `subprocess` timeouts of tests that drive a script or command-line entry point — `_verdict` in `tests/integration/test_pipefail_shell_pipeline_verdicts.py` (60 seconds) and `_run` in `tests/integration/test_ci_host_rebuild_from_bare_metal.py` (300 seconds) — and work item livespec-foe46p owns the change.
```

