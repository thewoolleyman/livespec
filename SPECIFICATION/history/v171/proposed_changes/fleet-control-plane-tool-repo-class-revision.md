---
proposal: fleet-control-plane-tool-repo-class.md
decision: accept
revised_at: 2026-07-20T15:40:27Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Accepted per maintainer ruling 2026-07-20 (D9, recorded in plan/overseer-productization/handoff.md): the livespec overseer moves to a dedicated `livespec-overseer` repo registered under the manifest's `fleet` array as a full member, and D7 ruled it a Control-Plane artifact, so it needs a Control-Plane class. `console` cannot be reused because `_PIN_WEB_CLASSES` is the subtraction set `_ALL_CLASSES - {"console"}`: classing the overseer as `console` would either deny it the auto-bump PRs its dev-tooling-sourced gates require, or drag the pure-Rust `livespec-console-beads-fabro` into the bump web. The proposal passed two independent adversarial Fable reviews; the first returned BLOCKERS FOUND (two unamended enumerations of the closed class set), which was FIXED rather than waived, and the re-review of the amended text returned NO BLOCKERS. Replacement-target fidelity was re-verified against live master immediately before this accept. The two ride-along co-edits are included so no unamended enumeration is left contradicting the amended contract. No `## ` heading is added, renamed, or removed, so tests/heading-coverage.json needs no co-edit.

## Resulting Changes

- non-functional-requirements.md
- ../.livespec-fleet-manifest.jsonc
- ../.claude/skills/needs-attention-fleet/SKILL.md
