---
topic: orchestration-layer-and-memo-paradigm
author: claude-opus-4-7
created_at: 2026-05-18T17:43:21Z
---

## Proposal: Three-layer orchestration architecture

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Articulate the three-layer orchestration architecture as a load-bearing spec concept. Layer 1 is the deterministic Python CLI implementations under each plugin's `.claude-plugin/scripts/bin/`. Layer 2 is the plugin primitives (the heavyweight and thin-transport skills that form the contract surface). Layer 3 is project-local composition — a `.claude/skills/loop/SKILL.md` checked into each consuming repository (livespec-core's own repo, each livespec-impl-* plugin's own repo, and every downstream consumer project) that composes Layer 1 + Layer 2 primitives in a project-specific way. The Layer 3 driver is NOT shipped by livespec-core or by any impl plugin: neither has the per-repo knowledge required (queue path, dispatch table, janitor invocation, budget/mode policy). Cross-side composition (combining `/livespec-core:next` with `<impl-plugin>:next` to produce a unified ranking) belongs at Layer 3 because the weighting decision is per-project.

### Motivation

The 2026-05-18 research revisions in `research/workflow-processes/architecture-summary.html` (Decision 15) and `research/workflow-processes/tool-agnostic-workflow.md` (the orchestration layer doctrine implicit in the new architecture) resolved an ambiguity about where the autonomous-loop driver should live. The pre-elephant snapshot had vague language suggesting it might live in livespec-core; the user pushed back that livespec-core can't ship it (lacks per-repo knowledge) AND no impl plugin can ship it (same plugin gets installed in many different consumer projects, each with their own answers). The three-layer architecture names the resolution: livespec-core publishes primitives, impl plugins publish primitives, and project-local composition wires them. Without this layering in the spec, future contributors will inevitably try to push composition into livespec-core (defeating the per-repo property) or into impl plugins (defeating the per-consumer property).

### Proposed Changes

In `SPECIFICATION/spec.md` (add a new top-level section titled "Three-layer orchestration architecture" placed after §"Lifecycle" or §"Sub-command lifecycle"):

LiveSpec orchestration is structured into three named layers:

- **Layer 1 — Deterministic Python CLIs.** Each plugin (livespec-core and every `livespec-impl-*`) ships Python wrapper implementations under `.claude-plugin/scripts/bin/<cmd>.py`. These CLIs perform the actual work of every skill (validation, file I/O, ranking, gap detection, etc.) and emit structured output suitable for machine consumption. Layer 1 is deterministic and testable in isolation; it carries no LLM calls.

- **Layer 2 — Plugin primitives (skills).** Each plugin's skills (heavyweight authored AND thin-transport, per the thin-transport doctrine) form the published contract surface. Skills delegate to Layer 1 CLIs and add the LLM-orchestrated dialogue, prompt-driven content generation, and structured-finding interpretation appropriate to each skill's purpose. Layer 2 is what consumers of the plugin invoke; Layer 1 is the implementation behind it. The cross-boundary contract (between livespec-core and the active impl plugin) lives entirely at Layer 2.

- **Layer 3 — Project-local composition.** Each repository that consumes livespec (livespec-core's own repo, every `livespec-impl-*` plugin's own repo, and every downstream consumer project) MAY check in a project-local orchestration driver at `.claude/skills/loop/SKILL.md`. The driver composes Layer 2 primitives — invoking `/livespec-core:next` and `<impl-plugin>:next` to produce a unified cross-side ranking; dispatching to the appropriate heavyweight skill for the chosen action; running janitor checks (e.g., `just check` plus `/livespec-core:doctor`); committing on green; looping until the queue drains or a project-defined budget exhausts. Layer 3 is fundamentally per-repository: it knows THIS repo's queue path resolution, dispatch table (mapping item-kind to verb), janitor invocation, budget/mode policy, and commit conventions. Neither livespec-core nor any impl plugin can ship the Layer 3 driver because the composition is fundamentally local.

**Cross-side composition belongs at Layer 3.** The combination of `/livespec-core:next` (spec-side ranking) and `<impl-plugin>:next` (impl-side ranking) into a single 'what should I work on now' answer requires project-specific weighting (whether spec evolution or impl execution is the bottleneck in THIS project at THIS time). Livespec-core MUST NOT bake a particular weighting in; impl plugins MUST NOT either; the weighting is a per-project judgment that lives at Layer 3.

In `SPECIFICATION/non-functional-requirements.md` (under the new §"Implementation plugin ecosystem" introduced by Proposal 1):

- Add a sub-section titled "Project-local orchestration layer" referencing the Layer 3 description in spec.md. Note that the copier template at `livespec-core/templates/impl-plugin/` (per Proposal 1) MUST ship a starter `.claude/skills/loop/SKILL.md` that generated impl-plugin repos inherit. The starter content (default dispatch table, budget defaults, janitor invocation, escalation policy) is deferred to a follow-on refinement; the existence of the starter file in the template is what THIS finding establishes.
- State that the copier-update drift check (per Proposal 1's Finding 3) MUST exclude `.claude/skills/loop/SKILL.md` from drift detection because local divergence of the loop driver is expected and load-bearing — different consumer projects make different orchestration choices.

## Proposal: Project-local Layer 3 loop driver — required shape and discipline

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Define the required shape of the project-local Layer 3 loop driver: a Claude Code skill at `.claude/skills/loop/SKILL.md` that, on invocation, runs an iteration loop composing Layer 2 primitives per the orchestration model. The skill MUST observe a `--mode` discipline (`interactive` vs `autonomous`) and a `--budget` discipline (iteration count, wallclock, or token budget). Janitor failure MUST be a hard gate (no commit on janitor red). The skill is hand-authored per repository; the copier template provides a starter (per Proposal 1) but local divergence is expected and explicitly exempt from copier drift detection.

### Motivation

The 2026-05-18 research revisions in `research/workflow-processes/architecture-summary.html` (the §"Orchestration layer" section and Decision 15) and `research/workflow-processes/tool-agnostic-workflow.md` (the orchestration-layers diagram and its supporting prose) settled the shape of the project-local loop driver after substantial back-and-forth about cost (thin pass-through pattern resolved that), discoverability (skill namespacing won over CLI-only), and placement (project-local won over plugin-resident). The discipline conventions (mode, budget, janitor as hard gate) are load-bearing for autonomous operation safety; without them documented in the spec, every consumer project re-invents safety rails or omits them entirely.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md` (under the new §"Implementation plugin ecosystem → Project-local orchestration layer" sub-section introduced by the companion finding in this propose-change cycle):

Add a sub-section titled "Layer 3 loop driver — required shape and discipline" that states:

- The Layer 3 loop driver MUST be implemented as a Claude Code project-local skill at `.claude/skills/loop/SKILL.md` in each consuming repository. The skill MAY be hand-authored from scratch or generated from the copier starter (per Proposal 1) and customized.

- The driver MUST accept a **mode parameter** (the exact invocation syntax — slash-command argument, environment variable, project-config key, or a combination — is the per-project skill's choice) with at minimum two recognized values:
  - **`interactive`** — the driver picks the work via `next` queries but each dispatched skill invocation runs interactively (human approves spec-side mutations, reviews each work-item closure, etc.). MUST be the default for spec-side dispatches.
  - **`autonomous`** — the driver picks the work AND runs the dispatched skill end-to-end without human approval per iteration; human review happens at PR boundaries only. MUST be the default for impl-side dispatches.
  - Additional modes (e.g., `dry-run` for previewing the loop without mutation) MAY be defined by individual consumer projects.

- The driver MUST accept a **budget parameter** bounding the loop. The driver MUST recognize at minimum one of three forms (or all three composed):
  - **iteration count** (loop terminates after N iterations regardless of queue state)
  - **wallclock duration** (loop terminates after the specified wallclock duration)
  - **token consumption** (loop terminates after consuming approximately N LLM tokens, measured by the driver's best-effort bookkeeping — exact token accounting inside a skill is non-trivial; precision is implementation-dependent)
  The default budget is implementation-defined per consumer project but MUST be finite — an unbounded loop is forbidden. Invocation syntax (named parameters, config keys, etc.) is the per-project skill's choice.

- **Janitor failure is a hard gate.** On every iteration where a mutation occurred, the driver MUST run the project's janitor (typically `just check` plus `/livespec-core:doctor`); a non-zero janitor exit MUST prevent the commit for that iteration. The driver MAY retry the iteration once (rolling back the mutation), MAY escalate to interactive mode for the next iteration, MAY surface the failure to the human and halt, or MAY take other recovery actions — the recovery policy is per-project, but the no-commit-on-janitor-red rule is universal.

- The driver MUST emit a structured iteration journal (typically appended to a project-local file or written as commit trailers) recording each iteration's pick (from `next`), dispatched skill, janitor result, commit SHA (or rollback), and exit reason. The journal MUST be machine-readable for post-hoc audit.

- The driver MUST be exempt from copier-update drift detection (per Proposal 1's copier-template content sync mechanism); local divergence of the loop driver per consumer project is expected and load-bearing.

- The thin-transport brevity discipline (per the thin-transport-skill-doctrine propose-change cycle) does NOT apply to the Layer 3 loop driver — the driver is a heavyweight authored skill (it carries dispatch logic, janitor invocation, mode/budget handling, journal emission) and MAY be as long as the consumer project needs. The discipline that applies is the project-local-composition constraint: the driver MUST NOT contain hardcoded references to other consumer projects' specifics.

## Proposal: Memo paradigm — transient by construction, four dispositions, Persistent Agent Knowledge

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md

### Summary

Document the memo paradigm as a first-class spec concept: memos are transient-by-construction (per the transient-vs-durable-pending principle introduced by Proposal 3), processed via four canonical dispositions (spec-bound, impl-bound, persistent-knowledge, discard), and managed by the `capture-memo` and `process-memos` skills on every impl plugin. Promote **Persistent Agent Knowledge** to a first-class store in the spec terminology (alongside Specification, Specification History, Work Items, Memos): the named target of the persistent-knowledge memo disposition. Persistent Agent Knowledge's form is implementation-dependent — file-based plugins use harness instruction files (CLAUDE.md, AGENTS.md, .ai/<topic>.md), other plugins may use long-lived memory stores — but the contract slot is uniform.

### Motivation

The 2026-05-18 research revisions in `research/workflow-processes/architecture-summary.html` (Decision 9 "Persistent Agent Knowledge is a first-class store" and Decision 11 "Memory is transient by construction") and `research/workflow-processes/tool-agnostic-workflow.md` (the **Memo**, **Process Memos**, and **Persistent Agent Knowledge** glossary entries) consolidated the memo paradigm after extensive comparison to bd-style permanent memory stores. The user explicitly rejected the bd-remember pattern as a junk-drawer anti-pattern; the four-disposition discipline plus the named Persistent Agent Knowledge store is the replacement. Without these named in the spec, impl plugins are likely to drift back toward permanent memory (the path of least resistance), and Persistent Agent Knowledge will remain an implicit convention rather than a contract slot.

### Proposed Changes

In `SPECIFICATION/spec.md` §"Terminology", add three new term definitions:

**Memo** — A transient free-text observation captured for later triage. Stored in the active impl-plugin's Memos store (queue + archive: items remain with a state marker after disposition for audit purposes). Captured via the impl-plugin's `capture-memo` skill; processed via the impl-plugin's `process-memos` skill. **Transient by construction** per the **Transient (queue/archive item)** principle: every memo MUST eventually flow to one of four canonical dispositions or be discarded. The memo is NOT a permanent memory store; doctor's memo-hygiene invariant (per the doctor-invariant-catalog-expansion propose-change cycle) enforces drain pressure when memos accumulate beyond a configured threshold. This rejects the permanent-memory-store pattern of tools like `bd remember`.

**Disposition (memo)** — A user's per-memo routing decision during a `process-memos` triage operation. The four canonical dispositions:

1. **spec-bound** — the memo's content describes intent that belongs in the Specification. `process-memos` routes the memo via the cross-boundary handoff to `/livespec-core:propose-change`; the memo content becomes a proposed-change finding awaiting `/livespec-core:revise`.

2. **impl-bound** — the memo's content describes a concrete impl-side work item (bug, refactor, tactical task). `process-memos` files a freeform work item in the plugin's Work Items store (no `gap-id` label); the work item closes via the freeform fix path when `implement` picks it up.

3. **persistent-knowledge** — the memo's content is long-term agent knowledge that doesn't fit as a spec requirement or as inline code. `process-memos` graduates the memo into the **Persistent Agent Knowledge** store. The graduation is explicit (per-memo user dialogue confirms placement and topic), preventing junk-drawer accumulation.

4. **discard** — the memo's content does NOT belong in spec, impl, or persistent knowledge. `process-memos` marks the memo discarded (state marker remains for audit; the memo content is NOT deleted from the store).

The dispositioned memo remains in the Memos store with its disposition state marker for audit; only the queue role of the store (unrouted memos) is subject to doctor's hygiene threshold.

**Persistent Agent Knowledge** — A first-class store, alongside Specification, Specification History, Work Items, and Memos, holding long-term agent guidance that doesn't fit as a spec requirement or as inline code. The store's **form is implementation-dependent**: file-based impl plugins typically use harness instruction files (`CLAUDE.md`, `AGENTS.md`, `.ai/<topic>.md` files referenced progressively from those harness files so context window stays bounded); other impl plugins may use a long-lived memory store the agent queries at relevant points. The contract slot — "there exists a Persistent Agent Knowledge store in every livespec-impl-* plugin and `process-memos` MUST route persistent-knowledge dispositions into it" — is uniform; the realization is per-plugin. Promoted from the v058-era `.ai/<topic>.md` convention to a named first-class store on 2026-05-18.

In `SPECIFICATION/contracts.md` (under the new §"Implementation-plugin contract — the 9-skill surface" introduced by Proposal 2):

- Each `livespec-impl-*` plugin MUST realize a **Persistent Agent Knowledge** store per the spec terminology. The plugin's own `SPECIFICATION/` MUST document the realization (harness instruction files, long-lived memory store, or other).
- The `process-memos` skill's persistent-knowledge disposition MUST route into this store; the routing mechanism is implementation-dependent but the disposition MUST NOT silently drop the memo content.
- Persistent Agent Knowledge content is NOT subject to doctor's memo-hygiene invariant (it is a store, not a queue/archive; the transient rule applies to memos in their pre-disposition state, not to dispositioned content that has graduated to the persistent store).
- The store MUST be readable by the agent at relevant points (skill invocation, dialogue context resolution, etc.); the loading mechanism (harness-loaded files, on-demand query, embedding-based retrieval) is per-plugin.
