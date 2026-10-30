## The maintainer's statement of what done means

OK, so the stopgap low hanging fruit is the Spec-side autonomy follow-up, correct? You can go ahead and update your plan with all these findings and research (capture research doc as appropriate) , but only  after you kick off that follow-up plan and get it running, and hand off to the coordinator?  Is my understanding correct?

## Definition of Done assertions derived from that statement

- The released livespec core revise prose asks the maintainer for per-proposal confirmation only when the effective revise decision mode or a core floor requires maintainer input, and states that a delegated non-drift proposal auto-spawns its independent reviewer even when the effective ratification review resolves to manual-spawn.
- The released Claude, Codex and pi Driver revise bindings describe the operation in their discovery descriptions and runtime-binding wording in terms that cover both manual confirmation and configured delegated decision ownership, without naming a fixed reviewer model.
- The released livespec-orchestrator-beads-fabro explanatory wording for the spec-change-tier hold describes release on ratification of the linked proposal rather than on a human ratifying it, while the hold still refuses dispatch of a held item until that proposal ratifies.
- An explicitly initiated, bounded delegated revise on an isolated governed fixture, driven through the released installed Driver and core surfaces, ratifies a non-drift proposal only with an independent reviewer's NO BLOCKERS verdict and an independent delegated decider's acceptance both bound to the same final-bytes digest recorded in the new revision.
- On the same fixture, a proposal under manual decision ownership and a proposal hitting a core floor each stop for explicit maintainer confirmation instead of being ratified by the delegated path.

# Opening research — spec-autonomy-followup

Created 2026-10-30 by Claude Code session `ce19c72a-238e-4973-bbde-0a4f85197eb8`, launched from a
dispatch-control-plane brief (repo `thewoolleyman/livespec-orchestrator-beads-fabro`, plan
`dispatch-control-plane`) under the maintainer authorization quoted verbatim as this plan's
Definition of Done statement above.

## Purpose

A focused, low-hanging stopgap: make the spec-side **delegated revise** path that the ratified
spec ALREADY defines actually usable and honestly described, then prove it once on an isolated
fixture. This plan does not build anything new; it removes contradictions between the ratified
contract and the surfaces that drive it.

## Why (the observed failure)

The ratified contract (`thewoolleyman/livespec` `SPECIFICATION/spec.md` §"revise" decision
ownership, lines ~243–295 at commit `f4b26fb9`) says:

- `effective_revise_decision_mode` resolves per file: design-record contradiction / missing
  design record / ratification-review blocker / drift-origin floors first, then a per-proposal
  `decision_policy`, then the global `spec_governance.revise_decision_mode`, then `manual`.
- Under `delegated`, a non-drift proposal is decided WITHOUT human input when an independent
  reviewer returns literal `NO BLOCKERS` and an independent delegated decider accepts, both bound
  to the exact same final bytes.
- "Delegated revise is stronger than manual revise": the delegated path MUST auto-spawn the
  reviewer "even when `effective_ratification_review` would otherwise resolve to `manual-spawn`".

The surfaces that drive it say otherwise:

1. **Core prose** — `thewoolleyman/livespec` `.claude-plugin/prose/revise.md` Step 5 (lines
   ~420–475): an unconditional bullet "**Prompt the user for confirmation.** Present each
   per-proposal decision ... and capture confirm / override" appears BEFORE "Resolve decision
   ownership per file"; the `modify` bullet says the LLM "iterates with the user in dialogue until
   the user confirms"; and the ratification-review bullet says "in `manual-spawn`, prompt the
   maintainer to provide the same evidence" with no statement of the delegated auto-spawn
   override. An agent reading top-to-bottom stops for a human even when the effective mode is
   `delegated`.
2. **Driver discovery descriptions** — the `revise` binding frontmatter in
   `livespec-driver-claude` (`.claude-plugin/skills/revise/SKILL.md`), `livespec-driver-codex`
   (`livespec/skills/revise/SKILL.md`) and `livespec-driver-pi`
   (`skills/livespec-revise/SKILL.md`) all begin "Walk the user through accepting or rejecting
   pending proposed changes ...". That advertises a human-only operation.
3. **Orchestrator explanatory comments** — `livespec-orchestrator-beads-fabro`
   `commands/_spec_change_tier_wall.py` (~line 21: "waiting on a human to ratify a proposal") and
   `commands/_dispatcher_loop_candidates.py` (~line 67: "until a human ratifies a proposal").
   These are COMMENTS only. The emitted refusal text in `_spec_change_tier_hold.py` names the
   topic and reason without claiming human-only authority, and the hold itself is valid and must
   be preserved.

## Configuration already armed (not proof of eligibility)

`.livespec.jsonc` in `livespec`, `livespec-orchestrator-beads-fabro` and `livespec-dev-tooling`
carry `revise_decision_mode: delegated`, `ratification_review: auto-spawn`,
`ratification_reviewer_model: ["sonnet"]`, `spec_pr_merge: auto-on-green`. That does NOT make
every pending proposal delegated-eligible: core floors (design-record, review-blocker,
drift-origin) and per-proposal `decision_policy` still apply and must be inspected per file.

## Related records (avoid duplication)

- `livespec-jvdvx4` (closed epic) shipped the levers; `livespec-jvdvx4.3`/`.4` shipped the
  resolver and floors. This plan does not redo them.
- `livespec-vb12` (backlog) records the old rollout shortfall; its "armed in ZERO repos" premise is
  stale (see config above). `livespec-yaig` (backlog) is a stale-proposal doctor invariant — out
  of scope here.
- `livespec-keou` (backlog) — `--only-topic` undiscoverable in summary surfaces; adjacent wording
  issue in the same descriptions, worth folding if the Driver description edits touch the same
  sentence.
- `plan/archive/spec-side-autonomy/research/brainstorm.md` (~line 216) assumed a foreman would RUN
  revise. `livespec-orchestrator-beads-fabro`
  `plan/archive/unattended-plan-operation/research/opening-research-2026-08-20.md` permits an
  already-running session's authorized spec operations.
- `livespec-console-beads-fabro`
  `plan/retire-overseer-and-redesign-control-plane-around-console/research/redesign-brainstorm-and-decisions.md`
  D3 / §5 propose staleness-triggered revise workflow variants with
  pluggable-factory-workflow-configs (`bd-ib-yqpdrt`). That is prior DESIGN, not deployment, and
  its integration belongs to `dispatch-control-plane`, not this plan.

## Scope boundary

In scope: repairing the three contradiction sites above (each in its owning repo through that
repo's normal filing seam); demonstrating the EXISTING delegated revise path once, explicitly
initiated and bounded, on an isolated governed fixture, through released installed surfaces;
preserving the manual path and every core floor.

Out of scope (owned elsewhere): a general autonomous spec-work scheduler; automatic discovery or
scheduled launching of revise; shared coordination DB/services; the full workflow-variants
rollout; bulk ratification of any production `proposed_changes/` queue; rescinding R219.
Cross-plan routing belongs to the coordinator session (`gitops-fleet-capacity-monitoring`,
`livespec-dev-tooling`).

## Repair shape (first cut)

Core prose: reorder Step 5 so decision ownership is resolved FIRST, and make the confirmation
bullet conditional ("when the effective mode or any floor requires maintainer input"); make the
`modify` iteration partner the effective decider (the maintainer under `manual`, the delegated
decider under `delegated`, both signals re-bound to the converged bytes); add the delegated
auto-spawn override to the ratification-review bullet. No spec change is needed — the spec is
already correct; this is a conformance fix of the prose to the ratified contract.

Driver descriptions: describe the operation neutrally (e.g. "Accept, modify, or reject pending
proposed changes — confirming each with the user, or under a configured delegated decision mode
with independent review — then snapshot ..."), without naming a reviewer model, in all three
Drivers.

Orchestrator comments: reword to "until its linked proposal ratifies" without changing behaviour.
