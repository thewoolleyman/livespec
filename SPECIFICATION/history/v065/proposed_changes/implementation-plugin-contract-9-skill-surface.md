---
topic: implementation-plugin-contract-9-skill-surface
author: claude-opus-4-7
created_at: 2026-05-18T17:43:21Z
---

## Proposal: Thin-transport skill doctrine and skill-weight terminology

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md

### Summary

Establish the **thin-transport skill** doctrine as a first-class spec concept: every contract-surface API a livespec plugin exposes MUST be a Claude Code skill, whether the skill carries dialogue and judgment (heavyweight authored) or is a deterministic pass-through to a CLI implementation (thin transport). Retires the prior split between user-facing skills and a separate machine-only contract surface. Adds the **Thin-transport skill** and (implicitly companion) **Heavyweight skill** distinctions to spec terminology and binds the doctrine into the contracts surface.

### Motivation

The 2026-05-18 research revisions in `research/workflow-processes/architecture-summary.html` (Decision 17) and `research/workflow-processes/tool-agnostic-workflow.md` (the new **Thin-transport skill** glossary entry) resolved an inconsistency in the pre-elephant design that had `list-memos` as plugin-discretionary while a separate untriaged-memo machine query was contract-required. The doctrine articulated by the user (every contract-surface API is a skill backed by a CLI implementation) collapses two surfaces into one and matches the existing livespec pattern where every authored skill already wraps a Python wrapper at `.claude-plugin/scripts/bin/<cmd>.py`. Naming the doctrine in the spec prevents future contributors from re-introducing the split (e.g., adding a 'pure machine surface' for a new contract query).

### Proposed Changes

In `SPECIFICATION/spec.md` §"Terminology", add two new term definitions (alphabetical placement appropriate):

**Thin-transport skill** — A Claude Code skill whose entire responsibility is to invoke its backing Python wrapper at `.claude-plugin/scripts/bin/<cmd>.py` and present the structured output verbatim, with NO ranking, summarization, or judgment in the SKILL.md body. Used for contract-surface query operations that need deterministic, fast, repeatable output suitable for invocation by other skills, by the project-local orchestration layer, or by automated tooling. The SKILL.md MUST stay short and MUST NOT accrete prompt content over time; all ranking, filtering, and formatting logic MUST live in the backing Python implementation. Mechanical enforcement (lint rule, line-count check, or SKILL.md schema) is deferred to a follow-on refinement but the discipline is load-bearing for the doctrine. Thin-transport skills render identically to heavyweight skills at the slash-command and namespace level; the distinction is internal to each skill's design.

**Heavyweight (authored) skill** — A Claude Code skill whose SKILL.md body carries the orchestrating prompt itself — dialogue capture, detection logic, judgment calls, structured-finding interpretation. Contrasts with **thin-transport skill**. All existing livespec-core skills authored before 2026-05-18 (`seed`, `propose-change`, `critique`, `revise`, `doctor`, `prune-history`, `help`) are heavyweight authored skills. Plugins MAY mix heavyweight and thin-transport skills freely; the contract surface treats them uniformly.

In `SPECIFICATION/contracts.md` (add a new section titled "Thin-transport skill doctrine" near the existing §"Wrapper CLI surface" or §"Skill ↔ template JSON contracts" cluster):

- Every contract-surface API a livespec plugin exposes MUST be exposed as a Claude Code skill (heavyweight authored or thin-transport per the terminology), NOT as a CLI-only surface or any other non-skill mechanism. This applies to both `livespec-core` and every `livespec-impl-*` plugin.
- Thin-transport skills MUST delegate to a backing Python wrapper at `.claude-plugin/scripts/bin/<cmd>.py` following the existing wrapper-shape contract; the wrapper performs the work and the SKILL.md is a transport.
- Cross-plugin invocation (doctor invoking the active impl-plugin's `list-memos`, the project-local loop driver invoking `livespec-core:next` and `<impl-plugin>:next`, etc.) MUST go through the skill namespace (e.g., `/livespec-impl-plaintext:list-memos --filter=untriaged --json`), NOT through a direct CLI path. This makes the contract surface discoverable, namespaced, and agent-aware uniformly.
- The thin-transport classification is internal to each skill's design and SHOULD be reflected in inline SKILL.md metadata or a tagging convention (the exact mechanism is deferred to a follow-on refinement); diagram rendering treats thin-transport and heavyweight skills identically (both render as light-blue rounded rectangles per the diagram vocabulary).

## Proposal: The 9-skill implementation-plugin contract surface

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Define the implementation-plugin contract surface as nine required skills: six heavyweight authored skills (`capture-impl-gaps`, `capture-spec-drift`, `capture-work-item`, `implement`, `capture-memo`, `process-memos`) plus three thin-transport query skills (`list-memos`, `list-work-items`, `next`). Every `livespec-impl-*` plugin MUST expose these nine skills under its own namespace prefix; consumer projects, doctor's cross-boundary invariants, and the project-local orchestration layer all consume the surface uniformly via skills (per the thin-transport doctrine).

### Motivation

The 2026-05-18 research revisions in `research/workflow-processes/architecture-summary.html` (Decision 18) and `research/architecture/multi-repo-implementation-providers.md` (the post-orchestration 9-skill table) settled the implementation-plugin contract surface after extensive working-through of which queries belong in the contract (work-items + memos query + next), what 'next' actually does (ranking, not state), and the asymmetry with the spec side (no symmetric query skills because the spec backend is fixed). Without the 9-skill contract documented, impl-plugin authors do not know what to expose; without the thin-transport classification, the boundary between heavyweight authored skills and contract-surface queries gets blurred. The current spec describes only a 3-skill repo-local plugin (being removed by Proposal 1) — the new 9-skill contract MUST replace it explicitly.

### Proposed Changes

In `SPECIFICATION/contracts.md` (add a new top-level section titled "Implementation-plugin contract — the 9-skill surface" appropriate to follow §"Plugin distribution" or the new §"Cross-repo coordination — pin-and-bump" section from Proposal 1):

Every `livespec-impl-*` plugin MUST expose these nine skills under its own namespace prefix (i.e., `/livespec-impl-<X>:<skill>`):

**Heavyweight authored skills (6):**

- **`capture-impl-gaps`** — Detect spec → impl gaps mechanically via the Spec Reader; file gap-tied work items into the plugin's Work Items store (per-gap user consent). Collapses the v058-era `refresh-gaps` + `plan` pair into one ephemeral-detection skill. Detection state is in-memory and discarded at skill exit (no persistent intermediate artifact).

- **`capture-spec-drift`** — Detect impl → spec drift heuristically (LLM-driven); per finding (with user consent) route to `/livespec-core:propose-change` via the cross-boundary handoff. Asymmetric counterpart to `capture-impl-gaps` (mechanical detection is on the spec→impl side; heuristic detection is on the impl→spec side).

- **`capture-work-item`** — Freeform direct filing of an impl-side work item (bugs, refactors, tactical tasks). The resulting work item carries NO `gap-id` label and closes via the freeform fix path.

- **`implement`** — Drive Red→Green for a single work item; for gap-tied items verify closure by re-running `capture-impl-gaps` in dry-run mode and confirming the gap-id is no longer detected; for freeform items close with a simple `--reason`. Closure branches on origin × disposition: gap-tied fix (verify + audit fields), freeform fix (simple reason), non-fix (administrative — `wontfix`, `duplicate`, `spec-revised`, `no-longer-applicable`, `resolved-out-of-band`).

- **`capture-memo`** — Low-friction free-text deposit of an in-flight observation that the user is not yet ready to classify. Memos are transient by construction (per the transient-vs-durable-pending principle).

- **`process-memos`** — Per-memo handholding dialogue: dispositions are spec-bound (→ `/livespec-core:propose-change` cross-boundary handoff), impl-bound (→ freeform work item in the plugin's Work Items store), persistent-knowledge (→ Persistent Agent Knowledge store, form is implementation-dependent), or discard.

**Thin-transport skills (3) — required machine query surface:**

- **`list-memos`** — Required (promoted from discretionary). Supports `--filter` flags (most notably `--filter=untriaged`) and `--json` output. Consumed by doctor's memo-hygiene invariant and by users for queue inspection.

- **`list-work-items`** — Required (new). Supports filter flags (`--gap-tied`, `--blocked`, `--with-gap-id`, etc.) and `--json` output. Consumed by doctor's four work-item structural invariants (defined by the doctor-invariant-catalog-expansion propose-change cycle), by the project-local loop driver for routing decisions, and by users for queue inspection.

- **`next`** — Required (new). Ranks the most ripe impl-side action using whatever native primitives the backend provides (e.g., `bd ready` for a beads-backed impl, JSONL traversal for a plaintext impl, GitLab API for a gitlab impl). Returns structured JSON with at minimum `action`, `work_item_ref`, `urgency`, and `reason` fields. Pure function of impl-side state; no LLM in the ranking path. Asymmetric counterpart to `livespec-core:next` (defined by the companion finding in this propose-change cycle).

**Cross-boundary handoffs (red edges in the workflow diagrams):**

1. `<impl-plugin>:capture-spec-drift` → `/livespec-core:propose-change` (drift findings).
2. `<impl-plugin>:process-memos` → `/livespec-core:propose-change` (spec-bound memo disposition).
3. `/livespec-core:doctor` → `<impl-plugin>:list-memos --filter=untriaged --json` (memo-hygiene invariant).
4. `/livespec-core:doctor` → `<impl-plugin>:list-work-items --json` (work-item structural invariants).
5. The project-local Layer 3 loop driver invokes both `/livespec-core:next` and `<impl-plugin>:next` to compose cross-side recommendations (the cross-side composition itself is defined by a separate propose-change cycle for the orchestration layer).

Backend-variability asymmetry: the impl side requires skill-wrapped queries because impl backends are pluggable (plaintext / beads / gitlab / ...); the spec side does NOT need symmetric `list-proposed-changes` / `list-history` skills because the spec backend is fixed (the canonical SPECIFICATION/ tree shape) and doctor's static phase already reads spec-side state directly from the filesystem.

## Proposal: Spec-side `next` thin-transport skill on livespec-core

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/spec.md

### Summary

Add `/livespec-core:next` as a new thin-transport skill on the livespec-core surface (the spec-side counterpart to `<impl-plugin>:next`). Brings the livespec-core skill count from 7 → 8. The skill ranks the most ripe spec-side action by reading the Proposed Changes queue depth, the Specification History recency, and unresolved Doctor findings; it returns structured JSON. Pure function of spec-side file state; no LLM in the ranking path; does NOT read impl-side stores (cross-side composition is the project-local orchestration layer's job).

### Motivation

The 2026-05-18 research revisions in `research/workflow-processes/architecture-summary.html` (Decision 18, and the 8-skill core surface table) and `research/workflow-processes/tool-agnostic-workflow.md` (the new "Required thin-transport query skills" section) added `livespec:next` to the spec-side surface as a thin-transport ranking primitive parallel to the impl-side `<impl-plugin>:next`. Without `livespec-core:next` documented, project-local orchestration loops would have no spec-side ranking primitive to consume and would have to either (a) re-implement spec-side ranking ad hoc per project, or (b) skip spec-side prioritization entirely. The two skills together form the cross-side ranking surface composed at the project-local Layer 3 (defined by a separate propose-change cycle).

### Proposed Changes

In `SPECIFICATION/contracts.md` (under the existing §"Plugin distribution" or the new §"Implementation-plugin contract — the 9-skill surface" section's spec-side parallel paragraph):

- The currently-documented livespec-core skill surface MUST grow from seven to eight slash commands: `seed`, `propose-change`, `critique`, `revise`, `doctor`, `prune-history`, `help`, AND **`next`** (new). The renamed namespace from Proposal 1 makes these `/livespec-core:seed` etc.; the eighth is `/livespec-core:next`.
- `/livespec-core:next` is a **thin-transport** skill per the doctrine. The backing Python wrapper lives at `.claude-plugin/scripts/bin/next.py` following the existing wrapper-shape contract. The SKILL.md MUST be a pass-through.
- The skill MUST read spec-side state (the Proposed Changes queue under `<spec-root>/proposed_changes/`, the Specification History under `<spec-root>/history/`, and any unresolved doctor findings if cached) and emit structured JSON. The output schema MUST include at minimum `action` (one of: `revise`, `propose-change`, `critique`, `prune-history`, `none`), `reason` (human-readable narration), and `urgency` (one of: `high`, `medium`, `low`). Additional fields MAY be added by follow-on refinements.
- The skill MUST NOT read impl-side stores; cross-side ranking composition (combining `/livespec-core:next` and `<impl-plugin>:next`) is the responsibility of the project-local orchestration layer (defined by a separate propose-change cycle), NOT of livespec-core.
- The skill MUST NOT mutate any spec-side state; it is purely advisory.
- The skill MUST be exempt from the pre-step/post-step doctor static lifecycle (no mutation, no precondition risk) per the existing exemption convention for `help`, `doctor`, and `resolve-template`.

In `SPECIFICATION/spec.md` §"Sub-command lifecycle":

- Update the enumeration of sub-commands from seven to eight: `seed`, `propose-change`, `critique`, `revise`, `prune-history`, `doctor`, `help`, AND `next`.
- Add `next` to the list of sub-commands with no pre-step and no post-step wrapper-side static (the existing list includes `help`, `doctor`, and `resolve-template`; `next` joins it).

## Proposal: Spec Reader required-capability surface for implementation-plugin adapters

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Define the **Spec Reader** required-capability surface that every `livespec-impl-*` plugin MUST expose internally to its own skills (`capture-impl-gaps`, `capture-spec-drift`, `implement`, `process-memos`). The Spec Reader is the impl-side adapter unifying spec-content access regardless of the plugin's backend; its internals are implementation-dependent (thin file pass-through, cached, indexed, embedded, RAG-style) but the required capabilities are uniform. Four required capabilities: (1) read the current Specification, (2) read the Specification History, (3) report the current spec version (`vNNN`), (4) read or summarize differences between specified versions.

### Motivation

The 2026-05-18 research revisions in `research/workflow-processes/architecture-summary.html` (Decision 8) and `research/workflow-processes/tool-agnostic-workflow.md` (the **Spec Reader** glossary entry and the §"Impl-side API" section) named the Spec Reader as a first-class impl-side adapter. Without the required-capability surface documented in livespec-core's contract, impl-plugin authors are left to invent ad-hoc spec-reading mechanisms per plugin, which (a) prevents shared tooling, (b) makes the cross-boundary edges undocumented in any uniform sense, and (c) blocks future advanced impl plugins (e.g., RAG-style retrieval) from declaring compliance with a stable surface. The four required capabilities are the minimum surface every skill that consumes spec content needs.

### Proposed Changes

In `SPECIFICATION/contracts.md` (add a new section titled "Spec Reader required-capability surface" placed near or under the new §"Implementation-plugin contract — the 9-skill surface"):

- Every `livespec-impl-*` plugin MUST expose a **Spec Reader** adapter internally — an impl-side API surface that unifies spec-content access for the plugin's own skills. The Spec Reader is NOT a slash-command or a cross-boundary surface; it is a within-plugin contract that the plugin's skill authors implement and consume.
- The Spec Reader MUST implement exactly the following four required capabilities; the API shape (function names, return types, language) is implementation-dependent and MUST be documented in the plugin's own `SPECIFICATION/`:

  1. **Read the current Specification.** Return the full content (or section-level addressable subset) of every spec_root file the active template manifest declares (per the template_config.schema.json `spec_files` mechanism landed in v063 by the `template-manifest-additional-files` propose-change cycle). The set is template-dependent; the Spec Reader MUST consult the active template's manifest rather than hardcoding the well-known file list.

  2. **Read the Specification History.** Return the content of any `vNNN/` directory under `<spec-root>/history/` for `NNN` in the contiguous range. MUST surface the pruned-marker exemption (`PRUNED_HISTORY.json`) for any version that has been pruned per the existing `version-directories-complete` exemption.

  3. **Report the current spec version.** Return the latest `vNNN` integer under `<spec-root>/history/`. This is the canonical version the impl currently corresponds to.

  4. **Read or summarize differences between specified versions.** Given two version numbers `vA` and `vB`, return a representation of what changed between them. The representation form is implementation-dependent (raw diff, structured change list, semantic summary, etc.); the contract is that the consumer skill MUST be able to answer "what is different between vA and vB."

- The Spec Reader's internals MAY be a thin file pass-through (plain-text reads of the spec_root tree), a cached layer, a section-level index, an embedding-based retrieval, a RAG-style adapter, a denormalized graph, or anything in between. The required-capability surface defines WHAT the adapter MUST provide; the HOW is per plugin.

- The Spec Reader MUST exclude content from `<spec-root>/proposed_changes/` from its returned spec content; only ratified canonical content is exposed. Pending proposals are not yet intent.

- Skills that consume the Spec Reader include `capture-impl-gaps` (gap-rule enumeration; also uses the version query to detect what has changed since the skill's own last-checked marker, an impl-internal state), `capture-spec-drift` (comparison baseline), `implement` (work-item context resolution), and `process-memos` (spec-vs-impl disposition decisions). Other impl-side operations MAY consume it as needed.

- The Spec Reader is NOT a Claude Code skill (no slash command, no namespace surface); it is an internal API within each `livespec-impl-*` plugin. This distinguishes it from the nine cross-boundary contract skills defined by the companion finding in this propose-change cycle.
