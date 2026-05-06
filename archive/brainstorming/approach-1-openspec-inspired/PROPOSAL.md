# Livespec: Living Specification Development

## What is Livespec?

A set of Claude Code skills and directory conventions for spec-anchored development. No CLI, no install, no dependencies. Specs are markdown files that serve as the primary human artifact. The tool is the skills that know how to read, write, and evolve them.

## Core Concept

Specs are living documents that describe what the system does. Amendments are bounded units of work that evolve specs and implement the changes. An amendment stays open until specs and code converge — not when a checklist is done, but when the system does what the specs say.

## Why This Exists

OpenSpec pioneered the separation between canonical specs and bounded changes, but its implementation has critical flaws:

- Single maintainer, inactive since February 2026. 316 open issues, 58 unreviewed PRs.
- Sync skill hardcodes `spec.md` — completely broken for multi-file spec structures despite the schema supporting them.
- Key schema issues (#666, #827, #829, #796, #770) have zero maintainer engagement.
- CLI-centric architecture adds unnecessary dependency, version drift, and a lossy translation layer between the tool and the AI.
- Linear pipeline workflow (create artifacts → implement → archive) doesn't model how development actually works.
- No alternative tools in the landscape have OpenSpec's changes-as-deltas-against-canonical-specs concept.

Livespec takes the best idea from OpenSpec (specs + bounded amendments) and rebuilds it correctly: as a skill pack with no CLI, proper multi-file support, and a convergence loop instead of a linear pipeline.

## Directory Structure

```
specs/                                  # canonical — the living truth
  <capability>/
    intent.md                           # what this capability does and why
    contracts.md                        # inputs, outputs, behaviors, APIs
    constraints.md                      # limits, invariants, non-functional requirements
    scenarios.md                        # concrete examples that prove it works

amendments/                             # bounded work in progress
  <name>/
    proposal.md                         # why are we changing the specs?
    specs/                              # updated spec files (sparse — only what's changing)
      <capability>/
        contracts.md                    # full file, changes applied
    plan.md                             # implementation approach and decisions
    tasks.md                            # checklist derived from plan
    journal.md                          # log of observations, problems, revisions

livespec.yaml                           # project config
```

## Artifacts

- **proposal.md** — The motivation. Why are these specs changing? What's the goal? What's in scope? The only artifact that captures intent at the amendment level.
- **specs/** — Updated spec files. Full copies of only the files being modified. Not diffs — complete files with changes applied. On close, these overwrite canonical versions.
- **plan.md** — Implementation decisions and rationale. Which files change, what approach, why this approach over alternatives. The bridge from "what the specs say" to "what to code."
- **tasks.md** — A checklist derived from the plan. Mutable — tasks get added, removed, and rewritten as implementation reveals reality.
- **journal.md** — A running log of observations during implementation. When you hit a problem, the observation goes here before anything gets revised. Makes the "observe" step explicit.

## Workflow

Not a pipeline. A convergence loop with four modes:

```
        draft
       ↗     ↘
  revise  ←  implement
       ↖     ↙
        observe
```

- **Draft** — Creating or updating artifacts. Each builds on the previous ones.
- **Implement** — Writing code. Working through tasks, making changes, running tests.
- **Observe** — Something's wrong. Log the observation, decide what to revise.
- **Revise** — Updating artifacts based on observations. Revisions cascade — if specs change, plan and tasks may need updating.

The amendment is done when you've gone around the loop enough times that everything converges.

## Skills

| Skill | Mode | What it does |
|---|---|---|
| `livespec:new-amendment` | Draft | Create amendment directory, write proposal from user's description |
| `livespec:continue` | Draft | Generate the next artifact, or regenerate a stale one after revisions |
| `livespec:propose` | Draft | Generate all artifacts at once from a description |
| `livespec:apply` | Implement | Work through tasks, writing code. Pause on problems |
| `livespec:observe` | Observe | Log an observation in the journal. Assess impact on specs/plan/tasks |
| `livespec:revise` | Revise | Update artifacts based on observations. Cascade changes downstream |
| `livespec:status` | Any | Show amendment state, progress, recent journal entries |
| `livespec:close` | — | Sync specs to canonical, mark amendment done |
| `livespec:verify` | — | Check implementation matches specs before closing |
| `livespec:explore` | Any | Thinking partner, not tied to a specific amendment |
| `livespec:onboard` | — | Guided walkthrough of a full cycle |

Plus `livespec-doctor` as a standalone validation script for CI.

## Configuration (livespec.yaml)

```yaml
spec_structure:
  - intent.md
  - contracts.md
  - constraints.md
  - scenarios.md

artifact_sequence:
  - proposal
  - specs
  - plan
  - tasks

# Maturity dial — scales from interactive to factory
scenarios:
  location: specs              # or "holdout" for factory-level hidden scenarios
  holdout: false

verify:
  mode: review                 # or "scenarios" for automated holdout validation

apply:
  mode: interactive            # or "factory" for attractor pipeline
```

## Factory Compatibility

The same artifacts, directory structure, and conventions work at factory level. What changes:

| Concern | Level 3-4 (Interactive) | Factory |
|---|---|---|
| Who implements | Human + skill | Attractor agents |
| Who validates | Human + tests | Holdout scenarios |
| Where scenarios live | `specs/` (visible) | `holdout/` (hidden) |
| What drives the loop | Human observation | Automated drift detection |
| When to stop | Human says "good enough" | Satisfaction threshold met |

`livespec.yaml` is the maturity dial. Start interactive, turn up as you add automation.

## What This Gets Right

1. Multi-file specs that actually work — sync walks the directory, not a hardcoded filename
2. Convergence loop, not linear pipeline — observe/revise skills close the feedback loop
3. Journal — observations are captured, not lost in chat history
4. Scenarios alongside specs — acceptance criteria live with the capability they describe
5. No install — copy the skills directory and you're running
6. Plan, not design — clear name for what it actually is
7. Sparse amendment specs — only changed files, copied on close
8. Factory-ready — same structure scales from interactive to fully automated
