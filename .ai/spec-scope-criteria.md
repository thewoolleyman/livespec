# What belongs in the spec, and what does not

**Read this BEFORE filing a `/livespec:propose-change`, before accepting a
`tier: spec-change` classification, and before holding a work-item for a spec
change.** Maintainer ruling 2026-11-16: not everything is a spec change; routing
every fix through the spec is one of the biggest bottlenecks in the factory, and
the spec must stop growing for things that are not contracts. Prefer code plus
tests, skills, and tools.

This is agent guidance, not a `SPECIFICATION/` clause. It changes how agents
route work; it does not change any contract.

## Bottom line

The spec (`SPECIFICATION/spec.md`, `contracts.md`, `scenarios.md`) and
`non-functional-requirements.md` hold only what another party can rely on:
a contract between components or repositories, a safety or security guarantee,
or a promise to users or operators. Everything else is code plus tests, or
guidance for agents (`AGENTS.md`, `.ai/<topic>.md`, skills, tools).

## What belongs where

| Home | Belongs there |
|---|---|
| `spec.md`, `contracts.md`, `scenarios.md` | (1) Contracts between components or repositories: wire shapes, schemas, CLI and exit-code surfaces, file layouts another repo reads or writes. (2) Safety or security guarantees. (3) Promises to users or operators: observable behaviour they may depend on. `scenarios.md` holds end-to-end behaviour of those promises. |
| `non-functional-requirements.md` | Constraints that bound how the whole system is built or run and that a consumer or operator relies on: supported runtimes and versions, required gates as a fleet-wide commitment, security and credential-handling constraints, performance or durability bounds a user may rely on. Not the mechanism that meets them. |
| Code plus tests | Internal mechanism, algorithms, retry and polling logic, bug fixes that restore already-stated behaviour, flake fixes, refactors, enforcement-check details. The test is the durable statement. |
| `.ai/<topic>.md`, `AGENTS.md`, skills, tools | Process rules, agent disciplines, workflows, runbooks, operator procedure, tool usage. |

## Decision procedure

Ask in order; the first YES decides.

1. **Does the change only restore behaviour the spec already states, or fix a defect with no change to any stated promise?** YES: code plus tests. No spec change.
2. **Is it only about how work is done (process, workflow, discipline, who does what, when)?** YES: `.ai/` guidance, a skill, or a tool. Not the spec.
3. **Is it only internal mechanism that no other repo, user, or operator can observe or depend on (a retry count, a poll loop, an enforcement-check detail, a screen heuristic)?** YES: code plus tests.
4. **Would another repo, user, or operator be broken or surprised if it changed (a schema key, a CLI surface, a file layout, an exit code, a documented behaviour)?** YES: spec (`contracts.md`, `spec.md`, or `scenarios.md` for end-to-end behaviour).
5. **Is it a guarantee about safety or security (credentials, isolation, destructive-operation limits)?** YES: spec or `non-functional-requirements.md`, whichever the guarantee is scoped to (system-wide constraint goes in non-functional-requirements).
6. **None of the above?** Default to code plus tests or `.ai/` guidance. If you still think the spec needs it, state in one sentence which party relies on it; if you cannot name one, it does not belong.

When a change has both a spec-worthy part and a mechanism part, split it: put only the contract part in the spec and the rest in code plus tests.

## Worked examples

| Item | Home | Why (question that decided it) |
|---|---|---|
| Flake fix: retry on shallow-fetch failure (`bd-ib-qawphe`) | Code plus tests | Q1/Q3: a flake fix restores intended behaviour; no one depends on the retry mechanism. |
| Host-only Definition-of-Ready screen (`bd-ib-ugel56`) | Code plus tests (and `.ai/` note if agents must know it) | Q3: a screening heuristic internal to one host's tooling; no cross-repo or user promise. |
| Merge-poll refreshing a BEHIND pull request (`bd-ib-us5l3f`) | Code plus tests | Q1/Q3: mechanism of the merge loop; the promise (PRs land through the queue) is already stated. |
| A new required key in a cross-repo schema | Spec (`contracts.md`), plus a cross-repo backfill epic | Q4: sibling repos read and write that schema; a required key breaks them if unannounced. |
| A credential-handling guarantee (secrets never written to `.beads/` or `.livespec.jsonc`) | Spec or `non-functional-requirements.md` | Q5: a security guarantee operators rely on. |
| The `/livespec:*` sub-command set and exit codes | Spec | Q4: users and Drivers depend on the surface. |
| A new `just check` enforcement script and its AST rules | Code plus tests | Q3: enforcement detail; the spec states only that the gate exists, if that. |
| "Use `mise exec -- git commit`; never `--no-verify`" | `AGENTS.md` / `.ai/` | Q2: process rule for agents. |
| Red-Green-Replay hook trailer handling details | Code plus tests, `AGENTS.md` | Q2/Q3: internal workflow mechanism. |
| End-to-end promise that a proposed change becomes a numbered history revision | `scenarios.md` | Q4: user-observable end-to-end behaviour. |
| A flaky-test policy or "don't poll background tasks" | `AGENTS.md` / user guidance | Q2: process discipline. |

## A `tier: spec-change` line is a record, not a hold

A ledger line of `tier: spec-change` records which tier a change was classified
into. It is NOT a hold, a gate, or a reason to stop. Do not park a work-item
waiting on it. If the classification is wrong under the procedure above
(for example a flake fix tagged `tier: spec-change`), reclassify it as code plus
tests and proceed; if it is right, file the proposed change and continue with
the parts that do not depend on it.

## Checks before filing a spec change anyway

- Name the party that relies on the clause (a repo, a user, an operator). No party, no clause.
- State the clause as a promise, not a mechanism; drop any sentence an existing check or test already enforces ("could this be deleted without losing the guardrail?").
- Prefer a test or tool that enforces it over prose that describes it.
- Then follow `.ai/spec-proposal-review.md` and the heading-coverage co-edit rule in `AGENTS.md`.
