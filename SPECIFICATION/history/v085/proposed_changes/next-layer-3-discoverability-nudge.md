---
topic: next-layer-3-discoverability-nudge
author: claude-opus-4-7
created_at: 2026-05-26T05:40:09Z
---

## Proposal: require-next-skills-to-nudge-toward-layer-3-loop-driver-on-direct-invocation

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Add a contract clause requiring every Layer-2 `next` skill's SKILL.md prose — both `/livespec:next` (per §"`/livespec:next` spec-side thin-transport skill") and every impl-plugin's `next` (per §"Implementation-plugin contract — the 10-skill surface" → "next") — to surface a discoverability nudge before invoking the underlying wrapper. The nudge MUST inform the user that the project-local Layer 3 loop driver at `.claude/skills/loop/SKILL.md` is the cohesive cross-side composition surface and ask the user to confirm they want to run `next` directly rather than via `/loop`. The wrapper itself remains a pure thin-transport pass-through; the nudge lives entirely in SKILL.md prose so the architectural property codified in §"Thin-transport skill doctrine" is preserved.

### Motivation

The three-layer orchestration architecture (per `spec.md` §"Three-layer orchestration architecture") places cross-side composition at Layer 3 — the project-local `.claude/skills/loop/SKILL.md` driver — and explicitly forbids Layer 2 (`/livespec:next` and `<impl-plugin>:next`) from baking in a cross-side weighting. The doctrine is load-bearing and correct, but it has a discoverability hole: a user (or an agent) who invokes `/livespec:next` or `<impl-plugin>:next` directly gets a single-sided answer and no signal that a more cohesive surface exists. The two thin-transport skills currently appear in skill-list output, in `/help`-style descriptions, and in agent-trigger phrases (e.g., "what should I work on next?") with no breadcrumb pointing at the Layer 3 driver. The result is that users who don't already know about the `loop` driver invoke the Layer 2 skills directly, get the spec-side-only or impl-side-only view, and never discover the cohesive cross-side composition the architecture was designed to provide.

The fix is a one-time SKILL.md-prose nudge: before invoking the wrapper, the SKILL.md prose instructs the agent to inform the user that `.claude/skills/loop/SKILL.md` (or whatever Layer 3 driver the project ships) is the cohesive surface, and to confirm they want the single-sided ranking. The nudge is enforced at the SKILL.md-prose layer — the wrapper stays a pure pass-through — which preserves the thin-transport doctrine (wrappers MUST NOT accrete logic; SKILL.md is the LLM-driven shaping layer that the agent reads) and keeps Layer 3 composition Layer-3's concern (the nudge is informational, not behavioral; it never picks the cross-side weighting itself).

The same discipline applies symmetrically across the spec-side `/livespec:next` (defined here) and every impl-plugin's `next` (defined by the 10-skill surface contract). Pinning the requirement once in this spec's contracts.md, with a cross-reference in the impl-plugin contract bullet, ensures every impl-plugin author inherits the discoverability discipline at contract-pin time.

### Proposed Changes

**Edit 1.** Append to `SPECIFICATION/contracts.md` §"`/livespec:next` spec-side thin-transport skill" a new subsection between the existing §"`.livespec.jsonc` configuration" and §"Cross-side composition exclusion":

> ### Layer 3 discoverability nudge
>
> The `/livespec:next` SKILL.md prose MUST surface a one-time discoverability nudge before invoking the wrapper on direct user invocation. The nudge MUST:
>
> 1. Inform the user that `.claude/skills/loop/SKILL.md` (the project-local Layer 3 loop driver per `spec.md` §"Three-layer orchestration architecture" → "Layer 3 — Project-local composition") is the cohesive cross-side composition surface that combines `/livespec:next` with the active impl-plugin's `next`.
> 2. Ask the user to confirm they want to run `/livespec:next` directly rather than via the project's Layer 3 driver.
> 3. Skip the nudge when `/livespec:next` is invoked by another skill (e.g., the Layer 3 driver itself, the `doctor` cross-boundary surface) rather than by a direct user request. The skill MAY detect the calling context via the standard SKILL.md invocation-context conventions; the detection mechanism is per-harness and out of scope here.
>
> The nudge lives entirely in SKILL.md prose. The wrapper at `.claude-plugin/scripts/bin/next.py` MUST NOT accrete a confirmation dialogue, an opt-in flag, or any other interactive layer — the wrapper remains a pure thin-transport pass-through per §"Thin-transport skill doctrine". The nudge is informational: it points the user at the Layer 3 surface but never selects the cross-side weighting itself, preserving the §"Cross-side composition exclusion" invariant.
>
> Projects whose `.claude/skills/loop/SKILL.md` is absent (the file is OPTIONAL per `spec.md` §"Layer 3 — Project-local composition") MAY soften the nudge to a documentation pointer (e.g., "consider authoring a Layer 3 loop driver per `spec.md` §...") rather than suppressing it. The discoverability discipline applies whenever direct user invocation is the entry path, regardless of whether the driver exists.

**Edit 2.** Append to `SPECIFICATION/contracts.md` §"Implementation-plugin contract — the 10-skill surface" → bullet `next` a parallel clause at the end of the bullet:

> The impl-plugin's `next` SKILL.md prose MUST surface a Layer 3 discoverability nudge on direct user invocation, parallel-and-symmetric to the requirement on `/livespec:next` codified in §"`/livespec:next` spec-side thin-transport skill" → §"Layer 3 discoverability nudge". The wrapper at `<impl-plugin>'s` `.claude-plugin/scripts/bin/next.py` MUST remain a pure thin-transport pass-through; the nudge is SKILL.md-prose discipline only. The impl-plugin author MAY specialize the nudge wording to reference the active backend (e.g., name the JSONL substrate, the beads database, or the GitLab project) but MUST preserve the load-bearing semantics: inform the user that the Layer 3 driver is the cohesive cross-side surface, and ask them to confirm direct invocation.

**Edit 3.** Update `SPECIFICATION/spec.md` §"Three-layer orchestration architecture" → "Cross-side composition belongs at Layer 3" paragraph to add a closing sentence pointing at the discoverability nudge as the discipline that prevents users from accidentally bypassing Layer 3:

> The cross-side composition discipline is reinforced by the §"Layer 3 discoverability nudge" requirement in `contracts.md` (defined for both `/livespec:next` and every impl-plugin's `next`): direct user invocation of either Layer 2 ranker MUST surface a one-time nudge informing the user that the project-local Layer 3 driver at `.claude/skills/loop/SKILL.md` is the cohesive cross-side surface and asking them to confirm direct invocation. The nudge is informational; the wrapper layer below remains a pure thin-transport pass-through. Together, the doctrinal exclusion (Layer 2 MUST NOT bake in a weighting) and the discoverability nudge (Layer 2 MUST point users at Layer 3) keep cross-side composition where the architecture places it.

**Edit 4 (companion downstream change).** This contract clause requires every consumer's `next` SKILL.md to be regenerated at the next `/livespec:revise` pass in livespec, livespec-impl-plaintext, and any future `livespec-impl-*` plugin. Each consumer's own propose-change cycle MUST land a companion SKILL.md update; the upstream contract clause is the load-bearing requirement, the per-consumer SKILL.md edits are the implementation. The companion change in `livespec-impl-plaintext` is filed in parallel under that repo's `SPECIFICATION/proposed_changes/next-layer-3-discoverability-nudge.md`. The two propose-changes are coordinated by a tracking epic in this repo's `work-items.jsonl` whose `depends_on` array references both PRs via the cross-repo `pull_request` `DependsOnEntry` kind (per §"Cross-repo dependency awareness" → §"DependsOnEntry typed union"). The epic stays open until `no-stalled-epic` doctor invariant detects both PRs merged.
