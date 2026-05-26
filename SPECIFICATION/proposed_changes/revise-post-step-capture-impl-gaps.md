---
topic: revise-post-step-capture-impl-gaps
author: claude-opus-4-7
created_at: 2026-05-26T07:30:00Z
---

## Cross-cutting parent

This PC is part of the coordinating epic `coordinating-epic-stale-revise-enforcement` (filed in this same repo, merged on master via PR #247). It contributes Layer 5 to the original 4-layer enforcement story: ensuring that spec changes accepted by `/livespec:revise` don't sit and never reach impl tracking because no one remembered to invoke gap detection.

This PC does NOT yet carry a `parent_proposed_change` front-matter field. That field is itself proposed in the parent PC (which has to widen `proposed_change_front_matter.schema.json` first). After acceptance, this PC SHOULD be retroactively edited to add `parent_proposed_change: coordinating-epic-stale-revise-enforcement`.

The Layer 5 companion PC lives at `livespec-impl-plaintext/SPECIFICATION/proposed_changes/capture-impl-gaps-since-version.md` and proposes the `--since-version` flag this PC's post-step depends on.


## Problem statement

After `/livespec:revise` cuts a `vNNN` snapshot accepting one or more proposed changes, NOTHING in the lifecycle ensures the impl side learns about whatever spec→impl gaps the accepted change introduced. The skill's post-step today runs doctor static (spec well-formedness) and exits. Detection of impl gaps is left to the user invoking `/livespec-impl-plaintext:capture-impl-gaps` separately, which they may never do — and the spec change then sits in the wild with no corresponding impl tracking.

This is the next failure layer after the original coordinating epic addressed orphaned revise branches (Layers 1-4). With Layers 1-4 in place, a revise lands on master cleanly. But the question "does anyone now KNOW the impl side has a gap to close?" still has no automatic answer.


## Proposal: invoke capture-impl-gaps as a revise post-step

### Target specification files

- skills/revise/SKILL.md

### Summary

Add a new sub-step to `/livespec:revise`'s post-step lifecycle, AFTER the existing post-step doctor static phase and AFTER the wrapper has fully archived the accepted PCs into `history/v<N+1>/proposed_changes/`. The sub-step invokes the active impl plugin's `capture-impl-gaps` skill (when available) with `--since-version <prior-vN>` to scope the scan to the diff just introduced.

The post-step is OPT-OUT: every detected gap surfaces via `capture-impl-gaps`'s existing per-gap consent dialogue. Defer / dismiss / skip are all valid responses — no user action is forced.

### Motivation

The minimal mechanical close of the spec→impl-tracking loop. Per the user's framing in the design discussion: "this should cover most of the case if we did it as long as it was always invoked immediately after the revise and the revise was completely finished and had already archived it."

The `--since-version` scoping (proposed in the impl-plaintext companion PC) is load-bearing here. Without scoping, the post-step would re-prompt for every long-standing gap on every revise — noisy enough that users would train themselves to dismiss it. With scoping, only NEW gaps introduced by this revise surface; the post-step's signal value stays high.

### Proposed Changes

Add a new Step 13 (or appropriate insertion point — confirmed at revise time) to `skills/revise/SKILL.md` §"Steps":

> **Step 13 — Capture impl gaps from this revise's changes.**
>
> AFTER the wrapper has exited 0 AND the post-step doctor static phase has completed AND the accepted proposed-change files have been fully archived into `<spec-target>/history/v<N+1>/proposed_changes/`:
>
> 1. Read the active impl plugin from `.livespec.jsonc`'s `implementation.plugin` key.
> 2. If the plugin advertises a `capture-impl-gaps` skill, invoke it with `--since-version <prior-vN>` where `<prior-vN>` is the version immediately preceding the just-cut `v<N+1>` (i.e., the highest `vNNN` directory present BEFORE this revise pass cut `v<N+1>`).
> 3. If the plugin does NOT advertise the skill, skip Step 13 silently (per the plugin-contract surface — not every impl plugin must implement gap detection).
> 4. The `capture-impl-gaps` invocation owns its own user dialogue (per-gap consent per the skill's existing flow). This SKILL.md prose surfaces the invocation but does NOT gate or wrap it.
>
> The user MAY skip the entire Step 13 via a new `--skip-post-step-capture-impl-gaps` flag (mutually exclusive with `--run-post-step-capture-impl-gaps`, per the precedence chain established by similar flag pairs in `seed`, `propose-change`, and `critique`). The default is `false` (run the step).

Add the new flag pair to the §"Inputs" section:

> - `--skip-post-step-capture-impl-gaps` (optional). Skips Step 13. Mutually exclusive with `--run-post-step-capture-impl-gaps`.
> - `--run-post-step-capture-impl-gaps` (optional). Forces Step 13 to run even when `post_step_skip_capture_impl_gaps` is `true` in `.livespec.jsonc`.

Add the corresponding config key to `.livespec.jsonc`'s skip-control inventory (per the existing pattern for `pre_step_skip_static_checks` and the LLM-driven-phase keys).

Narration rule (mirrors the existing silent-skip narration rule for doctor LLM-driven phase): when Step 13 is silently skipped (config key = true, no CLI flag), the SKILL.md prose MUST surface a warning narration. Explicit CLI skip → no narration (self-evident). Explicit CLI run override → no narration.


## Dependency on the companion PC

This PC's Step 13 invokes `capture-impl-gaps --since-version <prior-vN>`. That flag is the subject of the companion PC at `livespec-impl-plaintext#capture-impl-gaps-since-version` (filed at `livespec-impl-plaintext/SPECIFICATION/proposed_changes/capture-impl-gaps-since-version.md`).

The two PCs are independent at the SPEC level: livespec's SKILL.md can prospectively reference a flag that hasn't shipped in impl-plaintext yet. The IMPLEMENTATION of Step 13 (the SKILL.md prose actually causing the flag to be passed) needs the flag to actually exist; that's tracked in impl-plaintext's work-items after both PCs are accepted.

If the impl-plaintext PC is rejected, this PC's Step 13 needs minor rewording — invoke `capture-impl-gaps` without the flag and accept the noisy-post-step trade-off, OR depend on a different scoping mechanism. The reviser MAY modify this PC at revise time to make that decision.


## Acceptance criteria

This PC is complete when:

1. `/livespec:revise`'s SKILL.md carries Step 13 with the `--since-version <prior-vN>` invocation.
2. The new flag pair (`--skip-post-step-capture-impl-gaps` / `--run-post-step-capture-impl-gaps`) and config key (`post_step_skip_capture_impl_gaps`) are documented.
3. The silent-skip narration rule is documented per the existing pattern.
4. The plugin-advertisement check (impl plugin advertises `capture-impl-gaps` or skip silently) is documented.

This PC does NOT itself ship SKILL.md edits or wrapper changes. Acceptance via the next `/livespec:revise` cycle in this repo (livespec) cuts a new vNNN that lands the SKILL.md updates; subsequent impl follow-ups update the actual skill prose per TDD discipline.
