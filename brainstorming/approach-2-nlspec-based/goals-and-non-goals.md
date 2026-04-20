# Goals and Non-Goals

## Why This Document Exists

This document makes the scope of `livespec` explicit.

It captures:

- what `livespec` is trying to solve
- what it is intentionally not trying to solve
- where current public tools are strong
- where current public tools still leave important gaps

The goal is to keep the proposal honest and sharply scoped.

## Core Thesis

`livespec` is about **governance and lifecycle for a living `SPECIFICATION`**.

It is not primarily:

- a spec authoring format
- an implementation engine
- a workflow runner
- a general solution to every hard problem in factory-scale software generation

The central idea is:

- a project has a living `SPECIFICATION`
- changes to that `SPECIFICATION` are proposed, revised, acknowledged, validated, and versioned
- the exact on-disk shape of that `SPECIFICATION` is template-defined rather than hardcoded by `livespec`

## Goals

### 1. Make the `SPECIFICATION` the primary human artifact

`livespec` should support a project model where the `SPECIFICATION` is the maintained source of truth for intended system behavior.

This includes:

- initial seeding of a `SPECIFICATION`
- revising the `SPECIFICATION` over time
- keeping history of revisions
- treating implementation feedback as input to revision rather than as an informal chat artifact

### 2. Separate lifecycle from on-disk format

This is one of the main intended strengths of `livespec`.

`livespec` should define:

- how specifications are seeded
- how changes are proposed
- how revisions are acknowledged
- how validation and drift checks happen
- how history is recorded

But it should **not** hardcode one required file layout.

The file layout should come from a template.

That means a project should be able to choose:

- a single-file `SPECIFICATION`
- a split `SPECIFICATION` such as `spec.md`, `contracts.md`, `constraints.md`, `scenarios.md`
- an OpenSpec-compatible layout
- another custom structure defined by the team's own template

### 3. Support templated `SPECIFICATION` structures

The proposal already assumes that templates exist and that they define the structure of the `SPECIFICATION`.

That implies:

- `.livespec.jsonc` must specify the active template
- `livespec` should support more than one built-in template
- one built-in alternate template should support the default OpenSpec structure

This is important because it allows compatibility with familiar structures without forcing teams to adopt OpenSpec's full lifecycle model or naming conventions.

### 4. Be repo-native and tool-light

`livespec` should be a repository convention plus prompts/skills, not a CLI-first system with a mandatory tool-owned root and hardcoded workflow assumptions.

This is a direct response to pain points seen in OpenSpec:

- rigid directory assumptions
- tight coupling between workflow and file shape
- CLI mediation between the user, the AI, and the spec files

### 5. Support a disciplined natural-language `SPECIFICATION`

The current proposal already points toward a more disciplined spec language.

That includes:

- BCP 14 / RFC 2119 + RFC 8174 requirement language such as `MUST`, `SHOULD`, and `MAY`
- fenced `gherkin` blocks for scenario-style examples and acceptance criteria

This is meant to improve clarity and reduce ambiguity in a natural-language `SPECIFICATION`.

### 6. Preserve flexibility in how projects partition the `SPECIFICATION`

`livespec` should not force one answer to the question of how teams split their `SPECIFICATION`.

Some projects may want:

- a monolithic `SPECIFICATION`
- a split spec with operational partitions
- a domain- or subdomain-oriented structure

The governing principle is that `livespec` manages lifecycle and governance, while the template and implementation step define structure.

### 7. Stay compatible with stronger implementation stacks

`livespec` is not trying to replace factory-style implementation engines such as Attractor.

Instead, it should leave room for a `SPECIFICATION` to be consumed by:

- interactive AI workflows
- more deterministic implementation loops
- higher-autonomy factory-style execution systems

The implementation step is downstream of `livespec`.

## What Existing Tools Already Do Well

### OpenSpec

OpenSpec is the clearest public precedent for:

- canonical specs plus in-flight changes
- bounded change folders
- proposal/design/tasks workflow
- path-based syncing once target spec files are already known

It remains important prior art.

### Kiro

Kiro is strong at:

- structured feature- and bugfix-scoped spec packets
- breaking work into requirements, design, and tasks
- helping one work item move from planning to execution

It is useful prior art for execution-oriented spec workflows.

### Attractor and related factory work

Attractor and adjacent factory work are strong at:

- the implementation step
- workflow execution
- graph-based orchestration
- factory-style validation with holdout scenarios

They are highly relevant for downstream implementation and evaluation.

## What `livespec` Wants To Solve Better Than Existing Tools

### 1. Decouple governance from format

This is the most important differentiator.

Existing tools tend to tie together:

- spec lifecycle
- directory structure
- artifact names
- workflow assumptions

`livespec` should separate those concerns.

### 2. Allow OpenSpec-compatible structure without OpenSpec lock-in

OpenSpec has valuable ideas and existing ecosystem recognition.

`livespec` should let teams keep a familiar OpenSpec-style structure if they want it, while still using a different governance model.

### 3. Treat the `SPECIFICATION` as a living, revisable artifact rather than just a work packet

Kiro is strong for work-item specs, but it does not publicly present the same kind of canonical, evolving `SPECIFICATION` model that this proposal is aiming for.

`livespec` should center the long-lived `SPECIFICATION`, not just the current feature packet.

### 4. Make revision and acknowledgement first-class

The proposal is explicitly concerned with:

- change proposals
- revisions
- acknowledgements
- historical record

This is a stronger governance framing than just "generate requirements/design/tasks and go build."

### 5. Avoid pretending that one on-disk decomposition is universally correct

This is especially important given the current state of the ecosystem.

There is no clear public consensus yet on the one correct way to partition a canonical `SPECIFICATION` for AI-native development across all project types.

`livespec` should not hardcode a premature answer.

## Non-Goals

### 1. Solving subdomain ownership inside a `SPECIFICATION`

For now, `livespec` does not claim to solve:

- how subdomains should be defined
- which part of the `SPECIFICATION` owns a cross-cutting statement
- how shared interfaces should be assigned across subdomains

This problem appears to remain open in the public ecosystem.

### 2. Solving semantic routing of cross-cutting changes

This is one of the clearest explicit non-goals.

If one change affects frontend, backend, API, auth, and constraints at the same time, `livespec` v1 does not claim to determine mechanically:

- which exact spec files should be updated
- which statements belong in which subdomain
- how those changes should be distributed across a complex canonical `SPECIFICATION`

This is left to the chosen template, prompt conventions, and implementation discipline.

### 3. Defining one universal decomposition strategy

`livespec` is not trying to standardize:

- one mandatory spec partitioning scheme
- one required directory structure
- one required subdomain model
- one universally correct way to map system structure into spec structure

### 4. Replacing implementation engines

`livespec` is not trying to be:

- Attractor
- a workflow runtime
- a graph executor
- a software factory by itself

Those systems solve different downstream problems.

### 5. Designing the full template mechanism right now

The proposal now assumes:

- templates exist
- the config names the active template
- at least one alternate OpenSpec-compatible template is provided

But it does **not** yet define:

- how templates are represented
- how templates are loaded
- whether templates are file-based, prompt-based, script-based, or hybrid

That is intentionally deferred.

### 6. Claiming that current public tools have already solved the hard parts

`livespec` should not claim that the ecosystem already knows how to solve:

- canonical subdomain routing
- cross-cutting spec ownership
- universally correct multi-file semantic partitioning

The public evidence reviewed so far suggests otherwise.

## Why These Non-Goals Are Rational

These are not non-goals because they are unimportant.

They are non-goals because:

- the public ecosystem does not yet show a mature consensus
- existing tools either avoid the problem, centralize it manually, or leave it implicit
- pretending it is solved would make the proposal weaker and less credible

This is especially true for higher-autonomy or factory-style workflows, where mistakes in ownership and routing become more dangerous rather than less.

## Current Ecosystem Assessment

Based on the public systems reviewed so far:

- OpenSpec partially solves path-based syncing after target files are chosen, but does not clearly solve semantic routing across subdomains
- Kiro mostly avoids the problem by working with feature-scoped spec packets rather than a deeply partitioned canonical `SPECIFICATION`
- Attractor and related factory work are focused on implementation/runtime orchestration and validation, not general-purpose `SPECIFICATION` governance
- public community implementations show decomposition and workflow routing, but not a mature documented solution for cross-cutting canonical spec routing

So the honest conclusion is:

- there is useful prior art
- there is no clear public finished answer to the hardest subdomain questions

## Practical Scope For `livespec` v1

`livespec` v1 should therefore focus on:

- living `SPECIFICATION` governance
- templated structure
- revision and acknowledgement flow
- validation and history
- compatibility with different downstream implementation styles

And it should explicitly leave out:

- universal subdomain ownership rules
- mechanical cross-cutting routing
- one mandated canonical shape for every project

## References

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/prior-art.md`
- `brainstorming/approach-2-nlspec-based/subdomains-and-unsolved-routing.md`
- OpenSpec: <https://github.com/Fission-AI/OpenSpec>
- Kiro Specs: <https://kiro.dev/docs/specs/>
- Kiro Best Practices: <https://kiro.dev/docs/specs/best-practices/>
- StrongDM Attractor: <https://github.com/strongdm/attractor>
- StrongDM Factory: <https://factory.strongdm.ai/>
