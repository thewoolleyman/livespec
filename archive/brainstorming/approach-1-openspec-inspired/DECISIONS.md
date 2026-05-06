# Livespec: Decision Log

An exhaustive record of every discussion, decision, and rationale from the brainstorming sessions that led to the Livespec proposal.

---

## 1. Origin: Why Livespec Exists

### The OpenSpec Problem

OpenSpec is a spec-driven development tool that introduced a good core idea: separating canonical specs from bounded changes (deltas). However, critical implementation problems make it unsuitable for continued use:

**Sync is broken for multi-file specs.** The `openspec-sync-specs` skill hardcodes `spec.md` as the only supported filename (lines 30, 42, 48, 69 of the skill). The custom schema (`spec-driven-custom`) defines `generates: "specs/**/*.md"` and instructs multi-file creation (intent.md, contracts.md, constraints.md), but sync doesn't honor this. Any project using multi-file specs has broken sync.

**Maintainer is inactive.** Single maintainer (TabishB) last active February 27, 2026 — over 25 days of inactivity at time of analysis. 316 open issues, 58 open PRs with zero maintainer review. Key schema/sync issues (#666, #827, #829, #796, #770) have community investment but zero maintainer engagement. No active forks picking up the work.

**CLI-centric architecture is a liability.** OpenSpec requires a CLI (`openspec` command) that scaffolds files and prints instructions. The skills then call the CLI, parse JSON output, and act on it. This creates: a dependency to install/maintain, version drift between CLI and skills, and a lossy translation layer that strips context.

**Linear pipeline doesn't match reality.** OpenSpec treats development as: create artifacts → implement → archive. But implementation always reveals spec problems. There's no built-in way to loop back and revise.

### The Landscape

Research into alternatives (conducted March 2026) found no tool that replicates OpenSpec's core concept of changes-as-deltas-against-canonical-specs:

- **GitHub Spec Kit** (82K stars) — spec generation, no delta/amendment concept
- **BMAD Method** (42K stars) — business analysis framework, no living specs
- **GSD** (41K stars) — task decomposition, not spec-anchored
- **Taskmaster** (26K stars) — task management, no spec layer
- **OpenSpec** (34K stars) — has the right concept, broken implementation

**Decision:** Build from scratch rather than fork or contribute to OpenSpec. The maintainer situation makes contribution unproductive, and the architectural problems (CLI-centric, hardcoded sync) require a rewrite, not patches.

---

## 2. Naming

### Project Name: Livespec

**The core insight the name captures:** Specs are living documents. They evolve over time. They're not written once and forgotten — they're the canonical, maintained truth about what the system does.

Alternatives considered:
- Names focusing on the spec/change separation (too mechanical)
- Names focusing on the tool (it's not really a tool, it's conventions + skills)

**Decision:** "Livespec" — communicates the central philosophy that specifications are living, evolving documents.

### Terminology: Amendments Not Changes

OpenSpec uses "changes" as the unit of work. This term is:
- Generic and overloaded (git changes, code changes, requirement changes)
- Implies no lifecycle — a "change" is just a diff
- Doesn't communicate that it's bounded with a clear endpoint

**Decision:** Use "amendments" instead. An amendment:
- Has a clear lifecycle: open → in progress → applied → closed
- Implies modification of an existing document (which is exactly what it does to specs)
- Is bounded — it has a start and an end, unlike "changes" which could be ongoing
- Borrows from legal/constitutional language where amendments modify living documents

### Terminology: Plan Not Design

The artifact between specs and tasks was originally called "design" (carried over from OpenSpec). This is misleading — "design" implies UX/visual design to many people.

**What this artifact actually is:** Given what the specs now say, what's the implementation approach? Which files change, what new modules to create, technical decisions and rationale.

**Decision:** Call it "plan" — it's an implementation plan. Clear, unambiguous, describes exactly what it is.

### Terminology: Close Not Archive

OpenSpec "archives" completed changes. But archiving implies filing something away for reference. What actually happens is: the amendment's specs overwrite the canonical specs, and the amendment is done.

**Decision:** Use "close" — the amendment is applied and closed. The spec changes become canonical. The amendment record may be kept or removed, but the action is closing, not archiving.

---

## 3. Architecture: No CLI

### The CLI is Unnecessary

OpenSpec's CLI (`openspec new change`, `openspec status`, `openspec instructions`, etc.) does three things:
1. Scaffolds directories and files
2. Reads state and reports status
3. Provides instructions for skills to follow

All three of these things can be done directly by skills reading and writing files. The CLI is a middleman that:
- Adds a dependency to install and maintain
- Creates version drift between CLI and skills
- Serializes context to JSON and back, losing nuance
- Requires PATH configuration and environment setup

**Decision:** No CLI. Livespec is:
1. A directory convention (`specs/`, `amendments/`, `livespec.yaml`)
2. A set of Claude Code skills that know how to read/write that convention
3. Command wrappers (`.claude/commands/`) for discoverability (since skills don't autocomplete in Claude plugins)
4. A standalone validation script (`livespec-doctor`) for CI

### Command Wrappers for Discoverability

Skills in Claude Code don't autocomplete. Commands do. So each skill gets a thin command wrapper that invokes it:

```
.claude/
  skills/
    livespec-new-amendment/SKILL.md
    livespec-continue/SKILL.md
    ...
  commands/
    livespec/
      new-amendment.md          # → invokes livespec:new-amendment skill
      continue.md               # → invokes livespec:continue skill
      ...
```

This gives users `/livespec:new-amendment` autocomplete in the CLI.

### livespec-doctor: The Only Executable

The single standalone script handles CI/CD validation. It's a linter for spec structure, not a CLI framework. It checks:
- Every capability has at least `intent.md`
- No orphaned amendments (open with no activity)
- Amendment specs reference capabilities that exist
- Closed amendments have no unchecked tasks
- Spec files conform to expected structure

**Decision against a "validate" skill:** If you have the doctor script, a separate validate skill is redundant. Doctor handles structural validation. The `livespec:verify` skill handles semantic verification (does implementation match specs), which is a different concern.

---

## 4. Directory Structure

### Specs at Repo Root

OpenSpec buries specs under `openspec/specs/`. This makes specs subordinate to the tool.

**Decision:** `specs/` lives at the repo root. The tool serves the specs, not the other way around. Anyone can navigate to `specs/` and understand the system without knowing about Livespec.

### Multi-File Spec Structure

Each capability gets its own directory with up to four files:

```
specs/<capability>/
  intent.md           # what and why
  contracts.md        # inputs, outputs, behaviors, APIs
  constraints.md      # limits, invariants, non-functional requirements
  scenarios.md        # concrete examples that prove it works
```

This comes from the Software Factory Practitioner's Guide (Section 3) which defines the spec layer as intent, contracts, and constraints. Scenarios are added from Section 4 (holdout validation concept, adapted for level 3-4 as visible acceptance criteria).

**Decision:** Configurable via `livespec.yaml` — teams that prefer a single `spec.md` per capability can configure that. The default is the four-file structure.

### Sparse Amendment Specs

An amendment's `specs/` directory only contains the capabilities and files being changed. Not a full mirror of all canonical specs.

```
amendments/add-oauth/
  specs/
    auth/
      contracts.md    # full updated file, not a diff
```

**Decision:** Amendment spec files are full copies with changes applied, not diffs or patches. This means you can read them standalone and they make sense. On close, they simply overwrite the canonical version. Sync is a file copy — no merge logic, no conflict resolution.

### Journal: A New Artifact

Not present in OpenSpec. The journal (`journal.md`) is a running log of observations made during implementation.

**Why it exists:** The observe → amend → rebuild → validate loop requires an "observe" step. Without the journal, observations are made in chat, which is ephemeral. The journal makes observations persistent and reviewable.

**What goes in it:**
- Problems encountered during implementation
- Spec gaps discovered
- Decisions to revise artifacts and why
- Timestamps and context

**Decision:** Journal is a first-class artifact. The `livespec:observe` skill writes to it.

---

## 5. Workflow: Convergence Loop Not Pipeline

### The Problem with Linear Pipelines

OpenSpec's workflow is: `new change → continue → continue → continue → apply → archive`. This is a straight line. But real development is iterative:

- You implement task 4 and discover the contract didn't account for refresh tokens
- You implement task 2 and realize the plan's approach won't work
- You finish all tasks and tests fail because a constraint was wrong

OpenSpec has no skills for going back. You manually edit files and hope for the best.

### The Convergence Loop

Livespec models development as a loop with four modes:

```
        draft
       ↗     ↘
  revise  ←  implement
       ↖     ↙
        observe
```

**Draft** — Creating or updating artifacts (proposal, specs, plan, tasks). Each builds on previous ones. This is the initial forward pass.

**Implement** — Writing code. Working through the task list.

**Observe** — Something's wrong. A test fails, a requirement was misunderstood, a constraint was missed. Log it in the journal.

**Revise** — Update artifacts based on observations. If specs change, plan and tasks may need cascading updates.

The amendment closes when specs and code converge — everything is consistent, tests pass, implementation matches specs.

### Skills as Modes, Not Phases

Skills map to modes, not pipeline stages:

- `livespec:continue` works in draft mode and is re-runnable. "Specs changed, regenerate tasks."
- `livespec:apply` works in implement mode and is resumable. Picks up unchecked tasks.
- `livespec:observe` works in observe mode. Logs findings, assesses impact.
- `livespec:revise` works in revise mode. Updates artifacts, cascades changes.

You move between modes fluidly. There's no enforced sequence after the initial draft pass.

### Three Types of Problems (from the Software Factory Guide)

The guide identifies three signal types that trigger the loop:

1. **Behavioral drift** — Code doesn't match the spec. Mechanical fix: update the code.
2. **Spec gaps** — Spec didn't cover a situation. Requires human judgment to extend specs.
3. **Satisfaction regression** — Spec is wrong. The behavior it describes isn't what's needed. Hardest — requires rethinking.

All three feed into the observe → revise cycle. At level 3-4, humans drive this. At factory level, automated detection triggers it.

---

## 6. Skill Decisions

### Skills Eliminated

**`openspec-sync-specs` → eliminated.** Sync is merged into close. There's no reason to sync specs separately from closing the amendment. The only reason OpenSpec separates them is because sync is broken and people work around it manually.

**`openspec-ff-change` (fast-forward) → eliminated.** FF generates all remaining artifacts at once. But `livespec:propose` already does this — describe what you want, get everything generated. FF is the awkward middle ground between stepping through (`continue`) and generating everything (`propose`). Two options cover the spectrum; three is redundant.

**`openspec-bulk-archive-change` → eliminated.** Bulk operations add complexity for a rare use case. Close amendments one at a time.

### Skills Added

**`livespec:observe` — new.** Makes the "observe" step in the convergence loop explicit. Logs observations to the journal and assesses impact on existing artifacts.

**`livespec:revise` — new.** Handles artifact updates after observations. Cascades changes — if specs are revised, plan and tasks may need regeneration.

**`livespec:status` — replaces CLI.** In OpenSpec, status comes from `openspec status` CLI command. In Livespec, it's a skill that reads amendment state directly.

### Skills Retained (with refinements)

**`livespec:new-amendment`** (was `openspec-new-change`) — Creates amendment directory, writes proposal. Name reflects "amendment" terminology.

**`livespec:continue`** (was `openspec-continue-change`) — Generates next artifact OR regenerates a stale one after revisions. Not just forward — can re-draft.

**`livespec:propose`** (was `openspec-propose`) — One-shot: description in, all artifacts out. Subsumes FF.

**`livespec:apply`** (was `openspec-apply-change`) — Implements tasks. Pauses on problems (which feeds into observe/revise).

**`livespec:verify`** (was `openspec-verify-change`) — Checks implementation matches specs before closing. Distinct from doctor (structural) — this is semantic.

**`livespec:close`** (was `openspec-archive-change`) — Syncs amendment specs to canonical AND marks done. One action, not two.

**`livespec:explore`** (was `openspec-explore`) — Thinking partner. Not tied to a specific amendment.

**`livespec:onboard`** (was `openspec-onboard`) — Guided walkthrough.

---

## 7. Factory Compatibility

### The Maturity Dial

Livespec is designed for level 3-4 (spec-anchored, human-in-the-loop) but the same structure works at factory level. The differences are in execution, not artifacts.

**What stays the same across levels:**
- Directory structure (specs/, amendments/, livespec.yaml)
- Artifacts (proposal, specs, plan, tasks, journal)
- The convergence loop concept

**What changes:**

| Concern | Level 3-4 | Factory |
|---|---|---|
| Who implements | Human + skill | Attractor agents |
| Who validates | Human + tests | Holdout scenarios |
| Where scenarios live | `specs/` (visible) | `holdout/` (hidden) |
| What drives the loop | Human observation | Automated drift detection |
| When to stop | Human says "good enough" | Satisfaction threshold met |

### Configuration via livespec.yaml

```yaml
# Level 3-4 defaults
scenarios:
  location: specs
  holdout: false

verify:
  mode: review

apply:
  mode: interactive

# Factory overrides
# scenarios:
#   location: holdout
#   holdout: true
# verify:
#   mode: scenarios
#   satisfaction_threshold: 0.95
# apply:
#   mode: factory
#   attractor: attractor.dot
```

When `holdout: true`, a `holdout/` directory appears at repo root with scenarios hidden from implementation agents. The `livespec:apply` skill respects this boundary — it never reads holdout scenarios.

**Decision:** Build for level 3-4 now. Factory support is a configuration change, not an architecture change. The structure is ready; the automation comes later.

---

## 8. What Livespec Does NOT Do (By Design)

- **No holdout scenarios at launch** — scenarios.md is visible to all agents. Hidden holdout is a factory concern.
- **No attractor graph** — no automated re-generation pipeline. Humans drive the loop.
- **No automated drift detection** — you observe drift yourself. Tooling for that comes later.
- **No CLI** — skills are the interface. Doctor is the only executable.
- **No merge logic** — amendment specs are full file copies. Close is a file overwrite, not a merge.
- **No schema/workflow engine** — the artifact sequence is a convention, not enforced by a state machine. Skills are smart enough to figure out what comes next by reading the directory.

---

## 9. Conceptual Foundations

### The Software Factory Practitioner's Guide

Livespec draws heavily from the Software Factory Practitioner's Guide (by the project author). Key concepts adopted:

**Spec structure (Section 3):** Intent, contracts, constraints as the three pillars of a capability specification. Livespec adds scenarios as a fourth file.

**The amendment workflow (Section 8):** Observe → amend → rebuild → validate as the heartbeat of an evolving system. Livespec's convergence loop is a direct implementation of this for level 3-4.

**Three signal types (Section 6):** Behavioral drift, spec gaps, satisfaction regression. These inform how the observe/revise skills assess problems.

**Maturity progression:** Spec-first → spec-anchored → spec-as-source. Livespec targets spec-anchored with a path to spec-as-source.

**Separation of concerns:** The guide describes three agent sets (spec-refinement, factory execution, validation) that never see each other's artifacts. Livespec's factory mode respects this with holdout separation.

### What Livespec Adds Beyond the Guide

**The journal artifact** — The guide describes the observe step but doesn't specify where observations are recorded. Livespec makes this explicit.

**Skills as the interface** — The guide is tool-agnostic. Livespec implements the concepts as Claude Code skills with no other dependencies.

**Sparse amendment specs** — The guide discusses spec versioning but doesn't prescribe how deltas work. Livespec's approach (full file copies of only changed files, overwrite on close) is a specific implementation choice.

**The convergence loop as a skill workflow** — The guide describes the loop conceptually. Livespec maps it to concrete skills (observe, revise, continue, apply) that users invoke.

---

## 10. Open Questions

These were not resolved during brainstorming and need further discussion:

1. **Journal format** — What structure should journal entries follow? Timestamps? Categories? Free-form?
2. **Amendment lifecycle states** — Should amendments have explicit states (draft, implementing, revising, verifying) tracked somewhere? Or is the state implicit from what files exist?
3. **Multiple amendments** — Can multiple amendments be open simultaneously? What happens when two amendments modify the same capability's specs?
4. **Doctor implementation** — Shell script? Node? Deno? What's the right tech for a standalone validation script?
5. **Onboarding content** — What does the guided walkthrough actually teach? What's the example project?
6. **Explore scope** — Is explore tied to amendments at all, or purely freeform? Can explore output feed into new-amendment?
7. **Plan granularity** — How detailed should plan.md be? Just decisions and rationale? Or detailed enough to generate tasks mechanically?
8. **Scenario format** — What does scenarios.md look like? Given/when/then? Free-form examples? Structured YAML?
