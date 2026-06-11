---
proposal: retire-next-loop-driver-discoverability-nudge.md
decision: accept
revised_at: 2026-06-11T01:00:41Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Accepted as filed: retire the loop-driver discoverability nudge outright. (a) Its normative home (spec.md §"Layer 3 discoverability") was deleted at v103; (b) it points at /livespec-orchestrate, which wave W6 retires at the cutover gate; (c) orchestrators own their own discoverability per the v103 decision record — core's spec-side prose advertises no particular orchestrator (specify architecture, not mechanism); (d) the retired text is preserved in git history (recover via `git show a194b9de87b1bb8497c9f8bb19645099663c98df:.claude-plugin/prose/next.md`); no relocation target is warranted. No SPECIFICATION/ content or H2 heading changes, so no heading-coverage delta.

## Resulting Changes

- ../.claude-plugin/prose/next.md
