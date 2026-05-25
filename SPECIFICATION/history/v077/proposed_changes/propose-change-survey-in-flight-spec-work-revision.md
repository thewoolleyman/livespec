---
proposal: propose-change-survey-in-flight-spec-work.md
decision: modify
revised_at: 2026-05-25T05:01:07Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

The proposal's intent (force propose-change to enumerate concurrent in-flight design work before authoring) is sound and closes the documented architectural-drift gap from memo mm-jdmtgc (two competing v071 cross-repo-dep designs landed on different branches because neither propose-change session surveyed the other). Modified along three axes for structural consistency with the existing precedent. (1) Location: moved from contracts.md to spec.md as a new `### propose-change skill-prose responsibilities` H3 subsection under `## Sub-command lifecycle`, parallel to the existing `### revise skill-prose responsibilities` subsection the proposal cites as symmetric — skill-prose narration disciplines belong in spec.md, not contracts.md (which scopes wire-level interfaces). (2) Wrapper involvement: dropped the wrapper-enforcement aspect (`bin/propose_change.py` SHOULD perform the enumeration). The wrapper stays deterministic and network-free, matching the existing revise-narration pattern where the SKILL.md prose runs the survey via Bash invocations of git/gh. Wrapper enforcement would introduce network failure modes into a wrapper that currently has none. (3) `--no-survey` opt-out flag: dropped as premature CLI surface. The SKILL.md dialogue can already be steered by the user without a wire-level flag, and the flag can be reintroduced if friction emerges. Added explicit network-failure tolerance (degraded-survey warning rather than block) since the survey relies on network calls. The result is structurally symmetric with the existing revise narration discipline and avoids adding new CLI surface or wrapper obligations.

## Modifications

Relocated the rule from `contracts.md` (originally proposed as a new H2 section or addition under §'Cross-boundary handoffs') to `spec.md` as a new `### propose-change skill-prose responsibilities` H3 subsection under `## Sub-command lifecycle`, slotted between the existing `### revise skill-prose responsibilities` and `### prune-history skill-prose responsibilities` subsections. Phrased the narration discipline parallel to the existing revise discipline (skill prose MUST surface, MUST NOT gate wrapper, MUST NOT add doctor checks). Dropped the wrapper-enforcement bullet (the wrapper remains free of git/gh subprocess calls). Dropped the `--no-survey` CLI opt-out flag. Added explicit network-failure tolerance: failed `git fetch` / `gh` queries surface as a degraded-survey warning rather than blocking propose-change. Cross-referenced the symmetric revise narration so readers can navigate between the two narration disciplines.

## Resulting Changes

- spec.md
