# Livespec workflow diagrams

This document captures the livespec lifecycle as a set of PlantUML
diagrams, progressively drilling down from a single-page overview
into per-layer detail and the spec-vs-implementation routing
question.

## How these diagrams render

The diagram sources are individual `.plantuml` files under
[`diagrams/`](./diagrams/). The images embedded below are
rendered on demand by the public PlantUML proxy at
`www.plantuml.com/plantuml/proxy`, which fetches the raw
`.plantuml` source from this repository and returns a rendered
SVG. This is the established pattern for embedding PlantUML in
GitHub-flavored Markdown (which does not natively support the
PlantUML code-fence the way it supports Mermaid).

GitLab users: GitLab natively renders PlantUML code fences, so
each `.plantuml` file's content can also be pasted into a
GitLab markdown file as a `\`\`\`plantuml` block if needed.

If the proxy is unavailable or rendering breaks for a specific
diagram, see [`diagrams/`](./diagrams/) — every source is
versioned in the repo and can be rendered locally with
`plantuml <name>.plantuml`.

## Inspiration

The structure (high-level overview → progressively more
detailed sub-flows) follows the original NLSpec lifecycle
diagrams under
[`archive/brainstorming/approach-2-nlspec-based/`](../../archive/brainstorming/approach-2-nlspec-based/),
specifically `2026-04-19-nlspec-lifecycle-{diagram,diagram-detailed,legend}.md`.
Those archive diagrams are Mermaid; these are PlantUML and have
been extended to capture the implementation layer (built during
the bootstrap session at PR #42–#46) and the observation-flow
routing (the spec-vs-implementation question discussed in
[`spec-vs-implementation-line.md`](./spec-vs-implementation-line.md)).

The archive diagrams may not match the current state exactly;
where they diverge, these diagrams reflect current intent and
the archive is the historical reference.

## Legend

The symbol vocabulary used across all subsequent diagrams. Plain
rectangles for external inputs, cards (slightly-rounded
rectangles) for slash commands, dashed rectangles for actions /
observations, ovals for decisions, cylinders for stored
artifacts, stick figures for users / agents.

(PlantUML deployment-diagram syntax doesn't have a native diamond
shape outside the activity-diagram context; ovals are the closest
equivalent. The original archive Mermaid diagrams used diamonds
for decisions; these PlantUML diagrams use ovals to convey the
same "branch point" meaning.)

![Legend](https://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/thewoolleyman/livespec/master/research/workflow-processes/diagrams/legend.plantuml)

[Source: `diagrams/legend.plantuml`](./diagrams/legend.plantuml)

## High-level lifecycle

The single-page overview. An initial seed of intent populates
`SPECIFICATION/`. The spec drives implementation. Observations
return from the implementation layer (or from the spec itself,
or from observed behavior). Each observation is routed by a
single decision — *does this introduce or change a requirement?*
— either back into the spec lifecycle (left branch) or directly
into the implementation layer (right branch).

The detail of each branch lives in subsequent diagrams.

![High-level lifecycle](https://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/thewoolleyman/livespec/master/research/workflow-processes/diagrams/high-level-lifecycle.plantuml)

[Source: `diagrams/high-level-lifecycle.plantuml`](./diagrams/high-level-lifecycle.plantuml)

## Spec lifecycle (detailed)

The full spec-mutation flow:
[`/livespec:seed`](#) populates the initial `SPECIFICATION/` and
writes the `v001` history snapshot. From then on, the imperative
window is closed: any further mutation flows through
[`/livespec:propose-change`](#) →
[`/livespec:revise`](#) (selective per-proposal). Observations of
spec / implementation / behavior may be routed through
[`/livespec:critique`](#) for LLM-driven analysis before becoming
proposed changes.

[`/livespec:doctor`](#) splits into a static phase
(deterministic findings, expressible as inline diff and routed
straight to `propose-change`) and an LLM-driven phase
(non-deterministic findings, routed via `critique` to formulate
a fix). Doctor is invoked pre/post by every other command and is
also runnable on demand.

[`/livespec:prune-history`](#) collapses old `vNNN/` snapshots
into a pruned-marker once they're no longer load-bearing for
audit.

![Spec lifecycle](https://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/thewoolleyman/livespec/master/research/workflow-processes/diagrams/spec-lifecycle.plantuml)

[Source: `diagrams/spec-lifecycle.plantuml`](./diagrams/spec-lifecycle.plantuml)

## Implementation lifecycle (detailed)

The repo-local `livespec-implementation` layer that drives the
gap → bead → implement loop:

- [`/livespec-implementation:refresh-gaps`](#) reads the spec
  and the repo, writes
  `implementation-gaps/current.json`. Read-only with respect to
  `SPECIFICATION/`.
- `just implementation::check-gaps` validates the report against
  its schema.
- [`/livespec-implementation:plan`](#) surfaces every untracked
  gap to the user; with explicit per-issue consent, `bd create`
  files one beads issue per gap (label
  `gap-id:gap-NNNN`).
- `just implementation::check-gap-tracking` enforces the 1:1
  invariant: every current `gap.id` has exactly one beads issue
  across all statuses.
- [`/livespec-implementation:implement`](#) pulls a leaf-level
  issue from `bd ready`, drives a Red→Green code cycle (red =
  test only, green = impl that turns the test green), then
  re-runs `refresh-gaps` to verify the gap-id is gone from
  `current.json` before closing the beads issue with
  `--resolution fix` and the required audit fields.

Non-fix closures (wontfix / spec-revised / duplicate /
no-longer-applicable) take a separate path that does not require
the refresh-gaps verification step.

![Implementation lifecycle](https://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/thewoolleyman/livespec/master/research/workflow-processes/diagrams/implementation-lifecycle.plantuml)

[Source: `diagrams/implementation-lifecycle.plantuml`](./diagrams/implementation-lifecycle.plantuml)

## Observation flow — spec-vs-implementation routing

The diagram that captures the heart of the late-bootstrap
discussion: where exactly is the line between spec content
and implementation-only intent, and what's the workflow for
each?

Every observation — whether from a contributor noticing
something during work, an agent surfacing it during a
`refresh-gaps` walk, a failing test, a runtime drift, or
accumulated workarounds — is routed by a single decision:
**does this introduce or change a project requirement?**

The diagnostic for that decision is: *if the change landed and
you re-ran `refresh-gaps`, would `current.json` change?*

- **YES** — the change is realising or violating a requirement.
  It's spec-content, and follows Path A:
  `/livespec:propose-change` → `/livespec:revise` →
  `SPECIFICATION/` updated → next `refresh-gaps` run derives
  the corresponding gap → `plan` files a gap-tied beads issue
  (with `gap-id:` label). Closure requires the refresh-gaps
  verification step.
- **NO** — the change is implementation-only intent (a refactor,
  a helper extraction, a cleanup). It's not spec-content, and
  follows Path B: a freeform `bd create` (with explicit user
  consent) files an issue without any `gap-id:` label.
  Closure is freeform; no refresh-gaps verification required.

Both paths land in the same beads queue and are worked through
the same `/livespec-implementation:implement` skill. The
divergence is in *how the issue gets there* and *what closure
requires*.

![Observation flow](https://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/thewoolleyman/livespec/master/research/workflow-processes/diagrams/observation-flow.plantuml)

[Source: `diagrams/observation-flow.plantuml`](./diagrams/observation-flow.plantuml)

## Open questions deliberately not encoded in these diagrams

The diagrams reflect the workflow as currently understood and as
spec'd in `SPECIFICATION/non-functional-requirements.md` (v058 +
v059). A handful of refinements are still open and live in
[`spec-vs-implementation-line.md`](./spec-vs-implementation-line.md):

- Should freeform beads issues use a label namespace (e.g.
  `obs:`, `improvement:`, `tech-debt:`) to distinguish them
  from "untriaged"? Or is the absence of a `gap-id:` label
  sufficient signal?
- Should the implement skill's closure rules formally branch on
  label, or is "if `gap-id` present, run verification; else
  don't" the implicit rule everyone already knows?
- For non-actionable observations (notes that aren't yet work
  items): do they need a home, or do contributors trust their
  own judgement on bd-deferred / code-comment / drop?
- Some implementation changes look mechanical but are actually
  requirement-changes in disguise (e.g. "every subprocess call
  MUST have a timeout"). The line is the architecture-vs-
  mechanism distinction the spec already enforces; a heuristic
  in the spec for borderline cases would help.

These will be answered (or explicitly left as judgement calls)
when the next round of `/livespec:propose-change` activity
addresses them; the diagrams will be updated then.
