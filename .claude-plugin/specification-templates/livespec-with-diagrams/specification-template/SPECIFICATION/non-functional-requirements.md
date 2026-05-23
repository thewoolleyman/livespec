# `<intent-derived-title>` — non-functional requirements

This file enumerates the project's non-functional requirements:
invariants on the development environment, repository tooling,
build and test discipline, contributor workflow, and any other
internal-facing concerns that are NOT visible at the user-facing
CLI/API surface.

## Boundary

`non-functional-requirements.md` covers concerns of the form
"how the project is built, tested, and maintained". The
boundary against the other spec files:

- User-facing intent or behavior MUST stay in `spec.md`.
- User-facing wire contracts MUST stay in `contracts.md`.
- Constraints whose violation an end user could observe MUST
  stay in `constraints.md` (runtime versions, exit-code
  contracts, dependency envelopes, structured-logging
  schemas).
- User-facing scenarios MUST stay in `scenarios.md`.

The trickiest boundary is `constraints.md` ↔
`non-functional-requirements.md`: constraints whose violation
an end user could observe MUST stay in `constraints.md`;
constraints that bind only the project's contributors MUST
move here.

## Development discipline

Test-Driven Development practices, commit discipline, and
review process. Populated at seed time from the user's intent
and any inherited project conventions.

## Tooling and enforcement

Linter, formatter, type-checker, code-coverage targets, and
complexity thresholds. The enforcement aggregate (e.g.,
`just check`) MUST be derivable from this section.

## Hooks and CI

Pre-commit, pre-push, and CI hook configuration. Local hooks
and CI gates SHOULD chain consistently and SHOULD NOT bypass
each other.

## Contributor workflow

Repo-local task tracking, dev-environment tool pinning,
contributor onboarding, and agent-facing operating
instructions.
