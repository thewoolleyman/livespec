# Tool-agnostic spec ↔ implementation workflow

The spec ↔ implementation workflow uses domain terminology not
bound to LiveSpec, `/livespec:*` skill names, or any specific
implementation plugin. The shape described here is the load-bearing
conceptual model; the LiveSpec-specific instantiation is described
in [`livespec-architecture.md`](./livespec-architecture.md).

The diagram at
[`../workflow-processes/diagrams/tool-agnostic-workflow.svg`](../workflow-processes/diagrams/tool-agnostic-workflow.svg)
renders this workflow visually.

## Glossary

Terms used throughout this document. Some terms have meanings
here that differ from generic usage.

**Change** (or **proposed change**) — A structured proposal to
modify the Specification. Lives in the Proposed Changes queue
until processed by Revise. Authored directly via Propose Change,
or promoted from Critique findings, Process Memos (spec-bound
disposition), or Capture Spec Drift findings. One authoring
action MAY produce multiple proposals atomically. Processed
proposed-changes relocate from the Proposed Changes queue into
Specification History (paired with a revision file documenting
the disposition); they do not accumulate in Proposed Changes,
which holds only pending items.

**Closure** — The act of marking a work item as done. Performed
by Implement as the final step of its work cycle. The procedure
depends on the item's origin and the disposition:

- **Gap-tied fix**: requires verification — re-run gap detection
  via the Spec Reader, confirm the gap is gone, record audit
  fields (resolution method, verification timestamp, commits,
  files changed). If the gap remains, closure MUST NOT proceed
  as a fix.
- **Freeform fix**: close with a simple reason; no verification
  step required.
- **Non-fix closure** (gap-tied or freeform): administrative
  closures where work will not be done or was resolved
  out-of-band (e.g., `wontfix`, `duplicate`, `spec-revised`,
  `no-longer-applicable`, `resolved-out-of-band`). Close with a
  reason describing the disposition; no verification, no audit
  fields.

**Critique** — A spec-side LLM-driven analytical pass that
observes the Specification in isolation and surfaces findings
about spec quality (contradictions, undefined terms, dangling
references, BCP14-keyword issues, prose quality). Findings MAY
promote to proposed changes. Critique does NOT compare spec
against implementation; that direction is Capture Spec Drift's
job.

**Cross-boundary contract** — A deliberate, audited handoff
between the spec side and the implementation side. The hard wall
between sides means these edges are the only sanctioned spec ↔
implementation relationship; everything else stays inside its own
side.

**Disposition** — A user's per-item routing decision during a
triage operation. Most notably in Process Memos, where each memo
is dispositioned as spec-bound, impl-bound, persistent-knowledge,
or discard.

**Doctor** — Spec-side hygiene and invariant check. Two layers:
a static phase (mechanical structural checks) and an LLM-driven
phase (spec-quality findings). Also enforces cross-cutting
invariants such as memo hygiene by querying impl-side stores
through the published machine-readable contract.

**Drift** — Evolutionary lag in the spec: the implementation has
done something load-bearing that the spec does not yet describe.
The asymmetric counterpart to **gap** on the impl side. Detection
is heuristic and LLM-driven — the impl side has no enumerable
rule set the way the spec does. Drift findings close via routing
to Propose Change.

**Freeform (work item)** — A work item with no gap-id marker;
its existence is not tied to a detected spec gap. Comes from
Capture Work Item (direct user filing) or Process Memos
(impl-bound disposition). Closes with a simple `--reason` text;
no verification step required.

**Gap** — A deficit in the implementation: something the spec
prescribes that the implementation does not yet reflect. The
asymmetric counterpart to **drift** on the spec side. Detection
is mechanical (enumerate spec rules; check impl for each). Each
detected gap corresponds to exactly one tracked work item across
all statuses — the 1:1 gap-tracking invariant — and is marked
with a `gap-id:gap-NNNN` label on the resulting gap-tied work
item. Closure requires verifying the gap is no longer detected.

**Gap-tied (work item)** — A work item carrying a gap-id marker,
derived from automated detection by Capture Impl Gaps. Its
existence is justified by a specific spec rule the impl does not
yet satisfy. Closure requires verification (re-run detection;
confirm gap-id absent) plus audit fields. Participates in the
1:1 gap-tracking invariant.

**History** (or **Specification History**) — Versioned, immutable
snapshots of the Specification at each successful Revise pass.
Each snapshot lives in a `history/vNNN/` directory containing
byte-identical copies of every template-declared spec file plus
the processed proposed-change files (with revision files
documenting each disposition) that produced that version. History
is therefore the complete audit trail of how each version was
reached, not just a snapshot store. Items only enter (via
Revise); they never become pending and never drain except via
Prune History.

**Implementation** — The actual code, tests, configuration, and
infrastructure that realize the spec — what actually exists, in
contrast to what the spec says should exist. Distinct from
**Persistent Agent Knowledge**, which is the separate store for
long-term agent guidance.

**Implementation plugin** (or **impl plugin**) — A concrete
realizer of the implementation-side contract published by the
spec-side core. Each plugin owns its own storage backend
(in-repo files, embedded database, third-party tracker, etc.)
but exposes the same skill surface and the same machine-readable
contract surface.

**Intent** — Incoming change pressure that drives spec or
implementation work: an initial seed, an observation, a
requirement change, a bug report, an external constraint, a
refactor pressure. The Specification is itself the ratified
accumulated form of intent; the term "intent" refers to incoming
pressure that has not yet been ratified.

**Load-bearing** — Describes a piece of structure — a rule, a
contract, an artifact, an invariant — on which other parts of
the workflow depend. Removing or altering a load-bearing element
causes downstream breakage; incidental elements can be changed
freely.

**Memo** — A transient free-text observation captured for later
triage. Lives in the Memos queue/archive — items get a
disposition state marker on processing and remain in the store
for audit. Captured via Capture Memo and processed via Process
Memos. **Transient by construction**: every memo MUST eventually
flow to a proposed change (spec-bound), a work item (impl-bound),
persistent agent knowledge, or discard. Doctor enforces a hygiene
threshold to prevent unprocessed memo accumulation.

**Persistent agent knowledge** — Long-term agent knowledge in
whatever form the implementation chooses to store it. Common
forms: harness instruction files (e.g., CLAUDE.md, AGENTS.md,
`.ai/<topic>.md` files referenced progressively from those
harness files); a long-lived memory store queried by the agent at
relevant points; or any other mechanism a plugin opts into. The
landing place for memos that graduate via the persistent-knowledge
disposition in Process Memos.

**Proposed change** — See **Change**.

**Queue/archive** — A box in the workflow that holds a collection
of discrete items with lifecycle state. Items enter, change state
through processing, and either leave the box (toward another
destination) or remain with a state marker. Four exist in the
workflow: Proposed Changes (pure queue — processed items relocate
to Specification History via Revise), Specification History (pure
archive — versions accumulate without a pending state), Work
Items (queue + archive — closed items remain with a status
marker), Memos (queue + archive — dispositioned items remain
with a disposition marker). Doctor's hygiene invariants target
the pending-item subset (the queue role); the archived portion
is unbounded except by Prune.

**Revise** — The spec-side skill that processes pending proposed
changes, applies accept / modify / reject decisions per proposal
in dialogue with the user, and cuts a new Specification History
snapshot (`vNNN`). Selective per-proposal — the user MAY address
a subset and leave the rest pending for a future pass.

**Seed** — One-time spec-side skill that bootstraps a new
project's Specification from initial intent. After the Seed
commit lands, all subsequent spec mutations MUST flow through
Propose Change → Revise.

**Spec** — See **Specification**.

**Spec Reader** — A unifying impl-side adapter between the spec
side's canonical artifacts (Specification, Specification History)
and the impl-side operations that consume them. The spec side's
only contract for read access is exposing the canonical file
locations; the Spec Reader is the impl-side construct that reads
those locations and presents spec content to other impl-side
operations. Implementation-dependent in its internals: a plugin
MAY implement it as a thin pass-through (plain-text file reads),
as a richer adapter with caching, indexes, embeddings,
denormalized graphs, RAG-style retrieval, or anything in between.
Excludes Proposed Changes — only ratified canonical content is
exposed (pending proposals are not yet intent).

**Specification** (or **spec**) — The canonical, ratified source
of truth for project intent — what the system MUST / SHOULD / MAY
do or be. Mutates only through the Propose Change → Revise loop
after the initial Seed.

**Store** — A canonical, monolithic accumulation of intent. Three
exist in the workflow: Specification (the spec itself),
Implementation (the realized artifact), Persistent Agent
Knowledge (procedural agent knowledge). Stores have no concept of
discrete items with lifecycle; the artifact IS what it currently
is. Workflow operations mutate stores in place (Revise → Spec,
Implement → Impl, Process Memos persistent-knowledge disposition
→ Persistent Agent Knowledge).

**Verification** — The closure-time step that confirms a gap-tied
work item's underlying gap is actually resolved. Implemented by
re-running Capture Impl Gaps in dry-run mode and checking that
the gap-id is no longer present in the detection output. Does
not apply to freeform work items.

**Work item** — An actionable, tracked task on the implementation
side. Lives in the Work Items queue/archive — closed items remain
with `status:closed` for audit. Awaits processing by Implement.
Comes from three sources: Capture Impl Gaps (gap-tied), Capture
Work Item (freeform direct filing), or Process Memos (impl-bound
disposition, freeform). See **Gap-tied** vs **Freeform** for
closure semantics.

## The spec / implementation split

The workflow is partitioned into a SPEC SIDE and an IMPLEMENTATION
SIDE separated by a hard wall. The split exists because spec
captures *what should be true* and implementation captures *what
is*; treating them as one artifact makes it impossible to verify
the relationship, evolve them at independent paces, or substitute
one implementation for another while keeping intent stable.

Every piece of project state MUST live on one side or the other
— not both, not neither. Memos, work items, and persistent agent
knowledge are anchored on the implementation side because they
describe realization concerns; proposed changes and history are
anchored on the spec side because they describe intent evolution.

Neither side reads the other directly except through the
**cross-boundary contracts** enumerated below. Every cross-boundary
edge is a deliberate, audited handoff rather than an implicit
coupling.

The implementation side is **pluggable**: the spec side publishes
the contract, and any implementation that fulfills it is
interchangeable. The implementation MAY take any form — files in
the repo (markdown, JSONL, YAML, HTML), an embedded database, a
third-party issue tracker, or a hybrid — as long as it satisfies
the published contract obligations.

## External input

A single external entry point admits intent into the workflow.
The arrow from this node goes only to Seed, because every other
skill is invoked from within an already-running project (they are
internal entry points, not external ones, even when a human or
agent triggers them directly). The workflow is not sensitive to
which agent (human or LLM-backed) invokes any operation; actor
identity is not load-bearing.

## Skills

### Spec side

#### Seed

One-time bootstrap of a new project's Specification. Reads the
initial intent and materializes the initial state of the
Specification tree (the template-declared spec files plus a
`v001` History snapshot). Runs once at project birth; after the
Seed commit lands, all subsequent spec mutations MUST flow
through Propose Change → Revise — direct edits to the spec are
forbidden from that point on. Seed is exempt from the pre-step
doctor check (there is no prior state to check) but does run a
post-step check to verify the materialized state is consistent.

#### Propose Change

User-initiated authoring of one or more proposed changes to the
Specification. Accepts either a free-text rough deposit
(lightweight, no structure required) or a full interactive
structured dialogue, producing a proposed-change file in the
Proposed Changes queue. This is the direct path for spec
mutations — invoked when the user or agent knows they want to
change the spec. A single invocation MAY author multiple
proposals atomically in one file with one or more `## Proposal:`
sections (cardinality 1-to-N). Proposed-changes wait in the queue
for a Revise pass to process them.

#### Critique

LLM-driven analytical pass over the Specification — observes the
spec in isolation and surfaces findings about spec quality:
internal contradictions, ambiguities, undefined terms, dangling
references, BCP14-keyword issues, prose-quality concerns. Each
finding MAY promote to a proposed change in the Proposed Changes
queue. Critique deliberately does NOT compare spec against
implementation; that is Capture Spec Drift's job. Cardinality is
1-to-N: one invocation produces many findings, each potentially
becoming its own proposal. Critique does not require prior user
intent — it MAY walk the spec without being told what to look
for.

#### Revise

Processes pending entries in the Proposed Changes queue, applies
accept / modify / reject decisions per proposal in dialogue with
the user, and cuts a new Specification History snapshot (`vNNN`).
Selective per-proposal — the user MAY address a subset and leave
the rest pending for a future pass. Every successful Revise cuts
a new version even when every decision is `reject`, preserving
the rejection audit trail with byte-identical spec files. Applies
any `resulting_files` updates from accepted proposals to the
Specification in place before snapshotting.

#### Doctor

Health and invariant check across the Specification, the Proposed
Changes queue, and the Specification History. Also queries
impl-side stores (notably the Memos queue) via the machine-readable
impl-plugin contract for cross-cutting hygiene invariants. Runs
in two layers: a static phase that mechanically detects structural
failures (file shape, schema conformance, anchor reference
resolution, contiguous-version invariant), and an LLM-driven phase
that surfaces findings about spec quality and inter-store hygiene.
Memo hygiene — "no untriaged memo MUST remain unresolved beyond
N days" — is one such invariant; Doctor does not know how memos
get resolved (that is the impl plugin's responsibility), only
that they should be. Invokes as a pre-step and post-step around
every other spec-side skill (except Seed pre-step, which has no
prior state to check).

### Implementation side

#### Capture Impl Gaps

Detects implementation gaps where the spec prescribes something
the implementation does not yet reflect. Reads spec content via
the Spec Reader (and uses its version query to detect what has
changed since this skill's own last-checked marker; the marker
is internal state of the impl plugin). Walks the spec and the
impl, runs gap-detection predicates, and per detected gap files
an appropriately labeled, categorized work item into the Work
Items queue (with per-gap user consent). Work items it creates
carry a `gap-id:gap-NNNN` label tying them back to the originating
gap, which makes closure verifiable: re-running this skill in
dry-run mode and confirming the gap-id is no longer detected is
the verification step. Detection state is ephemeral and in-memory
— there is no persistent intermediate artifact. Each
implementation plugin defines its own predicate set and storage
backend.

#### Capture Spec Drift

Detects impl-to-spec drift — places where the implementation has
done something that looks load-bearing but is not reflected in
the spec. Reads spec content via the Spec Reader (using its
history + diff capabilities to anchor "what should this version
of impl correspond to in the spec?") and the impl directly, runs
LLM-driven analytical detection, and per finding (with user
consent) routes to Propose Change to create a proposal that
updates the spec.

Asymmetric counterpart to Capture Impl Gaps, not a mirror image:
the two directions have categorically different detection
characteristics, and the asymmetric `gap` / `drift` naming
reflects that. Spec → impl is mechanically tractable (enumerate
spec rules, check impl for each); impl → spec is heuristic and
fuzzy (every line of impl is "doing something"; signal-to-noise
is brutal). The two MUST be separate skills rather than one
bidirectional skill because merging would hide the reliability
gap between mechanical and LLM-driven detection.

#### Capture Work Item

User-initiated direct path to file a work item, bypassing both
gap detection and memo ceremony. Invoked when the user is certain
the work is impl-bound, well-formed, and ready to track. Items
it creates are **freeform**: they carry no gap-id marker, do not
participate in the 1:1 gap-tracking invariant, and close via the
freeform path (simple `--reason` text, no verification step).
Necessary for everyday workflows like filing a discrete bug,
queuing a refactor, or capturing a tactical cleanup task that
does not trace back to any spec rule.

#### Implement

Generic work-item processor — pulls items from the Work Items
queue (typically leaf-level, no blockers), drives a Red → Green
code cycle (a failing test first, then the implementation that
turns it green), and closes the item. Reads spec content via the
Spec Reader when a work item references spec rules (work items
frequently anchor on spec sections, so resolving that context is
part of normal execution). Agnostic to the work item's origin
(gap-tied from Capture Impl Gaps, impl-bound from Process Memos,
or freeform from Capture Work Item).

Branches on closure based on (a) the gap-id marker (gap-tied vs
freeform) and (b) the disposition (fix vs non-fix):

- **Gap-tied fix**: re-run Capture Impl Gaps in dry-run, confirm
  the gap-id is no longer detected, record audit fields
  (resolution method, verification timestamp, commits, files
  changed).
- **Freeform fix**: close with `--reason`; no verification step.
- **Non-fix closure** (regardless of origin — e.g., the spec was
  revised and the gap is now obsolete, the item is a duplicate,
  the work won't be done, the issue was resolved out-of-band):
  close with a reason describing the administrative disposition;
  no verification, no audit fields.

#### Capture Memo

Low-friction free-text deposit of an in-flight observation that
the user or agent is not yet ready to classify as spec-bound,
impl-bound, or persistent agent knowledge. Writes the memo into
the Memos queue for later triage via Process Memos. Memos are
transient by construction: every memo MUST eventually flow to a
proposed change, a work item, persistent agent knowledge, or
discard. Memo is not a permanent store; Doctor enforces this with
an invariant warning when memos accumulate beyond a configured
hygiene threshold.

#### Process Memos

Per-memo handholding skill that walks pending memos and disposes
each via user dialogue. Reads spec content via the Spec Reader
to inform the spec-bound vs impl-bound disposition decision
(without spec context, "does this memo's content correspond to a
spec rule or to implementation territory?" cannot be answered).

Four dispositions:

1. **Spec-bound** — routes to Propose Change (cross-boundary
   handoff into the spec-side workflow).
2. **Impl-bound** — files a freeform work item into Work Items.
3. **Persistent agent knowledge** — graduates the memo into the
   Persistent Agent Knowledge store (the specific form is
   implementation-dependent).
4. **Discard** — marks the memo discarded (state marker; the
   memo remains in the archive with no follow-on artifact).

The handholding principle is load-bearing: users do not manually
invoke Propose Change for spec-bound memos; Process Memos drives
them through the appropriate downstream skill. Doctor's hygiene
warning about untriaged memos points to Process Memos as the
resolution mechanism. Process Memos is the only operation whose
disposition cascades into multiple downstream destinations; every
other processor (Revise, Implement) drains a queue into exactly
one canonical store.

## Impl-side API: Spec Reader

A unifying access layer between the spec side's canonical
artifacts (Specification, Specification History) and the impl-side
operations that consume them. The spec side's only contract for
read access is exposing the canonical file locations; the Spec
Reader is the impl-side construct that reads those locations and
presents spec content to other impl-side operations.
Implementation-dependent in its internals.

**Required capabilities:**

1. Read the current Specification directly.
2. Read the Specification History directly.
3. Report the current spec version (`vNNN`).
4. Read or summarize differences between specified versions.

**Consumed by:** Capture Impl Gaps (gap-rule enumeration; also
uses the version query to detect what has changed since its own
last-checked marker), Capture Spec Drift (comparison baseline),
Implement (work-item context resolution), Process Memos
(spec-bound vs impl-bound disposition decisions). MAY be consumed
by other impl-side operations as needed.

Excludes Proposed Changes — only ratified canonical content is
exposed (pending proposals are not yet intent).

## Stores and queue/archives

### Spec side

#### Specification (store)

The canonical, ratified source of truth for the project's intent
— what the system MUST / SHOULD / MAY do or be. Typically a tree
of markdown files (`spec.md`, `contracts.md`, `constraints.md`,
`scenarios.md`, `non-functional-requirements.md`, `README.md`)
at a known root resolved via `.livespec.jsonc`. Mutates only
through the Propose Change → Revise loop after the initial Seed;
direct edits are forbidden from the Seed commit onward. Read by
Capture Impl Gaps (as the rule source), Capture Spec Drift (for
the comparison baseline), Critique (for analysis), and Doctor
(for invariant checks).

When the Specification and the Implementation disagree, the side
that is correct depends on the situation — the impl MAY have a
gap relative to the spec, or the spec MAY have drifted from
observed-correct impl — which is why Capture Impl Gaps and
Capture Spec Drift are asymmetric counterparts handling
structurally different problems rather than symmetric mirrors.

#### Proposed Changes (queue/archive — pure queue)

Holds pending proposed-change files that have been authored but
not yet processed by Revise. Each file is a structured markdown
document with YAML frontmatter and one or more `## Proposal:`
sections. Populated by Propose Change (direct user authoring),
Critique (findings promoted from the analytical pass), Process
Memos (spec-bound disposition handoff), and Capture Spec Drift
(drift findings promoted to proposals). Drains through Revise —
after a successful pass, processed proposals (whether accepted,
modified, or rejected) relocate to the corresponding
`history/vNNN/proposed_changes/` directory paired with revision
files documenting the disposition. So Proposed Changes holds only
currently-pending items; completed items leave the box entirely
and live in Specification History as part of the audit trail.
Selective per-proposal disposition means the queue MAY carry a
mix of in-flight work; entries that survive a Revise pass without
being addressed remain pending for the next pass.

#### Specification History (queue/archive — pure archive)

Versioned, immutable snapshots of the Specification at each
successful Revise pass — `history/vNNN/` directories containing
byte-identical copies of every template-declared spec file as it
stood when revision NNN was finalized. Each `vNNN/` also receives
the processed proposed-change files (with paired revision files
documenting each disposition) that produced that version, so
Specification History is the complete audit trail of how each
version was reached, not just a snapshot store. Read by Doctor
for invariant checks (contiguous-version invariant,
version-directories-complete). Items only enter (via Revise);
they never become pending and never drain — bounded only by an
explicit Prune History operation that collapses old `vNNN`
directories into a pruned-marker once they are no longer
load-bearing for audit. New entries appear after every successful
Revise — even all-reject Revise passes cut a new version,
preserving the rejection audit trail.

### Implementation side

#### Implementation (store)

The actual code, tests, configuration, and infrastructure that
realize the spec. Mutates through Implement (driven by Work
Items). Read by Capture Impl Gaps (current state for gap
detection) and Capture Spec Drift (observed truth for spec-drift
detection). Includes everything that is not the Specification
itself and is not Persistent Agent Knowledge: source code, tests,
infrastructure, build and CI configuration, dev tooling, and any
other artifact the project ships or operates.

#### Work Items (queue/archive — queue + archive)

Holds actionable tasks awaiting Implement, plus closed items that
remain with `status:closed` (or equivalent) marker for audit.
Items come from three sources: Capture Impl Gaps (gap-tied items
with gap-id markers), Process Memos (impl-bound dispositions,
freeform), and Capture Work Item (direct user filing, freeform).
Implementation-specific format and storage backend, but uniform
external behavior. Closure semantics branch on (a) gap-tied vs
freeform origin and (b) fix vs non-fix disposition (see
**Closure** in the glossary).

The 1:1 gap-tracking invariant applies only to gap-tied items:
every current gap in the spec MUST correspond to exactly one
tracked work item across all statuses (regardless of how it
closed).

#### Memos (queue/archive — queue + archive)

Holds pending free-text observations awaiting Process Memos
triage, plus dispositioned items that remain with a disposition
marker for audit (spec-bound, impl-bound, persistent-knowledge,
discarded). Populated by Capture Memo. Implementation-specific
storage but uniform external query API via the impl-plugin
machine-readable contract — Doctor queries the untriaged inventory
for hygiene checks.

Memos are transient by construction: every memo MUST eventually
flow to a proposed change, a work item, persistent agent
knowledge, or discard. The transient rule constrains the *queue*
role, not the archive role (processed memos remain visible).
Doctor enforces this with an invariant warning when unprocessed
memos accumulate beyond a configured hygiene threshold.

#### Persistent Agent Knowledge (store)

Long-term agent knowledge that does not fit in the spec (not a
requirement) and does not fit as inline code, test, or config
(too generic, too cross-cutting, or too procedural). The specific
form is implementation-dependent: common realizations include
harness instruction files (e.g., CLAUDE.md, AGENTS.md,
`.ai/<topic>.md` files referenced progressively from those harness
files); a long-lived memory store the agent queries at relevant
points; or any other mechanism the plugin opts into. Populated
by Process Memos when a memo is dispositioned as persistent
knowledge. Each entry is named, retrievable, and graduated
explicitly via user-driven dialogue, which avoids the
junk-drawer pattern. In file-based realizations, progressively-
loaded references also bound context-window growth (only relevant
topics load into agent context).

A separate first-class store, distinct from Implementation —
both live on the impl side, but they hold different categories
of artifact and are mutated by different operations.

## Cross-boundary contracts

The hard wall between SPEC SIDE and IMPLEMENTATION SIDE means
that all spec ↔ implementation interaction MUST flow through one
of five enumerated cross-boundary edges.

| # | Direction | Edge | Meaning |
|---|---|---|---|
| 1 | spec → impl | Specification → Spec Reader | Canonical spec content flows to the impl-side Spec Reader, which consumes it on behalf of all impl-side operations that need spec access. |
| 2 | spec → impl | Specification History → Spec Reader | Versioned snapshots + audit trail flow to Spec Reader, enabling version-aware spec reads and inter-version diff queries. |
| 3 | impl → spec | Capture Spec Drift → Propose Change | Drift findings (impl observed correct, spec lagging) feed back as proposals. |
| 4 | impl → spec | Process Memos → Propose Change (spec-bound) | Spec-bound memo dispositions become proposals. |
| 5 | impl → spec | Memos → Doctor (untriaged) | Doctor reads untriaged-memo inventory for its hygiene invariant check. |

## Reserved skills

### Next-action advisor (spec-side, advisory)

A reserved spec-side skill — provisionally surfaced as
`/livespec:next` in the LiveSpec instantiation — will recommend
the most logical next workflow action based on the current state
of the persistence stores and the dependencies between operations.
Purely advisory: it does not mutate any store.

Reads (via the impl-plugin machine-readable contract for impl-side
stores; directly for spec-side stores):

- **Proposed Changes** queue — pending proposals awaiting Revise?
- **Specification History** — recency of the last revision;
  pruning pressure?
- **Work Items** queue — ready leaf items? Blocked items? Stale
  items?
- **Memos** queue — untriaged memos, especially past the
  Doctor-enforced hygiene threshold?
- **Doctor** findings — unresolved invariant violations?

Surfaces the most ripe next action, applied to the full spec ↔
implementation lifecycle rather than just the Work Items queue.
