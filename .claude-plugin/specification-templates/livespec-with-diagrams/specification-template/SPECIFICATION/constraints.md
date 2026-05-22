# `<intent-derived-title>` — constraints

This file enumerates the architecture-level constraints the
project MUST satisfy. Constraints are stable invariants — when
a constraint changes, every downstream rule depending on it is
re-evaluated through the propose-change loop.

## Runtime

The runtime environment the project requires (language version,
operating-system family, etc.). Populated at seed time from the
user's intent + initial scaffolding.

## Dependencies

Upstream libraries or services the project depends on. Each
dependency MUST be vendored, pinned, or declared with a
documented version range; the choice depends on the project's
ergonomics constraints.

## Tooling

Developer-time tooling constraints (test runner, linter,
type-checker) that gate per-commit checks. The list lives here
so the project's `just check` (or equivalent) aggregate can be
re-derived from this constraint set without reverse-engineering.
