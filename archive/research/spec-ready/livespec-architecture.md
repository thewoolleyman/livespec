# LiveSpec architecture — implementation of the spec ↔ implementation pattern

This document describes the specific LiveSpec instantiation of the
conceptual model defined in
[`tool-agnostic-workflow.md`](./tool-agnostic-workflow.md). All
generic terms used here (Specification, Implementation, Capture
Impl Gaps, Spec Reader, Persistent Agent Knowledge, etc.) carry
the definitions from the glossary in that companion document.

## Plugin distribution: multi-repo

LiveSpec is distributed as a set of Claude Code marketplace
plugins:

- **`livespec-core`** — the spec-lifecycle plugin. Exposes the
  seven spec-side skills, publishes the spec contract and the
  implementation-plugin contract, governs `SPECIFICATION/`.
- **`livespec-impl-<tracking-mechanism>`** — implementation
  plugins, one per backend. Each ships the six canonical impl
  skills under its own namespace prefix and conforms to the
  implementation-plugin contract.

Each plugin lives in a separate GitHub repo with its own
`SPECIFICATION/` (dogfooded), its own release cadence, and its
own version history. The multi-repo split is driven by:

- **CI simplicity.** Per-repo pipelines are mentally simpler than
  monorepo path-filtering with wrapper jobs for required-status
  checks.
- **Agent context isolation.** Filesystem boundaries are
  categorically stronger than per-subdirectory CLAUDE.md
  conventions.

The cost paid is a shared-content sync mechanism. Non-functional-
requirement sections (TDD workflow, code style, CI conventions,
lint rules, Python pins, lefthook setup) genuinely live in
multiple plugins. The sync mechanism (subtree / pinned package /
generator / dedicated meta-repo) is plugin-ecosystem concern,
not spec concern; the existence of shared content is load-bearing.

Implementation-plugin catalog in scope:

- `livespec-impl-plaintext` — files in repo (md / jsonl / yaml /
  html backend; format choice in `.livespec.jsonc`). The format-
  consolidating plugin: one plugin owns readers and writers for
  all formats, making format migration a free bonus capability.
- `livespec-impl-beads` — Dolt-backed graph database via the bd
  CLI.
- `livespec-impl-gitlab` — GitLab work items.
- `livespec-impl-gascity` — Gas City's tracker.
- `livespec-impl-darkfactory-kilroy` — Darkfactory's Kilroy
  tracker.

New implementations slot in by satisfying the same contract;
`livespec-core` does not need to know about them in advance, and
adopters pick whichever implementation matches their concurrency
profile, existing tooling, and operational preferences.

Diagram:
[`../workflow-processes/diagrams/multi-repo-layout.svg`](../workflow-processes/diagrams/multi-repo-layout.svg).

## Marketplace install

Consumer projects install via the standard Claude Code marketplace
flow:

```
/plugin marketplace add thewoolleyman/livespec
/plugin install livespec-core@livespec
/plugin install livespec-impl-<choice>@<marketplace>
```

A consumer project installs exactly one `livespec-core` plus
exactly one `livespec-impl-*` plugin. The choice is recorded in
`.livespec.jsonc`'s `implementation.plugin` key.

## Core vs implementation: API surface

LiveSpec Core publishes a documented contract in
`SPECIFICATION/contracts.md` that implementation plugins MUST
honor. The contract has these sections:

- **File-system contract** — the `SPECIFICATION/` tree shape,
  `proposed_changes/` and `history/vNNN/` ownership, `spec_root`
  resolution rules.
- **Configuration contract** — `.livespec.jsonc` shape and
  per-plugin section ownership.
- **Slash-command contract for `livespec-core`** — every
  `/livespec:*` command's signature.
- **Implementation plugin contract** — what every
  `livespec-impl-*` MUST expose to be considered LiveSpec-
  compatible. Includes the six canonical skills, the Spec Reader
  required capabilities, the untriaged-memo machine query, and
  the Persistent Agent Knowledge conventions for file-based
  realizations.

Diagram:
[`../workflow-processes/diagrams/core-vs-impl-api-surface.svg`](../workflow-processes/diagrams/core-vs-impl-api-surface.svg).

## LiveSpec Core skill surface (7 skills)

| Command | Purpose |
|---|---|
| `/livespec:seed` | Initialize a new spec tree. |
| `/livespec:propose-changes` | Author one or more proposed changes. |
| `/livespec:critique` | Surface observations based on observing the spec; spec-internal analysis only. |
| `/livespec:revise` | Process pending proposed-changes; cut new `history/vNNN`. Selective per-proposal — user MAY address a subset and leave the rest pending. |
| `/livespec:doctor` | Spec invariants (static + LLM-driven) plus memo-hygiene invariant via the impl plugin's untriaged-memo machine query. |
| `/livespec:prune-history` | Bound history size; collapse oldest `vNNN` entries. |
| `/livespec:help` | Overview + routing. |

Diagrams:
[`../workflow-processes/diagrams/spec-lifecycle.svg`](../workflow-processes/diagrams/spec-lifecycle.svg),
[`../workflow-processes/diagrams/seq-revise.svg`](../workflow-processes/diagrams/seq-revise.svg).

## Critique's role

`/livespec:critique`'s role is to surface observations based on
observing the specification. Not the implementation. Not memos.
Not observations from the world. Spec-internal analysis only:
ambiguity, contradiction, undefined terms, dangling references,
prose quality, NLSpec conformance. The complementary impl-side
direction (impl → spec drift) is `/livespec-impl-*:capture-spec-
drift`'s job — a separate skill on the impl side that reads the
spec via the Spec Reader and surfaces findings as proposed
changes via the cross-boundary handoff.

Critique survives as a separate skill (alongside `propose-changes`)
because its input domain is the spec itself — structurally
different from authoring proposed changes from external intent.

## Implementation plugin canonical skill surface (6 skills)

Every `livespec-impl-*` plugin MUST expose these six skills under
its own namespace prefix:

| Command | Purpose |
|---|---|
| `/livespec-impl-*:capture-impl-gaps` | Detect spec → impl gaps mechanically via the Spec Reader; file labeled / categorized gap-tied work items (per-gap user consent). |
| `/livespec-impl-*:capture-spec-drift` | Detect impl → spec drift heuristically (LLM-driven); file findings as proposed changes via `/livespec:propose-changes` (cross-boundary handoff). Asymmetric counterpart to `capture-impl-gaps`. |
| `/livespec-impl-*:capture-work-item` | Freeform direct filing of an impl-side work item (bugs, refactors, tactical tasks). No `gap-id`; closes via the freeform path. Bypasses gap detection and memo ceremony. |
| `/livespec-impl-*:implement` | Drive Red → Green for a single work item; verify via dry-run re-detection (gap-tied); close. Three closure paths: gap-tied fix (verify + audit), freeform fix (simple reason), non-fix (administrative reason). |
| `/livespec-impl-*:capture-memo` | Low-friction free-text deposit of an in-flight observation that the user is not yet ready to classify. Transient by construction. |
| `/livespec-impl-*:process-memos` | Per-memo handholding dialogue with four dispositions: spec-bound (→ `propose-changes`, cross-boundary), impl-bound (→ freeform work item), persistent-knowledge (→ Persistent Agent Knowledge store), discard. |

`list-memos` is **plugin-discretionary**. Each plugin MAY expose
a user-facing `list-memos` if it adds value (search by keyword,
filter by disposition); the canonical contract does not require
it because Doctor's untriaged-memo hygiene query lives on a
separate machine-readable surface.

Cross-boundary handoffs from impl plugins into core occur in
three places: `capture-spec-drift` → `/livespec:propose-changes`
(drift findings), `process-memos` → `/livespec:propose-changes`
(spec-bound disposition), and the untriaged-memo query from
`/livespec:doctor` back into the plugin's memo store. The two
spec → impl edges (`Specification` → Spec Reader, `Specification
History` → Spec Reader) bring the cross-boundary contract total
to five.

Diagrams:
[`../workflow-processes/diagrams/implementation-lifecycle.svg`](../workflow-processes/diagrams/implementation-lifecycle.svg),
[`../workflow-processes/diagrams/seq-capture-impl-gaps.svg`](../workflow-processes/diagrams/seq-capture-impl-gaps.svg).

## Memory model: Persistent Agent Knowledge as a first-class store

Memory in LiveSpec is transient by construction. Every piece of
state MUST eventually flow to one of the three canonical stores
(Specification, Implementation, Persistent Agent Knowledge) or
be discarded. Memos are in-flight state awaiting that resolution;
the Memos box is queue + archive (dispositioned items remain with
a state marker for audit).

The four `process-memos` dispositions encode this:

| Disposition | Action | Notes |
|---|---|---|
| **spec-bound** | Calls `/livespec:propose-changes` with the memo text as input | Cross-boundary handoff to livespec-core; produces a proposed-change file that revise eventually consumes. |
| **impl-bound** | Files a freeform work item in the impl plugin's queue (no `gap-id` label) | Joins the same queue `capture-impl-gaps` and `capture-work-item` populate; `implement` picks it up and closes via the freeform fix path. |
| **persistent-knowledge** | Graduates the memo into the Persistent Agent Knowledge store | Form is implementation-dependent: file-based plugins typically use harness instruction files (CLAUDE.md / AGENTS.md / `.ai/<topic>.md`); other plugins MAY use a long-lived memory store. Named, retrievable, explicitly graduated. |
| **discard** | Marks the memo discarded (state marker; not deletion) | Terminal disposition. The discarded memo remains in the Memos archive for audit but no longer blocks hygiene. |

Persistent Agent Knowledge is a first-class store. Its form is
plugin-dependent. The most common realization in file-based
plugins (`livespec-impl-plaintext`, `livespec-impl-beads`) is a
set of harness instruction files: CLAUDE.md, AGENTS.md, and
`.ai/<topic>.md` files referenced progressively from those
harness files so context window stays bounded. Plugins backed by
external trackers MAY instead use a long-lived memory store the
agent queries at relevant points; the contract requires the slot
to exist, not a specific realization.

Diagrams:
[`../workflow-processes/diagrams/memo-lifecycle.svg`](../workflow-processes/diagrams/memo-lifecycle.svg),
[`../workflow-processes/diagrams/seq-process-memos.svg`](../workflow-processes/diagrams/seq-process-memos.svg).

## Gap-vs-drift asymmetric naming

A spec → impl deficit is a **gap**; an impl → spec lag is a
**drift**. The naming is deliberately asymmetric because the two
directions are categorically different problems:

| Direction | Name | Detection character | Skill |
|---|---|---|---|
| spec → impl (deficit in implementation) | **gap** | Mechanical. Enumerate spec rules; check impl for each. 1:1 invariant per `gap-id`. | `/livespec-impl-*:capture-impl-gaps` |
| impl → spec (lag in specification) | **drift** | Heuristic (LLM-driven). Every line of impl is "doing something"; signal-to-noise is brutal. | `/livespec-impl-*:capture-spec-drift` |

The two MUST be separate skills rather than one bidirectional
skill because merging would hide the reliability gap between
mechanical and LLM-driven detection.

## `.livespec.jsonc` — shared cross-plugin config

The file is the cross-plugin discovery point. Every plugin reads
it; livespec-core reads core keys; each impl plugin reads its
own top-level section. Schema is open at the root
(`additionalProperties: true`) so plugins can extend without
central coordination.

```jsonc
{
  // owned by livespec-core
  "template": "livespec",
  "spec_root": "SPECIFICATION",
  "pre_step_skip_static_checks": false,

  // implementation activation
  "implementation": {
    "plugin": "livespec-impl-plaintext"
  },

  // each implementation owns a top-level section keyed by its name
  "livespec-impl-plaintext": {
    "format": "md",
    "work_items_path": "implementation-work-items/"
  }
  // ... or "livespec-impl-beads": { "issue_prefix": "li-" }
  // ... or "livespec-impl-gitlab": { "project_id": "...", "labels_prefix": "livespec/" }
}
```

Rules in the published contract:

- livespec-core's schema covers Core's keys; all other top-level
  keys are open.
- Each impl plugin owns the schema for its own top-level section,
  named for the plugin.
- Each plugin MUST validate its own section on read; MUST tolerate
  unknown sections owned by other plugins.
- **Secrets MUST NOT live here.** External-tracker implementations
  (gitlab, jira, linear) need a separate credentials channel (env
  vars, OS keyring, 1Password, etc.). `.livespec.jsonc` is
  git-committed and may only contain non-sensitive configuration.

## Why livespec dogfoods plaintext, not beads

LiveSpec itself uses `livespec-impl-plaintext` (JSONL format) as
its implementation provider. The choice is driven by livespec's
own concurrency profile (single-author + branch-parallelism)
making the Dolt-backed merge story that beads uniquely provides
irrelevant for this project, while plaintext avoids the
integration cost that bd carries:

- 32 KB of workaround bootstrap scripts (`setup-beads.sh`,
  `bd-doctor.sh`).
- Documented upstream bugs (catalogued in
  `dev-tooling/implementation/research/beads-problems.md` and
  `research/beads/beads-gaps-workarounds.md`), including some
  with silent failure modes.
- Hook-chaining race with lefthook contributing to ongoing CI
  work.
- `bd edit` footgun (blocks agents; convention-enforced).
- Setup-time onboarding cost for new contributors.

The features beads provides over plaintext+git that are NOT
trivially replicable in plaintext: only the Dolt concurrent-merge
story, which livespec doesn't need.

`livespec-impl-beads` survives as a first-class implementation
for adopters who DO have the concurrency profile (e.g., Gas City).
The LiveSpec ecosystem supports both; LiveSpec the project picks
the one matching its actual usage. Other LiveSpec adopters
similarly choose the plugin whose concurrency profile matches
their team shape.

## Pluggable diagrams (reference index)

The complete diagram set for the workflow lives at
[`../workflow-processes/diagrams/`](../workflow-processes/diagrams/).
Quick index:

- `tool-agnostic-workflow.svg` — single composite view of the
  workflow using generic vocabulary.
- `multi-repo-layout.svg` — plugin distribution topology.
- `core-vs-impl-api-surface.svg` — what Core publishes and what
  every impl plugin honors.
- `spec-lifecycle.svg` — spec-side skill flow.
- `implementation-lifecycle.svg` — impl-side skill flow with
  Spec Reader.
- `memo-lifecycle.svg` — memo capture and routing including
  Persistent Agent Knowledge.
- `seq-revise.svg`, `seq-capture-impl-gaps.svg`,
  `seq-process-memos.svg` — sequence diagrams for the three most
  intricate skill flows.
- `legend.svg` — symbol vocabulary.
