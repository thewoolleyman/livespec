---
topic: retire-next-loop-driver-discoverability-nudge
author: claude-fable-5
created_at: 2026-06-11T00:59:16Z
---

## Proposal: retire-next-loop-driver-discoverability-nudge

### Target specification files

- .claude-plugin/prose/next.md

### Summary

Retire the loop-driver discoverability nudge from the core next prose outright (no re-codification). Step 1 of `.claude-plugin/prose/next.md` ("Surface the loop-driver discoverability nudge") is removed, the remaining steps renumber, and the "When to run" parenthetical advertising livespec's repo-local cross-repo orchestration driver is dropped in favor of the generic composing-loop-driver wording. No SPECIFICATION/ file content changes and no `## ` heading changes (no heading-coverage delta); the new history/vNNN snapshot records the decision.

### Motivation

From W2 slice B (PR #397) the nudge survived in prose/next.md only as a neutrally re-registered carry-over, and work-item livespec-phh3 (epic livespec-4moata) calls the spec-side question: retire or re-codify. Retirement is correct because: (a) the nudge's original normative home (spec.md §"Layer 3 discoverability") was deleted at v103, so the nudge has had no normative spec anchor since; (b) the nudge points the user at /livespec-orchestrate, which wave W6 retires at the cutover gate; (c) under the v103 decision record, orchestrators own their interactive front-ends and their own discoverability — core's spec-side prose does not advertise any particular orchestrator (specify architecture, not mechanism; spec.md §"Contract + reference implementations architecture" → "No required cross-repo loop driver"); (d) preservation: the retired nudge text remains recoverable in git history — last shaped by commit a194b9de87b1bb8497c9f8bb19645099663c98df (blob 2a4ae004b501a453206e1fb0d88ecc8712b4e780 at pre-change HEAD 5cbb22ac8c1109fb37e2765ff10619deacc6bfda; recover via `git show a194b9de87b1bb8497c9f8bb19645099663c98df:.claude-plugin/prose/next.md`). No relocation target is warranted: the Dispatcher's discoverability belongs to the orchestrator repo's own docs (livespec-impl-beads already documents its CLIs). The target artifact `.claude-plugin/prose/next.md` is core-owned harness-neutral prose outside the SPECIFICATION/ tree; it is named project-root-relative here and updated via the revise pass's resulting_files mechanism, the same co-edit pattern the heading-coverage discipline uses.

### Proposed Changes

In `.claude-plugin/prose/next.md`: (1) Step 1 ("Surface the loop-driver discoverability nudge.") MUST be removed in its entirety, including the SKIP-on-composed-invocation rule and the informational-only paragraph; the prose MUST NOT re-introduce any orchestrator-discoverability dialogue. (2) The remaining steps MUST be renumbered ("Invoke the next CLI" becomes Step 1; "Present the JSON verbatim" becomes Step 2) and the Failure-handling cross-reference "per Step 3" MUST be updated to "per Step 2". (3) In "When to run", the parenthetical naming livespec's repo-local cross-repo orchestration driver MUST be dropped; the bullet MUST retain the generic statement that a composing loop driver (non-contract working tooling per `SPECIFICATION/spec.md` §"Contract + reference implementations architecture" → "No required cross-repo loop driver") calls this operation as one of the `next` primitives it composes. (4) Core prose MUST NOT advertise any particular orchestrator's front-end; orchestrator discoverability is owned by the orchestrator's own documentation. (5) No SPECIFICATION/ spec file content changes and no `## ` heading set changes are part of this proposal, so `tests/heading-coverage.json` MUST NOT change.
