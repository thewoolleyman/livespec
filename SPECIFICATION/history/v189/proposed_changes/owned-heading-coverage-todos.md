---
topic: owned-heading-coverage-todos
author: claude-fable-5
created_at: 2026-07-04T09:12:24Z
---

## Proposal: Owned heading-coverage TODOs — auto-filed work-items; release gate narrows to unowned TODOs

### Target specification files

- spec.md
- non-functional-requirements.md

### Summary

Every `test: "TODO"` entry in `tests/heading-coverage.json` MUST carry a `work_item` field naming the open work-item that owns authoring the covering test; the revise flow files that work-item through the governed project's work-item capture seam at payload-assembly time and stamps its id into the entry. The `check-no-todo-registry` release-gate check narrows from rejecting ALL TODO entries to rejecting UNOWNED ones (a TODO missing a `work_item`), and the per-commit tier gains the same unowned-TODO rejection so unowned debt cannot land at all.

### Motivation

The v0.6.0..v0.6.4 incident (2026-07-04): a heading-coverage TODO registered by the v151 revise sat unowned for eight days, then silently failed the release gate on five consecutive releases while the `release` branch went stale and installed plugins ran old artifacts — including holding the unrelated seed-idempotency fix hostage. The existing design has a real justification — spec leads implementation, so a revise ratifying future behavior cannot ship that behavior's passing test in the same commit — but that justification only covers the spec-ahead-of-implementation class. The incident TODO was testable the day it landed; it was pure deferral with no owner and no clock. Making every TODO carry an auto-filed owning work-item turns ambient debt into tracked, dispatchable work (the Dispatcher drains testable-now items within a cycle; spec-ahead items depend on the implementing work and close when the Gap closes), and narrowing the release gate to unowned TODOs stops tracked spec-lead debt from blocking unrelated releases. Stall visibility moves from the silent release gate to the Release-readiness canary and its failure-alerting path, which are already live.

### Proposed Changes

In `spec.md` §"Self-application", extend the heading-coverage co-edit rule: when a revise pass lands a `tests/heading-coverage.json` entry with `test: "TODO"`, the revise flow MUST (a) file a covering-test work-item through the governed project's work-item capture seam (the configured orchestrator's capture-work-item operation) during payload assembly, and (b) stamp the returned work-item id into the entry's new `work_item` field alongside the existing `reason`. When the covering test cannot exist until implementation lands (spec-ahead-of-implementation), the filed work-item SHOULD declare `depends_on` the implementing work-item(s) so the debt closes when the Gap closes. When no orchestrator is configured, the author MUST supply an explicit `work_item` value referencing the project's external tracker; the field is never optional for a TODO entry.

In `non-functional-requirements.md` §"Enforcement-suite invocation" (the release-gate targets clause), redefine `check-no-todo-registry`: at the release gate it rejects any UNOWNED TODO entry — one whose `test` is `"TODO"` and whose `work_item` field is absent, empty, or names a closed/nonexistent work-item where liveness is mechanically checkable — and no longer rejects owned TODO entries; additionally the check runs in the per-commit tier (always wired, fail mode) rejecting any TODO entry missing a `work_item` field, so unowned debt cannot land on master. The concrete field-validation semantics realized by the shared check ship with the enforcement suite (livespec-dev-tooling) per §"Sibling spec ownership"; this spec owns the policy: no unowned heading-coverage debt on master, and releases blocked only by unowned debt.
