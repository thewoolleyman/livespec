# Subdomains and Unsolved Routing

## Why This Note Exists

This note isolates one specific design question that came up while discussing a templated `SPECIFICATION` model for `livespec`:

- if a `SPECIFICATION` is partitioned into subdomains
- and one change spans multiple subdomains
- how does the system know which requirements, constraints, scenarios, or acknowledgements belong in which spec files?

This turns out to be a harder problem than simple directory layout. It is fundamentally about ownership, routing, and how a canonical `SPECIFICATION` should absorb cross-cutting concerns.

## The Problem

Subdomains sound simple when a change is local:

- frontend-only changes belong in the frontend portion of the `SPECIFICATION`
- backend-only changes belong in the backend portion of the `SPECIFICATION`

The difficulty appears when a change is cross-cutting:

- frontend and backend must coordinate through an API contract
- authentication affects UI, session handling, persistence, and operational constraints
- one new capability introduces requirements that cut across multiple existing areas

At that point, the core question is not just where files live. The real question is:

- which part of the `SPECIFICATION` owns which statement?

And the follow-up question is even harder:

- can that ownership be determined mechanically?

## What Current Public Systems Seem To Do

### OpenSpec

OpenSpec is the closest public precedent for a canonical spec plus in-flight change model.

What it clearly does:

- keeps canonical specs under `openspec/specs/...`
- keeps proposed work under `openspec/changes/...`
- supports a path-based merge model once the target canonical spec path is already known

What it does not clearly solve in public documentation:

- semantic routing of a cross-cutting change into the correct canonical spec files
- deterministic ownership of requirements that span multiple subdomains
- a mature answer for multi-file or multi-subdomain canonical spec structures that removes ambiguity up front

Historically, this limitation was one of the reasons `livespec` was explored in the first place: public OpenSpec usage strongly centered on a rigid format and path assumptions, even where the concept itself suggested more flexibility.

### Kiro

Kiro takes a different approach.

Its public model is primarily:

- one spec bundle per feature or bugfix
- `requirements.md` or `bugfix.md`
- `design.md`
- `tasks.md`

That means Kiro mostly avoids the canonical subdomain routing problem instead of solving it.

For a cross-cutting change, Kiro can keep one feature spec that talks about frontend, backend, and API work together. But that is not the same as maintaining one canonical `SPECIFICATION` partitioned into subdomains and routing the change back into those subdomains mechanically.

So Kiro is useful prior art for structured work packets, but not for canonical subdomain ownership.

### Attractor and Related Factory Work

The public Attractor materials are useful prior art for level-5 implementation and validation, but they do not present a solved subdomain-management model either.

What they show publicly:

- a small set of manually layered canonical NLSpec files
- explicit dependencies between some of those specifications
- workflow routing inside the implementation engine
- external holdout scenarios for factory validation

What they do not publicly show:

- a general system for mechanically assigning cross-cutting requirements to canonical subdomains
- a general-purpose ownership model for one large `SPECIFICATION` split into many interacting subdomains

Community projects around Attractor show similar patterns:

- explicit decomposition
- layered specs
- workflow graphs
- runtime routing across graph nodes or model providers

But not a documented general solution to semantic routing across subdomains in a canonical `SPECIFICATION`.

## What "Routing" Means Here

This note is specifically about **specification routing**, not workflow routing.

Workflow routing means things like:

- which node runs next in a pipeline
- which model handles a node
- which branch is selected at runtime

That is a different problem.

The unsolved problem here is:

- given one high-level change
- how do you decide which exact spec files inside a canonical `SPECIFICATION` should be updated?

And then:

- how do you do that consistently for cross-cutting concerns?

## Why This Remains Unsolved

There are several reasons this is hard:

- ownership boundaries are often fuzzy
- requirements and architecture are not cleanly separable
- API contracts often sit between domains rather than inside only one of them
- different teams want different partitioning strategies
- implementation structure and specification structure do not always align
- a mechanically "correct" routing choice may still be conceptually wrong

In other words, this is not just a file-layout problem. It is a modeling problem.

## Livespec Position

For `livespec`, this is an acknowledged but intentionally unaddressed concern in v1.

`livespec` does **not** claim to solve:

- subdomain ownership inside a canonical `SPECIFICATION`
- semantic routing of cross-cutting changes into the correct subdomains
- a universal decomposition strategy for all projects

This is a deliberate non-goal for now.

The current AI tooling ecosystem does not yet show a clear public consensus or mature precedent for this problem, especially at higher-autonomy or factory-style levels. Pretending this is solved would weaken the proposal.

## What Livespec Does Say Instead

`livespec` standardizes governance and lifecycle concerns around a `SPECIFICATION`, such as:

- how specs are seeded
- how changes are proposed
- how revisions are acknowledged
- how history is recorded
- how validation is performed

But it leaves structure to the chosen template.

That means:

- one project may use a single `spec.md`
- another may split into `spec.md`, `contracts.md`, `constraints.md`, and `scenarios.md`
- another may choose an OpenSpec-like layout
- another may define its own subdomain-oriented structure

In all of those cases, the exact shape of the `SPECIFICATION` is determined by:

- the template
- the prompt conventions
- the implementation step that consumes the spec

Not by `livespec` itself.

## Practical Consequence

If a team wants subdomains, it can adopt them through its template and prompts.

If a team wants a monolithic `SPECIFICATION`, it can do that too.

If a team wants to experiment with subdomain ownership rules, it can do so without requiring `livespec` core to pretend that the problem is already solved.

That flexibility is a strength:

- `livespec` is not locked to one hardcoded directory shape
- `livespec` is not locked to one historical format
- `livespec` does not force a premature answer to an open problem

## Current Conclusion

Subdomains may eventually matter a lot for mature `SPECIFICATION` management.

But today, based on the public systems reviewed so far, there is not yet a clear, widely adopted, mechanically reliable answer for:

- how a canonical `SPECIFICATION` should partition subdomains
- how cross-cutting changes should be routed across those subdomains

So `livespec` should explicitly acknowledge that this remains open and leave it out of scope for now.

## References

- OpenSpec: <https://github.com/Fission-AI/OpenSpec>
- OpenSpec Concepts: <https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md>
- OpenSpec Getting Started: <https://github.com/Fission-AI/OpenSpec/blob/main/docs/getting-started.md>
- Kiro Specs: <https://kiro.dev/docs/specs/>
- Kiro Best Practices: <https://kiro.dev/docs/specs/best-practices/>
- Kiro Multi-root Workspaces: <https://kiro.dev/docs/editor/multi-root-workspaces/>
- StrongDM Attractor: <https://github.com/strongdm/attractor>
- StrongDM Factory: <https://factory.strongdm.ai/>
- AttractorBench: <https://github.com/strongdm/attractorbench>
- Fabro: <https://github.com/fabro-sh/fabro>
- Kilroy: <https://github.com/danshapiro/kilroy>
- Forge: <https://github.com/smartcomputer-ai/forge>
- Attractor Software Factory: <https://github.com/az9713/attractor-software-factory>
