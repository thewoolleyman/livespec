---
topic: orchestrator-skill-set-contract
author: claude-opus-4-8
created_at: 2026-07-08T10:11:34Z
---

## Proposal: Canonical orchestrator skill-set contract — twelve skills, identical across runtimes and across orchestrators

### Target specification files

- contracts.md
- spec.md
- non-functional-requirements.md

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
standalone-installable per `non-functional-requirements.md` §"Spec" (the
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

**Drift-sweep co-amendments (applied atomically by the same accepting
revise).** The new §"Orchestrator skill-set contract — the canonical twelve"
makes core's contract SEE the orchestrator skill surface (the operator seam)
alongside the three orchestrator CLIs (the machine seam). Several live
statements in `spec.md`, `non-functional-requirements.md`, and `contracts.md`
currently assert the OPPOSITE — that core sees ONLY / EXACTLY the three CLIs,
that the orchestrator skills are INTERNAL / invisible to core, or that the
grooming and Planning-Lane patterns introduce "NO new core skill". Left
unamended, the ratified spec would be self-contradictory. The accepting revise
MUST therefore apply the following prose- and diagram-label co-amendments in the
SAME `resulting_files[]` payload as the `contracts.md` new section above. Every
one is prose- or diagram-label-only: NONE adds, removes, or renames a `## `
heading, so the single heading-coverage co-edit below stays complete and
correct.

Each amendment is a verbatim replace: locate the quoted **From** text
(character-exact — em dashes and backticks included) in the named live file and
replace it with the **To** text.

_`spec.md` — Site A (§"Terminology", the **Orchestrator** entry):_

From:

```
Core's contract sees only its three config-named CLIs; everything else about it (store, prompts, internal state) is private.
```

To:

```
Core's contract sees its three config-named CLIs (the machine seam) plus its operator skill surface per `contracts.md` §"Orchestrator skill-set contract — the canonical twelve"; everything else about it (store, prompts, internal state) is private.
```

_`spec.md` — Site B (§"Contract + reference implementations architecture", the "Orchestrator internal decomposition" paragraph):_

From:

```
core's contract sees exactly the three orchestrator CLIs of `contracts.md` §"Orchestrator CLI contract — the three named CLIs" and never names Ledger/Loop/Dispatcher in any config key or invariant.
```

To:

```
core's contract sees exactly the three orchestrator CLIs of `contracts.md` §"Orchestrator CLI contract — the three named CLIs" plus the canonical skill surface of §"Orchestrator skill-set contract — the canonical twelve", and never names Ledger/Loop/Dispatcher in any config key or invariant.
```

_`spec.md` — Site C (the canonical architecture diagram in §"Contract + reference implementations architecture"): move the `oskills` node OUT of the `internals` subgraph — which is labeled "INTERNAL (invisible to core AND Driver)" — into the `orch` (orchestrator-plane) subgraph as a peer of the visible `rdr` / `gap` / `drift` CLI nodes, and relabel it to cite the contract instead of an unmarked six. `dispatcher` / `ledger` / `loop` stay inside `internals`. The node's existing edges (`console --> oskills`, `oskills -.-> gap`, `oskills -.-> drift`, `oskills -->|plan: writes| planstore`) reference it by id and stay valid unchanged. Apply as this single block replace:_

From:

```
        rdr["spec-reader CLI"]
        gap["gap-capture CLI"]
        drift["drift-capture CLI"]
        subgraph internals["INTERNAL (invisible to core AND Driver)"]
            dispatcher["Dispatcher: owns parallelism"]
            ledger[("Ledger: work-items + deps")]
            loop["Loop: per-work-item producer"]
            oskills["orchestrator skills: plan, groom, capture-work-item, capture-impl-gaps, capture-spec-drift, implement"]
        end
```

To:

```
        rdr["spec-reader CLI"]
        gap["gap-capture CLI"]
        drift["drift-capture CLI"]
        oskills["orchestrator skills: the canonical twelve<br/>(contracts.md §Orchestrator skill-set contract)"]
        subgraph internals["INTERNAL (invisible to core AND Driver)"]
            dispatcher["Dispatcher: owns parallelism"]
            ledger[("Ledger: work-items + deps")]
            loop["Loop: per-work-item producer"]
        end
```

_`spec.md` — Site E-1 (the planes diagram in §"Workflow planes and the Planning Lane", the `orchskills` node): mark the enumerated six as an explicit subset of the canonical twelve (an unmarked subset is the only thing the different-zoom convention forbids):_

From:

```
orchskills["orchestrator skills: plan, groom, capture-work-item,<br/>capture-impl-gaps, capture-spec-drift, implement"]
```

To:

```
orchskills["orchestrator skills (subset of the canonical twelve): plan, groom, capture-work-item,<br/>capture-impl-gaps, capture-spec-drift, implement"]
```

_`spec.md` — Site E-2 (the Planning-Lane diagram in §"Workflow planes and the Planning Lane", the `op` subgraph label enumerating eight): mark it as an explicit subset of the canonical twelve:_

From:

```
op["ORCHESTRATOR-PLANE skills: reference beads-fabro"]
```

To:

```
op["ORCHESTRATOR-PLANE skills (subset of the canonical twelve): reference beads-fabro"]
```

(The canonical diagram's own former unmarked-six label at the `oskills` node is
already reconciled by Site C, which relabels it to "the canonical twelve"; no
separate Site E amendment is needed there.)

_`non-functional-requirements.md` — Site D-1 (§"Orchestrator plugin ecosystem"):_

From:

```
Cross-boundary conformance is the orchestrator CLI contract published by `livespec` (`contracts.md` §"Orchestrator CLI contract — the three named CLIs"): the orchestrator owns its work-item machinery, and core's contract sees only the three named CLIs.
```

To:

```
Cross-boundary conformance comprises TWO published surfaces — the orchestrator CLI contract (`contracts.md` §"Orchestrator CLI contract — the three named CLIs" — the machine seam) AND the orchestrator skill-set contract (`contracts.md` §"Orchestrator skill-set contract — the canonical twelve" — the operator surface): the orchestrator owns its work-item machinery, and core's contract sees those two published surfaces.
```

_`non-functional-requirements.md` — Site D-2 (§"Orchestrator contract delegation"):_

From:

```
`livespec` publishes only the orchestrator CLI contract (`contracts.md` §"Orchestrator CLI contract — the three named CLIs"): the orchestrator owns its work-item machinery, and core's contract sees only the three named CLIs.
```

To:

```
`livespec` publishes two orchestrator-facing cross-boundary contracts — the orchestrator CLI contract (`contracts.md` §"Orchestrator CLI contract — the three named CLIs" — the machine seam) AND the orchestrator skill-set contract (`contracts.md` §"Orchestrator skill-set contract — the canonical twelve" — the operator surface): the orchestrator owns its work-item machinery, and core's contract sees those two published surfaces.
```

_`contracts.md` — borderline reconciliation (§"Orchestrator CLI contract — the three named CLIs", opening sentence): scope "cross-boundary contract" to the machine seam now that the skill-set contract is a second cross-boundary surface:_

From:

```
The cross-boundary contract is a CLI surface wired by `.livespec.jsonc`:
```

To:

```
The machine cross-boundary contract is a CLI surface wired by `.livespec.jsonc`:
```

_`non-functional-requirements.md` — borderline reconciliation, §"Orchestrator-internal grooming guidance" (two sentences): the grooming pattern now NAMES `groom` (and `plan`) as canonical skills whose existence core requires, so the "core neither names nor verifies any of it" / "NO new core skill" phrasings must be scoped to the discipline's realization:_

From:

```
Like the Dispatcher guidance above, this is explicitly NON-normative on core's contract: core neither names nor verifies any of it.
```

To:

```
Like the Dispatcher guidance above, this grooming discipline is explicitly NON-normative on core's contract: core neither names nor verifies its realization or mechanics (core requires each canonical skill's existence by name per `contracts.md` §"Orchestrator skill-set contract — the canonical twelve"; its realization and discipline stay orchestrator-private).
```

From:

```
Core deliberately gets the GUIDANCE only. This pattern introduces NO new core skill, NO new core CLI, and NO new core doctor invariant.
```

To:

```
Core deliberately gets the GUIDANCE only. This pattern introduces no new core CLI or doctor invariant (core requires each canonical skill's existence by name per `contracts.md` §"Orchestrator skill-set contract — the canonical twelve"; its realization and discipline stay orchestrator-private).
```

_`non-functional-requirements.md` — borderline reconciliation, §"Planning Lane guidance" (two spans within the same paragraph): the Planning-Lane pattern now NAMES `plan` (and `list-plan-threads`) as canonical skills whose existence core requires, so the same two phrasings must be scoped:_

From:

```
Like the Dispatcher and grooming guidance above, this is explicitly NON-normative on core's contract: core neither names nor verifies any of it.
```

To:

```
Like the Dispatcher and grooming guidance above, this Planning-Lane discipline is explicitly NON-normative on core's contract: core neither names nor verifies its realization or mechanics (core requires each canonical skill's existence by name per `contracts.md` §"Orchestrator skill-set contract — the canonical twelve"; its realization and discipline stay orchestrator-private).
```

From (the `— an interactive, stateful `plan` front-end` tail is REQUIRED to
disambiguate this Planning-Lane span from the byte-identical opening clause of
the §"Control-Plane guidance" disclaimer, which is DELIBERATELY left unamended
per the scope note below — match ONLY this occurrence):

```
This pattern introduces NO new core skill, NO new core CLI, and NO new core doctor invariant; the concrete realization — an interactive, stateful `plan` front-end
```

To:

```
This pattern introduces no new core CLI or doctor invariant (core requires each canonical skill's existence by name per `contracts.md` §"Orchestrator skill-set contract — the canonical twelve"; its realization and discipline stay orchestrator-private); the concrete realization — an interactive, stateful `plan` front-end
```

**Scope note (drift-sweep completeness).** Three families of nearby "NON-normative
/ NO new core skill" statements are DELIBERATELY left unamended because P1 does
not contradict them: (a) `non-functional-requirements.md` §"Orchestrator-internal
Dispatcher guidance" ("core neither names nor verifies any of it") — its "it" is
the loop discipline (mode / budget / janitor / journal), which P1 does not name;
(b) the §"Control-Plane guidance" disclaimer — about the `livespec-console-*`
console, not an orchestrator plugin, so none of the canonical twelve applies; and
(c) the §"Conformance Pattern" / §"governed-repo lifecycle" / §"release-freshness"
"NO new core skill … on core's *functional* surface" statements — fleet
self-application infrastructure, not the orchestrator skill surface. Amending any
of these would broaden the change beyond the contradiction.

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

No other spec file's `## ` heading set changes — the drift-sweep
co-amendments above are all prose- and diagram-label-only and add, remove, or
rename NO heading — so only this one entry is added. (This co-edit is NOT
applied in the propose-change PR itself — a
heading-coverage entry for a heading not yet present in the live
`contracts.md` would orphan-fail the `check-heading-coverage` guard; it is
applied atomically by the accepting revise, which adds the heading and the
entry together.)
