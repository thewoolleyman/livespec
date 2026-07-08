---
topic: orchestrator-skill-set-contract
author: claude-opus-4-8
created_at: 2026-07-08T10:11:34Z
---

## Proposal: Canonical orchestrator skill-set contract — twelve skills, identical across runtimes and across orchestrators

### Target specification files

- contracts.md

### Summary

Establish a core contract fixing the **orchestrator skill surface** — the
interactive, model-invocable operations an orchestrator plugin
(`livespec-orchestrator-*`) exposes to an operator — at the same altitude
as the existing Driver "same eight operations" contract in
`contracts.md` §"Plugin distribution". The contract fixes four things:

1. **The canonical set.** Every orchestrator plugin ships exactly the same
   twelve skills: `capture-impl-gaps`, `capture-spec-drift`,
   `capture-work-item`, `detect-impl-gaps`, `drive`, `groom`, `implement`,
   `list-plan-threads`, `list-work-items`, `needs-attention`, `next`,
   `plan`.
2. **Cross-runtime identity** (within one orchestrator): the Claude and
   Codex skill surfaces are IDENTICAL — the same twelve, each packaged for
   BOTH runtimes, never one runtime's packaging with an accidental fallback
   for the other.
3. **Cross-orchestrator identity** (across all orchestrators): EVERY
   orchestrator ships the SAME canonical set — no orchestrator ships a
   subset — anchored by a canonical skill manifest owned by core, because
   no single repository sees more than one orchestrator.
4. **The description convention:** every orchestrator skill's description
   leads with its owning plugin name.

The contract is architecture-level and mechanically checkable; the
enforcement check itself is a separate, dependent slice (it is NOT part of
this proposal). This proposal establishes ONLY the contract and states that
it is mechanically enforced.

This SUPERSEDES `livespec-orchestrator-git-jsonl`'s prior "reduced scope"
declaration (its OR3 v017), which documented that orchestrator's partial
skill surface rather than a hard capability limit.

### Motivation

Core `contracts.md` §"Plugin distribution" already mandates that the
*Driver* "exposes the same eight operations" on both the Claude and Codex
runtimes — an operator finds the same spec-side surface regardless of
runtime. There is NO equivalent enforced contract for the *orchestrator*
skill surface. That hole let the two reference orchestrators diverge:
`livespec-orchestrator-beads-fabro` ships twelve skills packaged for both
runtimes (`.claude-plugin/skills/` AND `.claude-plugin/.codex-plugin/skills/`),
while `livespec-orchestrator-git-jsonl` ships only eight, Claude-only, with
no `.codex-plugin/` tree at all — its skills "work" on Codex only by an
accidental fallback to the Claude `SKILL.md`. That divergence surfaced as a
confusing duplicate `needs-attention` entry in the Codex skill picker, its
two rows indistinguishable because Codex truncates the shared
`livespec-orchestrator-` prefix and the two descriptions came from
different packaging layers.

Closing the hole at the orchestrator surface — a fixed canonical set, an
identical surface across runtimes and across orchestrators, and a
description convention that disambiguates the picker — makes the operator
experience uniform no matter which orchestrator a project selects, and
turns "did this orchestrator ship a complete, both-runtime surface?" from
an ambient hope into a mechanically verifiable invariant.

**One point to confirm at ratification — exact set vs. floor + extras.**
This proposal drafts the RIGID reading: every orchestrator ships EXACTLY
the twelve, with no orchestrator-specific additional model-invocable skill
permitted beyond them. The design record
(`plan/orchestrator-surface-parity/research/design.md`, its "Open questions")
leaned toward exactly-identical-twelve, but flagged the alternative of a
REQUIRED FLOOR of twelve with allowed backend-specific EXTRAS. This is the
one design choice the maintainer should confirm when ratifying: keep the
rigid exact-set reading drafted here, or relax the "no extras" clause to a
required floor. If the maintainer chooses floor + extras, the canonical-set
paragraph's exact-set clause and the heading (which asserts "twelve") are the
only text to adjust at revise.

### Proposed Changes

**In `contracts.md`, add a new `## ` section** immediately AFTER the
existing `## Orchestrator CLI contract — the three named CLIs` section and
BEFORE the existing `## Spec-side CLI contract` section, so the two
orchestrator-facing cross-boundary contracts (the machine CLI seam and the
operator skill surface) sit adjacent. The new section reads, verbatim:

```markdown
## Orchestrator skill-set contract — the canonical twelve

An orchestrator plugin (`livespec-orchestrator-*`) exposes its operator
surface as **skills** — the interactive, model-invocable operations an
operator or agent drives — distinct from the three config-named
orchestrator CLIs of §"Orchestrator CLI contract — the three named CLIs",
which are the machine seam core wires. This section fixes that skill
surface as a cross-orchestrator, cross-runtime contract, exactly as
§"Plugin distribution" fixes the Driver's "same eight operations" surface:
an operator MUST find the SAME orchestrator operations regardless of which
orchestrator plugin is installed or which agent runtime drives it. This
contract does NOT make core depend on any orchestrator — core remains
standalone-installable per `non-functional-requirements.md` §"Spec" (its
orchestrator-side skills are simply unavailable until a consumer installs
an orchestrator plugin) — it constrains what an orchestrator plugin MUST
ship WHEN one is installed.

**The canonical set.** Every `livespec-orchestrator-*` plugin MUST ship
exactly this set of twelve skills, identified by these skill names:
`capture-impl-gaps`, `capture-spec-drift`, `capture-work-item`,
`detect-impl-gaps`, `drive`, `groom`, `implement`, `list-plan-threads`,
`list-work-items`, `needs-attention`, `next`, `plan`. The set is EXACT: an
orchestrator MUST NOT omit any of the twelve, and MUST NOT expose an
additional model-invocable orchestrator skill beyond them. Renaming, adding,
or removing a canonical skill requires a propose-change cycle against this
section.

**Cross-runtime identity (within one orchestrator).** The Claude and Codex
skill surfaces of a single orchestrator plugin MUST be IDENTICAL — the same
canonical twelve, each packaged for BOTH runtimes: a Claude skill tree at
`.claude-plugin/skills/<name>/SKILL.md` AND a Codex skill tree at
`.claude-plugin/.codex-plugin/skills/<name>/SKILL.md`. An orchestrator MUST
NOT ship one runtime's packaging and rely on a fallback to the other
runtime's binding; each runtime's skill-discovery location MUST carry the
full canonical set explicitly.

**Cross-orchestrator identity (across all orchestrators).** EVERY
`livespec-orchestrator-*` plugin ships the SAME canonical set; none ships a
subset or a superset. An orchestrator whose backend does not yet realize an
operation MUST still ship that operation's skill (degrading gracefully at
invocation), never omit it — the canonical operations (a factory `drive`,
plan threads, grooming) are orchestrator-agnostic, not specific to any one
backend. This SUPERSEDES any prior per-orchestrator "reduced scope"
declaration that documented a partial skill surface. Because no single
repository sees more than one orchestrator, this cross-orchestrator
invariant is anchored by a **canonical orchestrator-skill manifest owned by
core**; each orchestrator repository verifies its shipped surface against
that core manifest.

**Description convention.** Every orchestrator skill's description — in both
the Claude `SKILL.md` frontmatter and the Codex skill definition — MUST lead
with its owning plugin name, so an operator's skill picker disambiguates
skills that share a name across orchestrators even when the runtime
truncates the shared `livespec-orchestrator-` prefix.

**Mechanically enforced.** This contract is mechanically checkable and MUST
be enforced fleet-wide: the canonical orchestrator-skill manifest lives in
core, and each orchestrator repository's enforcement suite verifies that
its shipped skill set equals the canonical set on BOTH runtimes and that the
description convention holds, so drift in any orchestrator is un-mergeable.
The check's own realization is enforcement-suite implementation detail; this
section owns the contract it enforces.
```

**Heading-coverage co-edit (applied by the accepting revise, per
`spec.md` §"Self-application").** This proposal adds ONE new `## ` heading to
`contracts.md` — `## Orchestrator skill-set contract — the canonical twelve`.
The revise pass that accepts this proposal MUST, in the SAME
`resulting_files[]` payload, add a matching entry to
`../tests/heading-coverage.json`:

```json
{
  "heading": "## Orchestrator skill-set contract — the canonical twelve",
  "spec_root": "SPECIFICATION",
  "spec_file": "contracts.md",
  "test": "TODO",
  "reason": "Landed by the orchestrator-skill-set-contract proposal (epic livespec-xfqd, slice P1): establishes the canonical twelve-skill orchestrator surface, cross-runtime identity, cross-orchestrator identity, and the description-leads-with-plugin convention as a mechanically-enforced core contract. The covering enforcement check is slice P2 (a core dev-tooling check verifying each orchestrator ships exactly the canonical set on both runtimes plus the description convention); this TODO is replaced with that check's test id when P2 lands."
}
```

No other spec file's `## ` heading set changes; only this one entry is
added. (This co-edit is NOT applied in the propose-change PR itself — a
heading-coverage entry for a heading not yet present in the live
`contracts.md` would orphan-fail the `check-heading-coverage` guard; it is
applied atomically by the accepting revise, which adds the heading and the
entry together.)
