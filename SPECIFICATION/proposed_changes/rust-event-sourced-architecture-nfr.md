---
topic: rust-event-sourced-architecture-nfr
author: codex-gpt-5
created_at: 2026-06-22T02:18:00Z
---

## Proposal: Add Rust, ROP, DDD, and event-bus architecture NFRs for the event-sourced implementation line

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/constraints.md
- SPECIFICATION/scenarios.md

### Summary

The livespec family needs an explicit architecture-quality contract for the future event-sourced implementation line: Rust as the implementation language, railway-oriented programming (ROP) as the error-composition discipline, domain-driven design (DDD) as the module and boundary model, and an event-bus decision record for live-updating web behavior, eventual consistency, roll-forward, and rollback.

This proposal does NOT rewrite livespec core's shipped plugin scripts from Python to Rust. Core's current pure-Python runtime constraint remains valid for the existing core plugin surface. The new rules apply to the Rust event-sourced implementation line and to any repo that opts into that line by declaring itself as the Rust event-sourced implementation or web-app implementation in its own specification.

### Motivation

Livespec's Python implementation already treats quality gates, ROP discipline, strict typing, coverage, property tests, mutation tests, import-boundary checks, and red-green TDD replay as load-bearing architecture. The Rust event-sourced implementation line should have an equivalently explicit quality bar rather than relying on good taste or review memory.

The event-sourced direction also raises architecture questions that are easier to answer while the spec is still malleable:

- How do we keep domain logic independent from web, persistence, and transport frameworks?
- How do we prevent `Result` values and domain failures from being bypassed by panics, unchecked unwraps, or ad hoc exception-like control flow?
- How do we mechanically enforce module boundaries, dependency direction, and high cohesion?
- What event bus should carry domain events and projection updates when the product becomes a live-updating web app?
- How do roll-forward and rollback interact with immutable events, correction events, projections, and user-visible consistency?

The architecture-testing references the user supplied point to a practical enforcement style: architecture rules are tests, run in the normal test suite and CI, that check dependency direction, cycles, naming, file size, cohesion/coupling metrics, and custom project-specific constraints. Rust should adopt the same idea with Rust-native tooling and custom static checks where needed.

### Proposed Changes

#### Edit 1 — `SPECIFICATION/non-functional-requirements.md`, under `## Spec`, add `### Rust event-sourced implementation discipline`

Add a new subsection after `### Orchestrator plugin ecosystem`:

```markdown
### Rust event-sourced implementation discipline

The Rust event-sourced implementation line MUST use Rust for production code. Shell, SQL, TypeScript, generated bindings, and infrastructure files MAY exist at the edges, but the domain model, command handling, event model, projection logic, and application orchestration MUST be Rust unless a later proposal carves out a narrower exception.

The implementation MUST use railway-oriented programming as its normal control-flow and error-composition discipline:

- expected failures MUST flow through typed `Result<T, E>` values;
- command handlers, projectors, event-store adapters, and HTTP/RPC handlers MUST compose `Result` pipelines with `?`, `map`, `and_then`, `map_err`, explicit conversion traits, or equivalent railway combinators;
- domain and application errors MUST be typed enums with stable variants, not stringly typed errors;
- `panic!`, `unwrap`, `expect`, indexing that may panic, and unchecked conversion shortcuts MUST be forbidden in production code except in a narrow allowlist for impossible-state assertions that are mechanically audited;
- adapters MAY translate framework errors into typed application errors at the boundary, but domain code MUST NOT depend on framework error types.

The implementation MUST embrace domain-driven design boundaries:

- domain modules own aggregates, value objects, commands, events, invariants, and domain services;
- application modules own use-case orchestration and transaction/event-store coordination;
- infrastructure modules own persistence, event-store clients, web frameworks, external APIs, and background-runtime integration;
- presentation/API modules own HTTP, websocket, UI, CLI, or agent-facing transport concerns;
- dependency direction MUST point inward: presentation and infrastructure may depend on application/domain interfaces, but domain MUST NOT depend on presentation, infrastructure, persistence frameworks, web frameworks, or concrete event-bus clients.

The event-sourced model MUST treat events as the canonical history. Roll-forward is the default correction mechanism: errors in accepted history are corrected by appending compensating or replacement events with causal metadata, not by editing prior events. Rollback is a projection/user-experience operation unless an explicit administrative event-stream repair procedure is specified; any physical event-store rewrite MUST be exceptional, audited, and unavailable to normal product workflows.
```

#### Edit 2 — `SPECIFICATION/non-functional-requirements.md`, under `### Testing approach`, add Rust quality-gate clauses

Add the following after the existing mutation-testing clause:

```markdown
#### Rust quality gates for the event-sourced implementation line

Rust implementation repos in the event-sourced line MUST make their `just check` aggregate at least as strict as livespec core's Python gate. The aggregate MUST include:

- `cargo fmt --check`;
- `cargo clippy --all-targets --all-features -- -D warnings` plus project-specific denied lints for panic-prone APIs and ignored results;
- the full test suite, preferably via `cargo nextest` when available;
- documentation tests;
- coverage measurement with a ratcheting threshold and per-crate reporting;
- property-based tests for pure domain logic and event/projector invariants;
- fuzz targets for parsers, event deserialization, command validation, and other untrusted-input boundaries;
- mutation testing or an explicit mutation-testing substitute with a documented threshold and baseline;
- dependency and supply-chain audit checks;
- architecture tests that mechanically enforce module boundaries, dependency direction, cycle absence, naming conventions, file/module size limits, and cohesion/coupling thresholds.

Architecture tests MUST be first-class tests in the normal CI path, inspired by the ArchUnitTS and ArchUnitPython pattern: the architecture diagram is not trusted unless executable tests assert that code still follows it. When off-the-shelf Rust tooling cannot express a required rule, the repo MUST provide a custom static check using Rust syntax/metadata tooling rather than relying only on review.
```

#### Edit 3 — `SPECIFICATION/non-functional-requirements.md`, under `### Test-Driven Development discipline`, add Rust red-green replay parity

Add the following clause:

```markdown
Rust event-sourced implementation repos MUST enforce the same red-green commit discipline as the livespec Python repos. A `feat:` or `fix:` changeset MUST carry proof that a focused Red test failed before the implementation was staged, then passed after the Green amend. The commit-refuse hook MAY be implemented differently for Rust, but it MUST preserve the same semantics: Red stages the test-only delta, Green amends the implementation without changing the Red test bytes, and the final commit records machine-checkable Red and Green trailers. Documentation-only, config-only, and behavior-preserving refactor commits keep the same exemption categories as livespec core unless the repo's own spec narrows them.
```

#### Edit 4 — `SPECIFICATION/constraints.md`, add a Rust architecture constraint under `## Constraint scope`

Add a clause that separates existing Python-core constraints from Rust event-sourced constraints:

```markdown
The pure-Python runtime/dependency constraints below bind livespec core's shipped plugin scripts. They do NOT prohibit a separate Rust event-sourced implementation line. Any Rust implementation line MUST specify its own runtime, crate, and binary distribution constraints in its own spec or in a scoped subsection here before it becomes part of the livespec family contract.
```

#### Edit 5 — `SPECIFICATION/constraints.md`, add `## Event-sourced architecture constraints`

Add a new H2 section:

```markdown
## Event-sourced architecture constraints

For the Rust event-sourced implementation line, the event store is the source of truth. Projections, read models, caches, search indexes, websocket session state, and UI state are derived and rebuildable.

Domain events MUST be append-only, versioned, and schema-evolvable. Each event MUST carry enough metadata to support causality, audit, idempotent handling, projection rebuilds, and user-visible history. Command handling MUST validate invariants before appending events and MUST return typed railway failures for expected rejections.

The event bus is an explicit architecture decision and MUST NOT be hidden behind ad hoc direct calls. Until a concrete bus is selected, implementations MUST depend on an internal event-bus port/interface owned by the application layer. Candidate adapters MAY include in-process channels for a single-node MVP, Postgres-backed notification/outbox patterns, NATS, Redis Streams, Kafka/Redpanda, or another durable broker, but each candidate MUST be evaluated against:

- local development simplicity;
- ordering guarantees needed by aggregate streams and projections;
- at-least-once delivery and idempotency requirements;
- websocket/live-update fanout behavior;
- replay and projection rebuild ergonomics;
- offline/partition behavior and eventual-consistency semantics;
- operational burden for small deployments;
- migration path from in-process MVP to durable distributed bus;
- compatibility with roll-forward correction events and audited administrative repair.

Live-updating web behavior MUST be projection-driven. The UI MAY optimistically reflect edits, but server confirmation MUST reconcile against committed events and projection versions. Rollback in the UI MUST be modeled as either optimistic-state cancellation before commit or as a new compensating event after commit; the architecture MUST NOT require mutating historical events for ordinary undo.
```

This edit adds a new `##` heading. The corresponding revise payload MUST add a `TODO` entry for `SPECIFICATION/constraints.md` heading `## Event-sourced architecture constraints` in `tests/heading-coverage.json`.

#### Edit 6 — `SPECIFICATION/scenarios.md`, add event-sourced behavior scenarios

Add a new H2 scenario:

```markdown
## Scenario: Live edit is committed through the event stream and projected to clients

Given a user submits an edit to a live spec-backed web interface
When the application accepts the command
Then it appends one or more versioned domain events to the event store
And the read model is updated by projection from those events
And subscribed clients receive the projected update rather than a direct mutable-state patch
And the command result is returned through a typed railway success value.
```

Add a second H2 scenario:

```markdown
## Scenario: Accepted edit is undone by roll-forward correction

Given an accepted edit has already been committed to the event store
When the user requests undo or an operator corrects the accepted edit
Then the system appends a compensating or replacement event with causal metadata
And projections converge to the corrected state
And historical events remain auditable
And the command result is returned through a typed railway success or typed railway failure.
```

These edits add two new `##` headings. The corresponding revise payload MUST add `TODO` entries for both scenario headings in `tests/heading-coverage.json`, and each TODO reason MUST acknowledge the scenario-tier coverage requirement.

### Event-bus decision framing

The event bus should remain a decision record until the implementation proves its shape. Initial guidance:

- **MVP default:** use an internal application-layer event-bus port plus an in-process adapter or database outbox adapter. This keeps the domain/application boundary stable while avoiding premature operational complexity.
- **Durable distributed candidate:** evaluate NATS JetStream, Redis Streams, and Postgres outbox/listen-notify first. Kafka/Redpanda remains plausible for high-throughput multi-consumer workloads but is likely too heavy for the first self-hostable implementation.
- **Invariant:** command acceptance and event persistence are the transaction boundary; websocket delivery is downstream and eventually consistent.
- **Rollback posture:** prefer roll-forward correction events. Reserve physical event rewrite for audited administrative repair only.

### Acceptance Criteria

- The spec explicitly scopes Rust to the event-sourced implementation line and does not contradict the existing pure-Python core plugin constraint.
- The spec requires ROP with typed `Result`-based expected failures and mechanically forbids silent bypasses such as unchecked unwrap/expect/panic paths in production code.
- The spec requires DDD boundaries and inward dependency direction.
- The spec requires Rust quality gates covering formatting, linting, tests, doctests, coverage, property tests, fuzzing, mutation testing or substitute, dependency audit, and architecture tests.
- The spec requires red-green replay commit discipline for Rust `feat:` / `fix:` commits with the same semantics as the livespec Python repos.
- The spec records the event bus as an explicit architecture decision with evaluation criteria and a port/adapter boundary before any concrete broker choice.
- The revise payload updates `tests/heading-coverage.json` for each new `##` heading.
