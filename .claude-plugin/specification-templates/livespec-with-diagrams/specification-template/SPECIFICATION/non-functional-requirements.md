# `<intent-derived-title>` — non-functional requirements

This document MUST be read alongside `spec.md`, `contracts.md`,
`constraints.md`, and `scenarios.md`. It enumerates the
project's non-functional requirements: invariants on the
development environment, repository tooling, build and test
discipline, contributor workflow, and any other internal-facing
concerns that are NOT visible at the user-facing CLI/API
surface. The five top-level `##` sections below mirror the same
four-file boundary the user-facing spec uses (`Spec` /
`Contracts` / `Constraints` / `Scenarios`) plus a `Boundary`
preamble, so contributors and agents apply the same
categorization rule when landing non-functional content.

## Boundary

`non-functional-requirements.md` covers concerns of the form
"how the project is built, tested, and maintained". The
top-level sections below mirror the user-facing spec files; the
decision rule for each section:

- `## Spec` — process *intent and behavior*: what testing means
  in this project, what the project's development discipline is,
  what "done" means for a contributor change. Mirrors `spec.md`'s
  role.
- `## Contracts` — *contributor-facing external interfaces and
  toolchain*: the tools the project depends on, the command that
  runs the project's checks, and any test/coverage data-file
  shapes. Mirrors `contracts.md`'s role.
- `## Constraints` — *architectural invariants on the
  implementation*: code patterns, layout rules, thresholds, and
  style rules that bind only contributors. Mirrors
  `constraints.md`'s role.
- `## Scenarios` — *Gherkin-style scenarios for
  contributor-facing workflows*. Mirrors `scenarios.md`'s role.
  Empty initially; populated when a specific contributor flow
  needs to be captured.

The boundary against the user-facing spec files:

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
live here.

## Spec

This section's sub-sections enumerate the project's
contributor-facing process intent and behavior — the analogue
of `spec.md`'s role for the user-facing surface.

### Development discipline

The project's testing approach, commit discipline, and review
process. Populated at seed time from the user's intent and any
inherited project conventions.

### Tooling and enforcement

Linter, formatter, type-checker, code-coverage targets, and
complexity thresholds. The single command that runs the full
set of checks MUST be derivable from this section.

### Hooks and CI

Pre-commit, pre-push, and CI hook configuration. Local hooks
and CI gates SHOULD chain consistently and SHOULD NOT bypass
each other.

### Contributor workflow

Repo-local task tracking, dev-environment setup, contributor
onboarding, and agent-facing operating instructions.

## Contracts

This section's sub-sections enumerate the project's
contributor-facing external interfaces and toolchain — the
analogue of `contracts.md`'s role for the user-facing surface.
Example placeholder content:

### Contributor toolchain

The tools a contributor installs to build, test, and check the
project (language runtime, build and test tooling, hook
manager). Document how each tool's version is selected and
recorded so a fresh checkout reproduces the same checks. End
users install only the shipped runtime, NOT this contributor
toolchain.

### Check-aggregate command

The single command a contributor runs to execute every check.
Document its sub-steps and the data-file shapes any check
produces or consumes (coverage reports, test manifests).

## Constraints

This section's sub-sections enumerate the architectural
invariants on the project's implementation — the analogue of
`constraints.md`'s role for the user-facing surface, but bound
to contributor-facing concerns. Example placeholder content:

### Build-and-check layout

The single-source-of-truth rule for build and check invocation
(e.g., one canonical entry point owns every check; hooks and CI
delegate to it rather than invoking the underlying tools
directly). Populated at seed time from the project's tooling
conventions.

### Code patterns and thresholds

Style rules, structural-boundary invariants, and numeric
thresholds (coverage floor, complexity ceiling) that bind
contributors but are not observable at the user-facing surface.

## Scenarios

Contributor-facing Gherkin scenarios — the analogue of
`scenarios.md`'s role for the user-facing surface. Each
Gherkin keyword line is preceded and followed by a blank line
so that every step renders as its own Markdown paragraph under
GitHub-Flavored Markdown. Fenced code blocks are not used to
hold Gherkin steps. Empty initially; populated when a specific
contributor flow needs to be captured.

### Scenario: `<placeholder-contributor-scenario-name>`

Given a placeholder contributor precondition

When a placeholder contributor action is taken

Then a placeholder contributor outcome is observed
