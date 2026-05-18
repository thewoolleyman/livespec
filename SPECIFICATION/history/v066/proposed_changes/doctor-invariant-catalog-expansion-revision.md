---
proposal: doctor-invariant-catalog-expansion.md
decision: accept
revised_at: 2026-05-18T22:12:13Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Accepting all three `## Proposal:` sections in doctor-invariant-catalog-expansion as one atomic landing per the 2026-05-18 post-orchestration batch's dependency-order plan. The three proposals are mutually reinforcing: (1) the transient-vs-durable-pending principle in `spec.md` §"Terminology" articulates why doctor's hygiene enforcement is asymmetric across queue/archive categories, and is load-bearing for any future invariant-catalog expansion; (2) the four work-item structural invariants (gap-tracking-one-to-one, no-orphan-blocker, no-stale-gap-tied, no-duplicate-gap-id) added to `contracts.md` as a new §"Doctor cross-boundary invariants" section name what doctor MUST check via the impl-plugin's `list-work-items` / `capture-impl-gaps` thin-transport / heavyweight skills, with the cross-boundary check exit-code semantics and registry-enumerability requirement landing in `constraints.md` as a new §"Cross-boundary doctor static checks" subsection alongside accept-decision-snapshot-consistency; (3) the contract-version-compatibility doctor invariant closes the loop between the v064 pin-and-bump mechanism and doctor's enforcement, landing as a subsection under the new §"Doctor cross-boundary invariants" section in `contracts.md`. Wording follows research/workflow-processes/architecture-summary.html (Decisions 16, 19, 20) and research/workflow-processes/tool-agnostic-workflow.md (the Doctor / Durable-pending / Transient / Memo glossary entries). The two new spec.md terminology entries are placed in alphabetical order around the existing **Intent** entry (**Durable-pending** before **Intent**; **Transient** after **Intent**) per the proposal text. `tests/heading-coverage.json` is updated alongside this commit with one TODO+reason entry for the new contracts.md `## Doctor cross-boundary invariants` heading.

## Resulting Changes

- spec.md
- contracts.md
- constraints.md
- ../tests/heading-coverage.json
