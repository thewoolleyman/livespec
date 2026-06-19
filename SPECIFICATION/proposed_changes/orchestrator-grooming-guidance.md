---
topic: orchestrator-grooming-guidance
author: claude-opus-4-8
created_at: 2026-06-19T07:12:54Z
---

## Proposal: Orchestrator-internal grooming guidance (non-functional, repo-agnostic)

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add a new `#### Orchestrator-internal grooming guidance` subsection to `non-functional-requirements.md`, placed immediately after the existing `#### Orchestrator-internal Dispatcher guidance` subsection (both under `### Implementation plugin ecosystem`). The new subsection records, as repo-agnostic non-functional GUIDANCE for orchestrator authors, the human-led front-end work-breakdown pattern that sits BEFORE autonomous dispatch — the slice cut-line, the intake Definition-of-Ready, the agent-drafts/human-approves regroom pass, and slice-size calibration. It states explicitly that core gets the guidance only: NO new skill, NO new CLI, NO new doctor invariant; the concrete realization belongs to the reference orchestrator's own specification. It is structurally a `####` (H4) subsection only — no `## ` (H2) heading is added, renamed, or removed, so `tests/heading-coverage.json` is unaffected.

### Motivation

Graduate the repo-agnostic grooming PATTERN from research (`research/dark-factory-operability/work-breakdown.md`) into the spec as durable architectural guidance. The work-breakdown research settled on the functional/non-functional split as its spine: grooming operates on the orchestrator-internal Ledger, so it is NOT core functional contract; but the repo-agnostic pattern/guidance IS non-functional core content, and its home is `non-functional-requirements.md` beside the existing Dispatcher guidance (per `non-functional-requirements.md` §"Boundary": functional files describe only what any livespec consumer inherits; livespec's own family infrastructure and orchestrator guidance are self-application and live in `non-functional-requirements.md`). The concrete realization — a groom front-end, ledger state, calibration mechanics — is a SEPARATE proposed-change against the reference orchestrator's own spec and is out of scope here.

### Proposed Changes

Insert ONE new `####` subsection into `non-functional-requirements.md` immediately after the existing `#### Orchestrator-internal Dispatcher guidance` subsection's final paragraph (the one ending with the cross-reference to the Beads/Dolt + Fabro dark factory carrying routine cross-repo work unattended) and immediately before the `### Codex dogfooding compatibility` heading. No existing text is modified, removed, or renamed. The new subsection is structurally an H4 (`#### `), so no `## ` heading set changes and `tests/heading-coverage.json` is unaffected.

The inserted subsection reads:

---

#### Orchestrator-internal grooming guidance

Like the Dispatcher guidance above, this is explicitly NON-normative on core's contract: core neither names nor verifies any of it. It records, for orchestrator authors, the human-led *grooming* discipline — the front-end work-breakdown that sits BEFORE autonomous dispatch, where a maintainer decides how work is split into the units the orchestrator's Loop and Dispatcher then carry. Grooming operates on the orchestrator-internal Ledger, so it is orchestrator-internal and belongs in the orchestrator repo's own specification; what core records here is the repo-agnostic PATTERN, not the realization. The guidance is repo-agnostic: a single-repo and a multi-repo project groom identically. Multi-repo coordination is `livespec`'s own family self-application — already covered in this document — and is NOT part of the general grooming pattern; the only functional tie between multi-repo work and core is the `.livespec.jsonc` CLI delegation seam.

Core deliberately gets the GUIDANCE only. This pattern introduces NO new core skill, NO new core CLI, and NO new core doctor invariant. The concrete realization — the groom front-end, the ledger state it reads and writes, and the calibration mechanics — belongs to the reference orchestrator's own specification (for the family's dogfood default, `livespec-impl-beads`'s `SPECIFICATION/`). The cut-line PRINCIPLE below reaches down to exactly ONE core *functional* concept: the scenario / acceptance.

**The slice cut-line.** A slice is the smallest unit with exactly ONE coherent "done". Two independent "done"s mean two slices: split. A slice's single "done" is verified one of two ways:

- *scenario-verified* — one named scenario passes (behavioral feature work); or
- *gate-verified* — the project's standing gates (its enforcement aggregate plus the `doctor` operation) fully define "done", with no scenario (configuration, spec-text, refactor, or cross-repo-bump work).

A slice-size FLOOR balances the cut-line against over-splitting: a unit is not split below the point where two slices cost more coordination than they save (for example, two changes with the same blast radius ride together). The floor is currently uncalibrated and rests on human judgement; see slice-size calibration below.

**The intake Definition-of-Ready.** A readiness checklist folded into the orchestrator's existing work-item capture front-ends — no new machinery; the capture aid auto-answers what it can and prompts the human only on the rest. An item is ready only when all of these hold; otherwise it is routed (not filed as ready):

- *one coherent "done"* — exactly one acceptance (one named scenario, or "the standing gates fully define done, no scenario"); an item that cannot name exactly one is an epic and routes to a regroom pass;
- *autonomously-verifiable acceptance* — an agent can confirm "done" with no human judgement call (the scenario passes, or the standing gates pass); an acceptance that needs human taste is given a verifiable acceptance or marked human-gated;
- *autonomy tier assigned* — a spec-change slice is human-gated (it routes through the propose-change / revise operations and is never auto-dispatched); every other slice is factory-dispatchable;
- *dependencies linked* — blockers are identified and linked; "ready" means blockers are closed AND an acceptance exists, never dependency-closure alone;
- *repo target named* — one slice targets one ledger / repo;
- *above the floor* — big enough to deserve its own slice rather than riding along with a same-blast-radius sibling.

**The agent-drafts / human-approves regroom pass.** The heavier breakdown that actually splits not-yet-ready items (epics, too-big items) into slices. It is the field's only published breakdown ritual: the orchestrator's groom front-end produces a read-only DRAFT, the human OWNS the cut and the acceptance and approves it, and only then are slices filed. The pass:

1. *read-only draft* — the groom front-end reads the epic, the relevant spec / scenarios, and the ledger, and drafts candidate slices with the intake fields above pre-filled; it files nothing yet;
2. *layer* — the drafted slices are arranged into dependency layers (no-blocker slices dispatch immediately; same-layer slices parallelize);
3. *human approves the cut* — the human edits the cut, acceptance, dependencies, and tiers and approves, or sends the draft back to re-draft;
4. *file on approval* — approved slices are filed via the existing capture machinery with dependencies linked; spec-change slices route to propose-change / revise rather than the factory;
5. *per-layer validation checkpoint* — after a layer converges, the standing gates and the named scenarios re-run before the next layer dispatches.

The regroom pass is triggered by an intake item marked needs-regroom (an epic) OR by factory non-convergence: a dispatched slice that will not converge IS the "too big" signal — it routes back to a human regroom pass, never an infinite retry. In an otherwise-autonomous loop this is the one human-in-the-loop step: the Dispatcher SURFACES needs-regroom items (escalate, do not drop), a human grooms and approves, and the factory drains the resulting ready slices.

**Slice-size calibration.** The field publishes no quantitative agent-sizing cut-point, so an orchestrator does not guess thresholds: it instruments. The approach emits, on the orchestrator's run journal, an outcome signal (did the slice converge to a merged result through the janitor gate without human rescue; the verify-then-fix loop count; an outcome class; the economic cost; whether it bounced to regroom) plus several mechanical size proxies (acceptance count, diff size, dependency fan-out, spec surface touched, dispatch-context size, archetype, repo), then correlates them to discover a ceiling — the proxy value(s) above which trouble spikes — empirically. The ceiling and the floor are asymmetric: the ceiling has a direct outcome signal (non-convergence, rising fix-loops) and calibrates straightforwardly; the floor has no direct signal — over-splitting's cost is a counterfactual the data never shows — so the floor needs a separate retrospective method and lags the ceiling. The ceiling is used two ways: reactively, by bailing after N fix-loops to a regroom pass (doable without calibration — it is the non-convergence trigger above); and predictively, by flagging an oversized slice at intake (which needs calibration, and the reactive bail-out is its training signal). Calibration is phased from a cold start: dispatch on the qualitative "one coherent done" with a human-guessed ceiling and reactive bail-out on while everything is instrumented; once runs accrue, an analysis pass proposes data-backed thresholds a human reviews and adopts; the adopted thresholds become advisory inputs to the size gate, re-calibrated as the model and codebase drift. The qualitative "one coherent done" stays the primary rule; the numbers are an advisory safety net the data calibrates.

**Hard versus advisory gating (resolved), by gate type.** The structural gates — one coherent "done"; an acceptance exists; dependencies linked — can be HARD: they are mechanically checkable and certain. The slice-size gate is ADVISORY: it is data-derived and uncertain, so it informs rather than blocks.

**Open questions (not resolved here).** The following are surfaced for a later decision rather than settled by this guidance: the slice-size FLOOR value (uncalibrated); whether the intake Definition-of-Ready and the regroom pass are better framed as ONE mechanism (the Definition-of-Ready gate plus what you do when it fails) rather than two; and the calibration sample size required before a threshold is trustworthy together with the re-calibration cadence against model and codebase drift.

---
