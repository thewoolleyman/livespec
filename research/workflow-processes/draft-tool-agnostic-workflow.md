# Draft — tool-agnostic workflow diagram

**Status:** DRAFT for review (v8). Not yet integrated into the
canonical
[`2026-05-11-architecture-summary.html`](./2026-05-11-architecture-summary.md);
expected to iterate based on review feedback before promotion.

**Purpose:** represent the fundamental spec ↔ implementation
workflow with **tool-agnostic, generic domain terminology**
(NOT bound to `livespec`, `/livespec:*` skill names, or any
specific implementation plugin).

**Layout conventions:**

- **SPEC SIDE** (pink package, left) ▏ **IMPLEMENTATION SIDE** (green package, right). Side-by-side rather than vertically stacked — see *Layout history* below for why.
- **Arrow direction = data flow.** A read goes `artifact → skill`; a write goes `skill → artifact`.
- **Shape vocabulary:**
  - light blue rounded rectangle = skill / operation (verb is in the node name)
  - tan cylinder = artifact / store / queue (noun)
  - yellow rectangle = external input (the single entry point)
- No actor figures. Any action can be taken by a human or an agent; the actor distinction isn't load-bearing. A single yellow input rectangle ("initial intent / prompt / instruction / seed") represents the external entry point into Seed.
- **Cross-boundary edges** between the two packages are **hard contracts**; rendered as thick red lines.
- All arrows are pure black for contrast; all node text is dark.
- Arrow labels are sparse — only where genuinely ambiguous (Process Memos disposition branches; Doctor's untriaged-memo query).

## Diagram

![Draft tool-agnostic workflow](./diagrams/draft-tool-agnostic-workflow.svg)

[PlantUML source](./diagrams/draft-tool-agnostic-workflow.plantuml)

## Summary

This section describes every node in the diagram, organized by
node type. Each node carries one paragraph summarizing its role
and the nuances established during the design conversation.

### Spec / implementation split

**Why this is needed:** the spec captures *what should be true* (prescription); the implementation captures *what is true* (description). Treating these as one combined artifact conflates intent with realization, which makes it impossible to verify whether impl matches intent, to evolve them at independent paces, or to substitute one implementation for another while keeping the intent stable. A foundational invariant falls out of this: every piece of project state must live on one side or the other — not both, not neither.

The wall between the two sides is hard. Neither side reads the other directly except through the **cross-boundary contracts** rendered as red edges in the diagram (and enumerated in the *Cross-boundary contracts* table below). Every cross-boundary edge is a deliberate, audited handoff rather than an implicit coupling — the wall forces the relationship between spec and implementation to be explicit and load-bearing rather than ambient.

The implementation side is **pluggable**. LiveSpec Core (the spec side) publishes the contract; any implementation that fulfills it is interchangeable. The implementation can take any form — files in the repo (markdown, JSONL, YAML, HTML, etc.), an embedded database, a third-party issue tracker, or a hybrid — as long as it satisfies the published contract obligations (the cross-boundary edges plus the machine-readable query/mutation APIs that Doctor and the disposition handoffs rely on). Concrete implementations already in scope: `livespec-impl-plaintext` (files in repo, configurable format), `livespec-impl-beads` (Dolt-backed graph database), `livespec-impl-gitlab` (GitLab work items), `livespec-impl-gascity` (Gas City's tracker). New implementations slot in by satisfying the same contract; LiveSpec Core does not need to know about them in advance, and adopters pick whichever implementation matches their concurrency profile, existing tooling, and operational preferences.

### External input

#### initial intent / prompt / instruction / seed

**Why this is needed:** workflows do not start themselves; the system needs one explicit external entry point that admits intent from a human, an agent, or an automated trigger without privileging which.

The single external entry point into the workflow. Represents
whatever sparks a workflow action — a human's initial ask, an
agent's recurring prompt, an instruction from elsewhere in the
team. The diagram uses exactly one external input box (rather
than separate User and Agent actors) to convey that any
operation can be invoked by a human or an agent and the workflow
is not sensitive to which — actor identity is not load-bearing.
The arrow from this node goes only to `Seed` because every other
skill is invoked from within an already-running project; they
are internal entry points, not external ones, even when a human
or agent triggers them directly. In practice this is realized as
a human typing a slash-command, an agent firing a scheduled
skill, an automated job dispatching work, or any other
mechanism by which external intent enters the system.

### Skills / operations

*Spec side.*

#### Seed

**Why this is needed:** a new project's spec cannot exist without an initial materialization step; the rest of the workflow assumes a spec tree it can read, mutate, and version against.

One-time bootstrap of a new project's Specification. Reads the
initial intent and materializes the initial state of the
Specification tree (the template-declared spec files plus a
`v001` History snapshot). Runs once at project birth; after the
seed commit lands the imperative window for direct spec edits
closes, and all subsequent spec mutations MUST flow through
`Propose Change → Revise`. Seed is exempt from the pre-step
doctor check (there is no prior state to check) but does run a
post-step check to verify the materialized state is consistent.

#### Propose Change

**Why this is needed:** once the imperative window closes, spec mutations need a structured, audited entry point — otherwise every change becomes either an unrecorded direct edit or heavyweight ceremony that gets bypassed.

User-initiated authoring of one or more proposed changes to the
Specification. Accepts either a free-text rough deposit
(lightweight, no structure required) or a full interactive
structured dialogue, producing a proposed-change file in the
Proposed Changes queue. This is the **direct** path for
spec mutations — invoked when the user or agent knows they want
to change the spec. Plural in name (`propose-changes`) because
a single invocation can author multiple proposals atomically in
one file with one or more `## Proposal:` sections; cardinality
1-to-N. Proposed-changes wait in the queue for a `Revise` pass
to process them.

#### Critique

**Why this is needed:** spec quality issues (contradictions, undefined terms, dangling anchors) accumulate silently as the spec grows; a casual read will not surface them, so a systematic analytical pass is required to catch them before they erode the spec's authority.

LLM-driven analytical pass over the Specification — observes the
spec in isolation and surfaces findings about **spec quality**:
internal contradictions, ambiguities, undefined terms, dangling
references, BCP14-keyword issues, prose-quality concerns. Each
finding can promote to a proposed change in the Proposed Changes
queue. Critique deliberately does NOT compare spec against
implementation; that is `Capture Spec Drift`'s job and lives on
the impl side. Cardinality is 1-to-N: one invocation produces
many findings, each potentially becoming its own proposal.
Posture differs from `Propose Change`: Critique does not require
prior user intent — it can walk the spec without being told what
to look for.

#### Revise

**Why this is needed:** proposed changes do not apply themselves; the queue needs a controlled process that walks each proposal with the user, applies accepted ones, snapshots the result, and produces an audit trail.

Processes pending entries in the Proposed Changes queue, applies
accept / modify / reject decisions per proposal in dialogue with
the user, and cuts a new Specification History snapshot
(`vNNN`). Selective per-proposal — the user can address a subset
and leave the rest pending for a future pass. Every successful
Revise cuts a new version even when every decision is `reject`,
preserving the rejection audit trail with byte-identical spec
files. Applies any `resulting_files` updates from accepted
proposals to the Specification in place before snapshotting.

#### Doctor

**Why this is needed:** spec and store invariants drift silently — broken anchors, missing sections, untriaged memos accumulating past their hygiene window — and without a regular hygiene check those failures fester until they cause harder downstream breakage.

Health and invariant check across the Specification, the
Proposed Changes queue, and the Specification History. Also
queries impl-side stores (notably the Memos queue) via the
machine-readable impl-plugin contract for cross-cutting hygiene
invariants. Runs in two layers: a **static phase** that
mechanically detects structural failures (file shape, schema
conformance, anchor reference resolution, contiguous-version
invariant, etc.), and an **LLM-driven phase** that surfaces
findings about spec quality and inter-store hygiene. Memo
hygiene — "no untriaged memo MUST remain unresolved beyond N
days" — is one such invariant; Doctor does not know how memos
get resolved (that is the impl plugin's responsibility), only
that they should be. Invokes as a pre-step and post-step around
every other spec-side skill (except Seed pre-step, which has no
prior state to check).

*Implementation side.*

#### Capture Impl Drift

**Why this is needed:** without mechanical detection of which spec requirements are missing in impl, the gap-tracking discipline cannot be enforced and work either falls through the cracks or gets duplicated against the same underlying gap.

Detects implementation gaps where the spec prescribes something
the implementation does not yet reflect. Walks the spec and the
impl, runs gap-detection predicates, and per detected gap files
an appropriately labeled, categorized work item into the Work
Items queue (with per-gap user consent). Work items it creates
carry a marker (e.g. a `gap-id:gap-NNNN` label) tying them back
to the originating gap, which makes closure verifiable: re-running
this skill in dry-run mode and confirming the gap-id is no longer
detected is the verification step. Collapses what used to be two
separate operations (`refresh-gaps` + `plan`) into one
consent-driven skill; the previous persistent JSON intermediate
artifact is eliminated — detection state is ephemeral and
in-memory. Implementation-specific in nature: each implementation
plugin (`livespec-impl-plaintext`, `livespec-impl-beads`,
`livespec-impl-gitlab`, etc.) defines its own predicate set and
storage backend.

#### Capture Work Item

**Why this is needed:** not every piece of impl work derives from a spec rule or an in-flight memo; bugs, refactors, and tactical tasks need a low-ceremony direct path to track them without pretending to be drift detection or observation triage.

User-initiated direct path to file a work item, bypassing both
gap detection and memo ceremony. The third deposit channel —
alongside `Propose Change` (spec-bound work) and `Capture Memo`
(uncertain observations) — invoked when the user is certain the
work is impl-bound, well-formed, and ready to track. Items it
creates are **freeform**: they carry no gap-id marker, do not
participate in the 1:1 gap-tracking invariant, and close via
the freeform path (simple `--reason` text, no verification
step). This is the restoration of the old observation-flow's
"Path B — manual create, freeform issue" pattern, which was
lost in the tool-agnostic refactor and is necessary for
everyday workflows like filing a discrete bug, queuing a
refactor, or capturing a tactical cleanup task that does not
trace back to any spec rule.

#### Implement

**Why this is needed:** work items do not realize themselves; once filed, they need a driver that authors a failing test, produces the impl that turns it green, verifies closure correctly per the item's origin, and updates the tracker.

Generic work-item processor — pulls items from the Work Items
queue (typically leaf-level, no blockers), drives a Red → Green
code cycle (a failing test first, then the implementation that
turns it green), and closes the item. Agnostic to the work
item's origin (gap-tied from `Capture Impl Drift`, impl-bound
from `Process Memos`, or freeform from `Capture Work Item`).
Branches on closure based on the gap-id marker: **gap-tied**
items require verification (re-run `Capture Impl Drift` in
dry-run, confirm the gap-id is no longer detected, record audit
fields including verification timestamp); **freeform** items
close with a simple reason and no verification step. The
`implement` verb is deliberate — the skill stays a clean
processor and is not renamed for symmetry with the `capture-*`
family, because work items can legitimately originate from
sources other than spec gaps.

#### Capture Spec Drift

**Why this is needed:** sometimes the impl is observably correct and the spec is wrong; without explicit detection of this direction of drift, the spec slowly atrophies as ground truth shifts beneath it and no skill is responsible for catching the divergence.

Detects impl-to-spec drift — places where the implementation has
done something that looks load-bearing but is not reflected in
the spec. Reads both the spec and the impl, runs LLM-driven
analytical detection, and per finding (with user consent) routes
to `Propose Change` to create a proposal that updates the spec.
Mirror image of `Capture Impl Drift` but with categorically
different detection characteristics: spec → impl is mechanically
tractable (enumerate spec rules, check impl for each), while
impl → spec is heuristic and fuzzy (every line of impl is "doing
something"; signal-to-noise is brutal). This asymmetric
detection difficulty is structural rather than incidental, which
is why the two directions are separate skills rather than one
bidirectional skill — merging would hide the reliability gap
between mechanical and LLM-driven detection.

#### Capture Memo

**Why this is needed:** in-flight observations that are not yet ready for spec or impl classification will be lost or force-fit into the wrong channel unless there is a low-friction transient deposit that preserves them for later triage.

Low-friction free-text deposit of an in-flight observation that
the user or agent is not yet ready to classify as spec-bound,
impl-bound, or persistent agent knowledge. Writes the memo into
the Memos queue for later triage via `Process Memos`. The verb
is `capture` (rather than `remember`) deliberately — generic
across backends and avoiding tool-specific vocabulary. Memos are
**transient by construction**: the LiveSpec philosophy says every
piece of intent must eventually flow to either the Specification
or the Implementation (or be discarded as no longer relevant);
memo is not a permanent store. Doctor enforces this with an
invariant warning when memos accumulate beyond a configured
hygiene threshold. This is a fundamental paradigm shift from
tools like `bd remember` where memories accumulate indefinitely
as a persistent agent context store; LiveSpec rejects that
pattern as a junk drawer that erodes the canonical stores.

#### Process Memos

**Why this is needed:** captured memos must eventually flow to spec, impl, persistent knowledge, or discard — otherwise the memo store devolves into a junk drawer that erodes the canonical stores and that LLMs cannot reliably consume.

Per-memo handholding skill that walks pending memos and disposes
each via user dialogue. Four dispositions: **(1) spec-bound** →
routes to `Propose Change` (cross-boundary handoff into the
spec-side workflow); **(2) impl-bound** → files a freeform work
item into Work Items; **(3) persistent agent knowledge** →
graduates the memo to a named file under Persistent Agent
Knowledge (the `.ai/<topic>.md` convention) with a
progressively-loaded reference added to AGENTS.md / CLAUDE.md;
**(4) discard** → removes the memo with no follow-on artifact.
The handholding principle is load-bearing: users do not manually
invoke `Propose Change` for spec-bound memos; `Process Memos`
drives them through the appropriate downstream skill. Doctor's
hygiene warning about untriaged memos points to `Process Memos`
as the resolution mechanism.

### Artifacts / stores / queues

*Spec side.*

#### Specification

**Why this is needed:** a project needs a single canonical source of truth for intent that humans and agents can consult, reference, and align against; without it, intent fragments across hallway conversations, code comments, and tribal knowledge that LLMs cannot reliably consume.

The canonical, ratified source of truth for the project's intent
— what the system MUST / SHOULD / MAY do or be. Typically a tree
of markdown files (`spec.md`, `contracts.md`, `constraints.md`,
`scenarios.md`, `non-functional-requirements.md`, `README.md`)
at a known root resolved via `.livespec.jsonc`. Mutates only
through the `Propose Change → Revise` loop after the initial
Seed; direct edits are forbidden once the seed commit closes the
imperative window. Read by `Capture Impl Drift` (as the
prescription), `Capture Spec Drift` (for the comparison
baseline), `Critique` (for analysis), and `Doctor` (for
invariant checks). When the Specification and the Implementation
disagree, **the side that is correct depends on the situation**
(impl drifted from spec, vs. spec drifted from observed impl)
— which is exactly why the two `capture-*-drift` skills are
symmetric mirrors of each other.

#### Proposed Changes

**Why this is needed:** spec mutations cannot land atomically without an intermediate staging area; the queue holds in-flight proposals so they can be reviewed, modified, and selectively dispositioned rather than applied piecemeal.

Queue of pending proposed-change files that have been authored
but not yet processed by `Revise`. Each file is a structured
markdown document with YAML frontmatter and one or more
`## Proposal:` sections. Populated by `Propose Change` (direct
user authoring), `Critique` (findings promoted from the analytical
pass), `Process Memos` (spec-bound disposition handoff), and
`Capture Spec Drift` (drift findings promoted to proposals).
Drains through `Revise` — after a successful pass, processed
proposals move to the corresponding `history/vNNN/proposed_changes/`
directory paired with revision files documenting the
disposition. Selective per-proposal disposition means the queue
can carry a mix of in-flight work; entries that survive a Revise
pass without being addressed remain pending for the next pass.

#### Specification History

**Why this is needed:** without immutable versioned snapshots, the spec's evolution cannot be audited and there is no way to answer "what did the spec say at version N?" against a current claim.

Versioned, immutable snapshots of the Specification at each
successful Revise pass — `history/vNNN/` directories containing
byte-identical copies of every template-declared spec file as it
stood when revision NNN was finalized. Provides the audit trail
of how the spec evolved over time. Read by `Doctor` for invariant
checks (contiguous-version invariant, version-directories-complete,
etc.). Bounded by an explicit Prune History operation (not
represented on the current diagram but retained in the skill set)
that collapses old `vNNN` directories into a pruned-marker once
they are no longer load-bearing for audit. New entries appear
after every successful Revise — even all-reject Revise passes cut
a new version, preserving the rejection audit trail.

*Implementation side.*

#### Implementation

**Why this is needed:** spec is prescription, but value only flows when something actually realizes it; the implementation is the running, testable, deployable embodiment of the spec's intent.

The actual code, tests, configuration, infrastructure, and
agent-instruction files (CLAUDE.md, AGENTS.md, `.ai/*.md`, etc.)
that realize the spec. Mutates through `Implement` (driven by
Work Items) and via direct edits to agent-instruction files by
`Process Memos` (persistent-knowledge disposition). Read by
`Capture Impl Drift` (current state for gap detection) and
`Capture Spec Drift` (observed truth for spec-drift detection).
The **descriptive** side of the workflow — what actually exists
— in contrast to the Specification's **prescriptive** side of
what should exist. Includes everything that is not the
Specification itself: source code, tests, infrastructure, build
and CI configuration, dev tooling, agent prompts, and any other
artifact the project ships or operates.

#### Work Items

**Why this is needed:** work must be tracked durably between filing and completion; without a queue, items get lost, duplicated against the same gap, or worked out of dependency order with no way to verify closure.

Queue of actionable tasks awaiting `Implement`. Items come from
three sources: `Capture Impl Drift` (gap-tied items with
gap-id markers), `Process Memos` (impl-bound dispositions,
freeform), and `Capture Work Item` (direct user filing,
freeform). Implementation-specific format — beads issues for
`livespec-impl-beads`, JSONL records for `livespec-impl-plaintext`,
GitLab work items for `livespec-impl-gitlab`, etc. — but
uniform external behavior. Closure semantics branch on the
gap-tied vs. freeform distinction: **gap-tied items require
verification** (re-run drift detection, confirm gap-id is gone,
record audit fields including resolution method and verification
timestamp); **freeform items close with a simple reason**. The
1:1 gap-tracking invariant applies only to gap-tied items: every
current gap in the spec MUST correspond to exactly one tracked
work item across all statuses.

#### Memos

**Why this is needed:** captured observations need durable storage between deposit and triage without becoming a permanent store, which would defeat the transient-by-construction discipline and re-introduce the junk-drawer pattern.

Queue of free-text observations awaiting `Process Memos` triage.
Populated by `Capture Memo`. Implementation-specific storage
(the beads memory store, a JSONL log file, etc.) but uniform
external query API via the impl-plugin machine-readable
contract — Doctor queries `--untriaged --json` for hygiene
checks. Memos are **transient by construction**: every memo
must eventually flow to a proposed-change, a work item,
persistent agent knowledge, or discard. Doctor enforces this
with an invariant warning when memos accumulate beyond a
configured hygiene threshold. Replaces the open-ended "memory
store" pattern from tools like `bd remember` — LiveSpec rejects
permanence-by-default because it leads to a junk drawer that
LLMs cannot reliably consume and that erodes the discipline of
the canonical spec and implementation stores.

#### Persistent Agent Knowledge

**Why this is needed:** some long-term knowledge genuinely does not fit as a spec requirement or as inline code, but still needs to load into agent context when its topic is relevant; named topic files with progressive AGENTS.md / CLAUDE.md references solve both the placement problem and the context-window-blowup problem.

Long-term agent knowledge artifacts that do not fit in the spec
(not a requirement) and do not fit as inline code, test, or
config (too generic, too cross-cutting, or too procedural).
Realized as named files under `.ai/<topic>.md` referenced
progressively from AGENTS.md and/or CLAUDE.md, so they load into
agent context only when their topic is relevant to the current
work. Populated by `Process Memos` when a memo is dispositioned
as persistent knowledge. The structural alternative to
memo-as-permanent-store: each entry has a topic, a focused
subject, and an explicit reachability path from agent-instruction
files. Solves both the context-blowup problem (progressive
loading) and the junk-drawer problem (named topics, explicit
graduation step from a memo through user-driven dialogue). Lives
inside the Implementation surface because it is part of how the
implementation is operated and maintained.

## Cross-boundary contracts (the load-bearing red edges)

| # | Direction | Edge | Meaning |
|---|---|---|---|
| 1 | spec → impl | `Specification → Capture Impl Drift` | The prescription. Capture Impl Drift reads the spec to detect what impl is missing. |
| 2 | spec → impl | `Specification → Capture Spec Drift` | Capture Spec Drift compares observed impl against the spec to find spec-side drift. |
| 3 | impl → spec | `Capture Spec Drift → Propose Change` | Drift findings (impl observed correct, spec lagging) feed back as proposals. |
| 4 | impl → spec | `Process Memos → Propose Change` (spec-bound) | Spec-bound memo dispositions become proposals. |
| 5 | impl → spec | `Memos → Doctor` (untriaged) | Doctor reads untriaged-memo inventory for its hygiene invariant check. |

## Pending skill placeholders

### `livespec:next` (spec-side, advisory)

A future spec-side skill — provisionally named `livespec:next` —
will recommend the most logical next workflow action based on the
current state of the persistence stores and the dependencies between
operations. Purely advisory: it does not mutate any store.

Reads (via the impl-plugin machine-readable contract for impl-side
stores; directly for spec-side stores):

- **Proposed Changes** queue — pending proposals awaiting revise?
- **Specification History** — recency of the last revision; pruning pressure?
- **Work Items** queue — ready leaf items? blocked items? stale items?
- **Memos** queue — untriaged memos, especially past the doctor-enforced hygiene threshold?
- **Doctor** findings — unresolved invariant violations?

Surfaces the most ripe next action — conceptually similar to
`bd ready` but applied to the full spec ↔ implementation lifecycle
rather than just the Work Items queue.

Not yet represented in the diagram. Full design (single recommendation
vs. ranked list, cross-boundary read mechanism, weighting heuristics
across stores) is open for future iteration.

## Open questions for review

- Cross-boundary red arrows take long winding routes around the
  diagram instead of crossing the wall directly. PlantUML routes
  edges around nodes; constrained by the side-by-side layout.
- `spec-bound` and `untriaged` labels sit on the far right edge,
  semantically detached from where the visual arrow turns.
- `List Memos` and `Prune History` still dropped (tangential to
  the spec ↔ impl drift story); re-add if they belong on the
  canonical diagram.
- Vertical stacking was attempted (v4-v7) but the trade-offs
  weren't worth it — see *Layout history*.

## Layout history

The layout has gone through several iterations:

- **v1 (`32edbd5`):** PlantUML deployment with `package`
  containers, `top to bottom direction`. Rendered side-by-side
  (dot won't stack containers vertically when there are
  bidirectional cross-container edges).
- **v2 (`3e83aba`):** Added hidden vertical edges, reverted to
  plain arrows. Still side-by-side.
- **v3 (Mermaid, `dcd6335`):** Switched to Mermaid for
  reliable `flowchart TB` + `subgraph` vertical stacking.
  Reverted — staying on PlantUML.
- **v4 (`e96efb1`):** Flat layout, no outer containers,
  hidden vertical edges + horizontal yellow WALL divider.
  First working vertical stacking, but intra-section layout
  was loose.
- **v5-v6 (unpushed):** Tried `linetype ortho`, aggressive
  hidden edges anchoring the WALL. WALL kept getting pulled
  out of position by visible cross-boundary edges.
- **v7 (`6a0dfbb`):** Added `together { }` blocks. Vertical
  stacking mostly worked, but the WALL rendered as a
  fixed-width rectangle (not a real divider), Capture Impl
  Drift and Capture Memo were pulled above the WALL by
  visible Spec edges, and cross-boundary arrows took long
  winding paths.
- **v8 (this version, `4383ff2`):** Back to `package`
  containers (side-by-side). Reviewer judges container
  grouping cleaner than flat-layout vertical with messy
  positioning. All v7 content improvements kept:
  - Single yellow input box (no User/Agent actor figures)
  - Spec → Capture Spec Drift cross-boundary edge
  - Pure black ArrowColor
  - Explicit dark FontColor on all nodes
  - No bold-markup artifacts
