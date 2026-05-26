---
proposal: revise-post-step-capture-impl-gaps.md
decision: accept
revised_at: 2026-05-26T07:54:39Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Accepted as filed (PC #3 of the Wave 1 cross-cutting safety-net ratification, Layer 5 of the stale-revise-enforcement coordinating epic). The PC closes the spec→impl-tracking loop: after a /livespec:revise pass archives accepted proposed-change files into history/v<N+1>/, the active impl plugin's capture-impl-gaps skill is invoked with --since-version <prior-vN> so any new spec→impl gaps the revise introduced are surfaced immediately, rather than waiting for the user to remember to invoke gap detection separately. The spec-side acceptance lands the new contract — flag pair, config key, silent-skip narration rule, plugin-advertisement check — into spec.md §"Sub-command lifecycle" and §"`revise` skill-prose responsibilities". The actual SKILL.md prose edit, wrapper input-schema additions, and the companion --since-version flag in livespec-impl-plaintext's capture-impl-gaps skill are filed as separate impl follow-up work-items per the PC's own instruction ("This PC does NOT itself ship SKILL.md edits or wrapper changes").

## Resulting Changes

- spec.md
