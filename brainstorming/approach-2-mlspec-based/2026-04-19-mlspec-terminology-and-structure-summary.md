# MLSpec Terminology and Structure Summary

## Context

This note summarizes the discussion around adopting NLSpec-inspired structure for `livespec`, while correcting two issues that became clear during review:

1. The term `intent` was overloaded.
2. The framing `Intent -> NLSpec -> Implementation` did not fit the looped revision model we want.

The important clarification is that the old `SPECIFICATION/intent.md` was never meant to be "pre-spec". It was being used as the main body of the living specification, with `contracts.md`, `constraints.md`, and `scenarios.md` as companion files.

That naming created conceptual drag because a specification is itself a form of intent. It also made the file name carry too much meaning for both humans and LLMs.

## Final Model

The current model is:

- The specification is conceptually one logical living specification.
- It is represented on disk as multiple files for explicit LLM boundaries, lower nondeterminism, and specialized processing.
- `spec.md` is the primary source surface for the living specification.
- `contracts.md`, `constraints.md`, and `scenarios.md` are specialized operational partitions of the same specification.
- `scenarios.md` is intentionally split out both because it is more mechanically processable and because it should support holdout scenario usage in the StrongDM Dark Factory style.
- `intent` is freed up to refer to inputs feeding into specification revision: seeds, requests, critiques, observations, external requirements, implementation feedback, and other change pressure.

This yields a cleaner loop:

- intent inputs feed into revision of the spec
- the spec governs implementation
- implementation and observation generate new intent inputs

In that model, the specification is still a form of intent, but it is the current authoritative and ratified form of intent.

## Why `spec.md` Won

We considered alternatives such as `intent.md`, `behavior.md`, `foundation.md`, `core.md`, `main.md`, `general.md`, `source.md`, and `index.md`.

The key issue was not aesthetics but boundaries for LLM processing.

`contracts.md`, `constraints.md`, and `scenarios.md` are separated because they can be processed with lower ambiguity and stronger mechanical enforcement. The remaining main file therefore is not best understood as "behavior" or "architecture" or "goals". It is the default authoritative surface for all current spec content not factored into the specialized files.

Under that constraint:

- `intent.md` was broad, but semantically muddy for LLM routing.
- `core.md` and `main.md` were operationally clearer, but less semantically precise.
- `spec.md` was the clearest machine-facing name for the primary source surface, even though `SPECIFICATION/spec.md` is aesthetically redundant to human readers.

We concluded that the redundancy is acceptable because it improves explicit boundaries for LLMs.

## Why Not Collapse to a Single File

A single file would simplify the conceptual model, but it works against the main operational goals:

- weaker hard boundaries for LLM retrieval and editing
- more bleed between high-context prose and deterministic partitions
- noisier processing due to unrelated sections being pulled into context
- awkward handling of scenario holdouts for Dark Factory evaluation

So the right framing is:

- conceptually one spec
- operationally partitioned into multiple files

That is the cleanest way to preserve both spec unity and LLM-friendly boundaries.

## Key Terminology Distinction

The useful distinction is not:

- intent vs non-intent

It is:

- incoming or candidate intent
- committed or specified intent

So:

- `intent` refers to revision inputs
- `spec` refers to the current authoritative specification

This avoids pretending that the spec is not intent, while still preserving a useful lifecycle distinction.

## Relationship to NLSpec

NLSpec was useful prior art, especially in its emphasis on:

- strong boundaries between spec and implementation
- self-consistency
- explicit ambiguity management
- treating structure seriously

But we are intentionally diverging in two places:

1. We do not want the main living specification surface to be named `intent`.
2. We do not want the lifecycle described as a one-way `Intent -> NLSpec -> Implementation` chain.

The local copy of `nlspec-spec.md` explicitly states:

- "The relationship is directional and non-negotiable"
- `Intent -> NLSpec -> Implementation`

and later also acknowledges iteration and progressive discovery. That means the document already contains some tension between a clean authority chain and real iterative practice. Our revised terminology resolves that by reserving `intent` for incoming revision pressure and letting `spec` name the current source of truth.

## Prior Art and Research Notes

### NLSpec

- NLSpec spec: <https://github.com/TG-Techie/NLSpec-Spec/blob/main/nlspec-spec.md>
- Local copy reviewed in this folder: [nlspec-spec.md](/Users/cwoolley/workspace/livespec/brainstorming/approach-2-mlspec-based/nlspec-spec.md:15)

Relevant takeaway:

- useful as prior art for disciplined spec structure
- less suitable as-is for our terminology around `intent`

### Requirements Engineering Foundations

- Pamela Zave and Michael Jackson, "Four Dark Corners of Requirements Engineering": <https://www.pamelazave.com/4dc.pdf>
- Pamela Zave, "Foundations of Requirements Engineering": <https://www.pamelazave.com/fre.html>

Relevant takeaway:

- strong distinction between desired effects, domain knowledge, and specification
- useful for separating incoming change pressure from current authoritative specification

### Requirements vs Architecture Boundary Is Fuzzy

- Remco de Boer et al., "On the similarity between requirements and architecture": <https://www.sciencedirect.com/science/article/pii/S0164121208002574>

Relevant takeaway:

- the boundary between requirements and architecture is not clean
- both can be understood as optative statements
- this supports the observation that a specification is itself a form of intent

### Iterative Co-Development of Requirements and Architecture

- Bashar Nuseibeh, "Weaving the Software Development Process Between Requirements and Architectures": <https://cin.ufpe.br/~straw01/epapers/paper05/paper05.html>
- Twin Peaks summary: <https://www.microtool.de/en/knowledge-base/what-is-the-twin-peaks-model/>
- Background discussion referencing Twin Peaks: <https://www.sciencedirect.com/science/article/pii/S0164121208002574>

Relevant takeaway:

- requirements and architecture are often developed concurrently and iteratively
- this supports rejecting a strictly one-way framing for the overall process

### Multi-View Documentation

- ISO/IEC/IEEE 42010 conceptual model: <https://www.iso-architecture.org/ieee-1471/cm/>
- Kruchten 4+1 View Model: <https://www.researchgate.net/publication/220018231_The_41_View_Model_of_Architecture>
- arc42 overview: <https://arc42.org/overview>

Relevant takeaway:

- one conceptual description can be represented through multiple views
- that supports the model of one logical specification split into multiple files for different concerns and processing modes

### Living Documentation and Executable Specification

- Martin Fowler, "Specification By Example": <https://martinfowler.com/bliki/SpecificationByExample.html>
- Cucumber, "BDD is not test automation": <https://cucumber.io/blog/bdd/bdd-is-not-test-automation/>
- Cucumber, "BDD in the Finance Sector": <https://cucumber.io/blog/bdd/bdd-in-the-financial-sector/>
- Cucumber, "Isn't the business readable documentation just overhead?": <https://cucumber.io/blog/bdd/isn-t-the-business-readable-documentation-just-ove>

Relevant takeaway:

- discovery, formulation, automation, and living documentation are iterative
- scenarios are valuable as executable and reviewable specification artifacts
- this reinforces the decision to keep scenarios structurally separate

### Current AI Spec-Driven Tooling

- Augment Intent overview: <https://docs.augmentcode.com/intent/overview>
- Augment Intent product page: <https://www.augmentcode.com/product/intent>
- OpenSpec concepts: <https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md>
- OpenSpec getting started: <https://github.com/Fission-AI/OpenSpec/blob/main/docs/getting-started.md>
- spec-gen repository: <https://github.com/clay-good/spec-gen>

Relevant takeaway:

- modern AI tooling already treats the spec as a living source of truth
- OpenSpec is especially relevant for its explicit separation between current specs and proposed changes
- Intent is relevant as an example of a system where the spec stays aligned with implementation over time

## Proposed Terminology Going Forward

- `seed`: optional initial freeform input used to create the first spec
- `intent`: incoming revision inputs, including requests, critiques, observations, external requirements, and implementation feedback
- `spec`: the current authoritative living specification
- `contracts`: the mechanically stronger contract-oriented partition of the spec
- `constraints`: the mechanically stronger rule and invariant partition of the spec
- `scenarios`: the executable and evaluative scenario partition of the spec, including holdout scenarios
- `proposed_changes`: candidate revisions awaiting incorporation
- `history`: archived versions plus proposal acknowledgements and rationale

## Recommended README / Template Language

To reduce ambiguity for both humans and LLMs, the primary spec file should define its scope explicitly.

Suggested wording:

> `spec.md` is the primary source surface of the living specification. It contains all current authoritative specification content that is not captured in `contracts.md`, `constraints.md`, or `scenarios.md`. Those companion files are specialized operational partitions of the same specification, maintained separately to support clearer boundaries, stronger checking, and lower-nondeterminism processing by LLMs and tooling.
