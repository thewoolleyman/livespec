# orchestrator-surface-parity — design (captured for later work)

## Status
CAPTURED 2026-07-07 for LATER work — maintainer-directed NOT to be tackled inside the needs-attention track (epic livespec-bj9x). Decision is settled and slices are identified; execution is deferred to a future session that resumes this thread.

## Problem
The two livespec orchestrator plugins ship DIVERGENT skill surfaces:
- `livespec-orchestrator-beads-fabro`: 12 skills, packaged for BOTH runtimes (`.claude-plugin/skills/` AND `.claude-plugin/.codex-plugin/skills/`).
- `livespec-orchestrator-git-jsonl`: 8 skills, Claude-only — it has **no `.codex-plugin/` at all**; its skills "work" on Codex only by an accidental fallback to the Claude `SKILL.md`.

Canonical set (the 12, from beads-fabro): capture-impl-gaps, capture-spec-drift, capture-work-item, detect-impl-gaps, drive, groom, implement, list-plan-threads, list-work-items, needs-attention, next, plan. git-jsonl is missing 4: **drive, groom, list-plan-threads, plan**.

Two parity gaps:
1. **Runtime parity** (within an orchestrator, Claude ≡ Codex): git-jsonl ships zero Codex packaging — the severe fail. This is what surfaced the confusing duplicate needs-attention in the Codex picker (two entries, indistinguishable because Codex truncates the shared `livespec-orchestrator-` prefix, and their descriptions came from different packaging layers — beads-fabro's `.codex-plugin` file vs git-jsonl's Claude fallback).
2. **Cross-orchestrator parity** (beads-fabro ≡ git-jsonl skill set): git-jsonl has 4 fewer skills.

## Decision (maintainer, 2026-07-07)
**FULL PEER** — identical skill SET across all orchestrators, each skill packaged for BOTH Claude + Codex runtimes, every skill description leading with its owning plugin name, mechanically enforced. git-jsonl becomes a full peer (gains drive/groom/plan/list-plan-threads + a full `.codex-plugin`). This SUPERSEDES git-jsonl's OR3 v017 "reduced scope" (which merely documented git-jsonl's incompleteness, not a hard capability limit — the factory and plan-threads are not beads-specific).

## Precedent
Core `contracts.md` already mandates the *Driver* "exposes the same eight operations" on both Claude and Codex. There is NO equivalent enforced contract for the *orchestrator* skill surface — that hole let git-jsonl ship Codex-broken. This thread closes that hole for the orchestrator surface.

## Slice plan (6)
- **P1** [core spec, propose-change → revise]: the canonical orchestrator skill set + cross-runtime identity + cross-orchestrator identity + description-leads-with-plugin convention. Architecture-level, mechanically checkable. Requires independent adversarial review + maintainer-gated ratification.
- **P2** [core dev-tooling, dep P1]: the enforcement check — a canonical skill manifest in core; per-orchestrator verification that it ships exactly the canonical set on BOTH runtimes + the description convention. Wired into `just check` (runs in every orchestrator repo).
- **P3** [git-jsonl, dep P1 + P4]: gain drive, groom, plan, list-plan-threads + a full `.codex-plugin` (all 12 skills, both runtimes). The bulk of the work (4 heavyweight authored skills + Codex packaging).
- **P4** [git-jsonl spec, propose-change → revise]: supersede OR3 v017 reduced-scope (git-jsonl is now a full peer).
- **P5** [both orchestrators]: skill descriptions lead with the owning plugin + single-source the Claude/Codex descriptions so they stop drifting.
- **P6** [beads-fabro]: reconcile its own `.claude`/`.codex` needs-attention description drift (its Claude blurb says "…plan-thread, and hygiene…"; its Codex blurb says "Compose the repo attention primitives into Markdown or JSON").

## Open questions (to settle when the thread is resumed)
- Canonical skill set: exactly-identical-12 (rigid) vs a required floor + allowed backend-specific extras? The decision leaned exactly-identical; confirm at P1.
- Cross-orchestrator identity enforcement needs a canonical manifest in core (no single repo sees both orchestrators) — design the manifest + per-repo check.
- Confirm git-jsonl's backend genuinely supports drive (a factory/dispatcher) + plan-threads (believed yes — neither is beads-specific).

## Relationship to other work
- Sibling of `factory-safe-by-default` (epic livespec-nrdk) — both are "mechanical fleet-consistency enforcement," but distinct concerns.
- Interacts with `needs-attention` (epic livespec-bj9x): P5's description fix is what resolves the Codex-picker confusion the maintainer hit; it is deliberately deferred OUT of the needs-attention track into this thread.
