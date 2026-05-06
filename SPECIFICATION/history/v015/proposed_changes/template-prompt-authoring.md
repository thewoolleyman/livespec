---
topic: template-prompt-authoring
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-06T04:32:25Z
---

## Proposal: Bookkeeping closure of deferred-item `template-prompt-authoring`

### Target specification files

- (none — bookkeeping closure record; no `SPECIFICATION/` content edits required)

### Summary

Record the closure of deferred-item `template-prompt-authoring` (item 1 of `brainstorming/approach-2-nlspec-based/deferred-items.md`). The mechanism for specifying built-in template content — prompt interview flows, starter content, NLSpec-discipline internalization, delimiter-comment formats, critique/revise prompt output structures — is the template sub-specification tree under `SPECIFICATION/templates/<name>/` per v018 Q1-Option-A, materialized by Phase 6 (initial multi-tree seed) and Phase 7 (per-template prompt regeneration cycles). No `SPECIFICATION/` content edit lands with this revise; the audit-trail entry is the propose-change file landing in `SPECIFICATION/history/vNNN/proposed_changes/template-prompt-authoring.md` per v038 D1 Statement B's "every successful revise cuts a version, byte-identical-to-prior spec files when no decision is `accept`/`modify`" contract.

### Motivation

The deferred entry `template-prompt-authoring` was raised in v001 of the brainstorming and carried forward through v017. v018 Q1 closed it: the mechanism is now the template sub-specification tree under `SPECIFICATION/templates/<name>/` (PROPOSAL.md §"Template sub-specifications (v018 Q1)", line 1076 of the frozen-at-v039 PROPOSAL). Phase 6 of the bootstrap plan seeded both built-in templates (`livespec` and `minimal`) atomically with the main spec via `bin/seed.py`, materializing the sub-spec scaffolds. Phase 7 widened sub-spec content via per-prompt `propose-change --spec-target SPECIFICATION/templates/<name>/` → `revise --spec-target ...` cycles per v018 Q1-Option-A's agent-generated-from-sub-spec contract:

- `livespec` sub-spec: seed/propose-change/revise/critique prompts regenerated through Phase-7 sub-steps (c).2–(c).5 (livespec sub-spec versions v003–v006, plus the (c).6 starter-content authoring against the now-canonical sub-spec).
- `minimal` sub-spec: delimiter-comment format codified at sub-step (d).1 (sub-spec v002, commit `02ae376`); seed/propose-change/revise/critique prompts regenerated through sub-steps (d).2–(d).5 (sub-spec versions v003–v006); minimal `specification-template/SPECIFICATION.md` starter content authored at sub-step (d).6.

The delimiter-comment format mandate originally enumerated under v014 N9 for the `minimal` template's prompts is now codified at `SPECIFICATION/templates/minimal/contracts.md` §"Delimiter-comment format". Phase 7 sub-step (f) additionally landed the prompt-QA harness machinery exercising every regenerated REQUIRED prompt against canonical fixtures (per the joint resolution with deferred-item `prompt-qa-harness`).

This closure records that the v018 Q1 mechanism shipped per the plan and that no further `template-prompt-authoring`-scoped work remains. The deferred entry stays in `brainstorming/approach-2-nlspec-based/deferred-items.md` AS-IS per the Phase 8 plan's exit criterion ("brainstorming is frozen"); the authoritative state — that this work is complete — is preserved in `SPECIFICATION/history/vNNN/proposed_changes/template-prompt-authoring.md` after this revise lands.

### Proposed Changes

No `SPECIFICATION/` content edits. The revise decision is `reject` with rationale = closure record. Per v038 D1 Statement B, the revise still cuts a new version; the version's spec files are byte-identical copies of the prior version's spec files; the version's `history/<vNNN>/proposed_changes/` directory holds this propose-change file as the audit-trail record of the closure.

### Anchors

- **PROPOSAL.md** §"Template sub-specifications (v018 Q1)" (line 1076 of the frozen-at-v039 PROPOSAL.md) — sub-spec mechanism.
- **PROPOSAL.md** §"SPECIFICATION directory structure" (line 950+) — directory-shape contract for `SPECIFICATION/templates/<name>/`.
- **`SPECIFICATION/templates/minimal/contracts.md`** §"Delimiter-comment format" — codified format for the `minimal` template's delimiter comments.
- **`brainstorming/approach-2-nlspec-based/deferred-items.md`** §`template-prompt-authoring` — original entry text marked CLOSED in v018 Q1.
- **`brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`** Phase 8 item 1 — the closure-record disposition for this deferred entry.
- Phase-7 anchor commits: `02ae376` (minimal v002), `2ab22b6` (minimal v003 atomic), `312321e` (minimal v004), `46e4a44` (minimal v005), `04d120e` (minimal v006); plus the analogous livespec sub-spec cycle commits at sub-steps (c).2–(c).6.
