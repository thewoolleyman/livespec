---
topic: recast-layer3-standalone-orchestrate-plugin
author: claude-opus-4-8
created_at: 2026-05-29T10:28:28Z
---

Recast Layer 3 from a livespec-resident project-local skill into an
OPTIONAL, independently-distributed, opt-in orchestration **plugin** that
any livespec-governed project MAY install — single-repo or multi-repo
ecosystem — and that depends only on the published cross-plugin contract
surface plus project configuration. This makes cross-side orchestration
generically applicable across topologies and impl backends, fixes the
dead-end Layer 3 discoverability nudge, and reconciles a contracts.md ↔
spec.md naming contradiction. The implementation (extracting the existing
resident skill into the new plugin) is deliberately out of scope for this
propose-change; see the prerequisite reference in Proposal 2.

## Proposal: recast-layer-3-to-optional-standalone-orchestration-plugin

### Target specification files

- SPECIFICATION/spec.md

### Summary

Recast the "Layer 3 — Cross-repo orchestration (livespec-resident)" bullet
and the "Cross-side composition belongs at Layer 3" paragraph in
§"Three-layer orchestration architecture" so Layer 3 is provided by an
OPTIONAL, independently-distributed, opt-in orchestration plugin that a
livespec-governed project MAY install, rather than a project-local skill
resident only in the `livespec` repository. The orchestrator MUST depend
solely on the published cross-plugin contract surface (spec-side `next`,
each active impl-plugin's `next`, and the thin-transport query skills) plus
project configuration; it MUST NOT read impl-side stores directly nor
hardcode any specific repository's paths.

### Motivation

The current livespec-resident framing (adopted v089) ties the single Layer 3
driver to the `livespec` repository and forbids downstream consumers from
carrying one. Two consequences follow. First, the published `/livespec:next`
Layer 3 discoverability nudge points every downstream / dogfooding consumer
at a driver that — by this same spec — they can never have: a dead-end
pointer (addressed by Proposal 4). Second, single-project adopters and
non-livespec-family ecosystems get no cross-side orchestration at all.

v089 correctly withdrew the per-repo, copier-shipped driver because it was
dead architecture — a template stub that was never invoked and that nobody
maintained. A standalone, independently-versioned, opt-in PLUGIN is a
fundamentally different distribution model that addresses exactly why the
per-repo instance failed (it becomes a real, maintained, installable
artifact) while preserving the §"Cross-side composition exclusion"
invariant: the bottleneck-sensitive weighting lives in the dedicated
orchestration plugin — the orchestration layer — and is opt-in, so neither
livespec-core nor any impl plugin bakes a weighting into the published
Layer 2 surface. A consumer who does not install the orchestrator simply
uses the raw `next` skills with no imposed cross-side weighting.

### Proposed Changes

1. Replace the bullet currently reading "**Layer 3 — Cross-repo
   orchestration (livespec-resident).** The `livespec` repository MUST carry
   a project-local orchestration driver at
   `.claude/skills/livespec-orchestrate/SKILL.md`. … The composition is local
   to the livespec family, not to each repo in it." with a recast bullet:
   "**Layer 3 — Cross-repo orchestration (optional standalone plugin).**
   Cross-side orchestration is provided by an OPTIONAL,
   independently-distributed orchestration plugin that a livespec-governed
   project MAY install opt-in. The orchestrator composes Layer 2 primitives —
   invoking the spec-side `next` and each active impl-plugin's `next` to
   produce a unified cross-side ranking; dispatching to the appropriate
   heavyweight skill for the chosen action; running the project's janitor as
   a hard gate; emitting a structured iteration journal; looping until the
   queue drains or the configured budget exhausts. The orchestrator MUST
   depend only on the published cross-plugin contract surface plus project
   configuration; it MUST NOT read impl-side stores directly nor hardcode any
   specific repository's paths. It MUST be applicable to both single-repo
   projects (where the 'ecosystem' is the one repo and cross-repo machinery
   no-ops) and multi-repo ecosystems (where a configured manifest enumerates
   the member repos), and to any conformant impl backend. No repository is
   REQUIRED to carry a Layer 3 driver; the livespec family itself installs the
   orchestrator opt-in like any other consumer."
2. Update the following "Cross-side composition belongs at Layer 3"
   paragraph so its cross-references describe the optional orchestration
   plugin (replacing "livespec's Layer 3 driver at
   `.claude/skills/livespec-orchestrate/SKILL.md`" and any "the project's
   Layer 3 driver" phrasing), and so the discoverability-nudge cross-reference
   is consistent with the recast nudge contract (Proposal 4). The doctrinal
   exclusion (Layer 2 MUST NOT bake in a weighting) is unchanged and remains
   the reason the weighting lives in the opt-in orchestration plugin rather
   than in any Layer 2 primitive.

## Proposal: recast-nfr-orchestration-layer-and-required-shape-backend-agnostic

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Recast §"Cross-repo orchestration layer (livespec-resident)" and §"Layer 3
loop driver — required shape and discipline" so they describe the optional
standalone orchestration plugin and state the required shape in
backend-agnostic, topology-agnostic terms. Drop the "livespec MUST carry …
impl repos MUST NOT carry their own" mandate in favor of "any project MAY
install the orchestrator plugin opt-in." Restate the required-shape
discipline (mode, budget, janitor-as-hard-gate, structured iteration
journal) so that cross-repo state aggregation flows through the published
query contract (NOT impl-store internals); the janitor command, integration
branch, repo manifest, and worktree/isolation strategy are supplied by
project configuration; and dispatch is derived from the published `next`
output as `<emitting-plugin>:<action> <work-item-ref|target>`.

### Motivation

The current section ties the driver to `livespec` and reaches into a specific
impl's store reducer plus a hardcoded family repo list, which prevents the
orchestrator from generalizing to single-repo projects, to other ecosystems,
or to other impl backends (e.g. beads, gitlab). Stating the discipline
against the published contract + configuration makes the orchestrator
portable by construction, which is the prerequisite for extracting it into a
standalone plugin.

### Proposed Changes

1. Rename §"Cross-repo orchestration layer (livespec-resident)" to
   §"Cross-repo orchestration layer (optional standalone plugin)" and recast
   its body: the orchestrator is an optional, independently-versioned plugin
   a project MAY install; no repository is required to carry it; it depends
   only on the published contract surface plus project configuration; it MUST
   NOT hardcode family-specific paths or read impl-side stores directly. Drop
   the copier-template and per-repo-mandate withdrawal language as obsolete
   under the plugin model.
2. In §"Layer 3 loop driver — required shape and discipline", drop the "in
   the `livespec` repository / No other repo in the livespec family carries a
   Layer 3 driver" framing. Keep the mode-parameter, budget-parameter,
   janitor-as-hard-gate, and structured-iteration-journal requirements, but
   restate them backend-agnostically: (a) cross-repo / cross-side state MUST
   be obtained via the published query contract (`next`, `list-work-items`,
   `list-memos`), never by reading an impl plugin's store format directly;
   (b) the janitor command, the integration branch, the ecosystem repo
   manifest, and the worktree / isolation strategy MUST be supplied by project
   configuration rather than hardcoded; (c) dispatch MUST be derived from the
   published `next` output as `<emitting-plugin>:<action>
   <work-item-ref|target>`.
3. **Prerequisite reference (tracked separately — NOT specified here).** Add
   a note to the recast section recording that, before the existing
   livespec-resident orchestrate skill is extracted into the standalone
   orchestration plugin, ALL of its references to transient Claude Code
   auto-memory MUST first be inlined into governed artifacts (skill prose,
   this SPECIFICATION, and existing doctor invariants / hooks) so the
   extracted plugin is fully self-contained. This self-containment cleanup is
   an INDEPENDENT problem, is a PREREQUISITE to extraction, and is tracked
   under a SEPARATE propose-change. It is referenced here only to record the
   ordering dependency; its mechanism (including ecosystem-wide enforcement
   that forbids saving transient memories) is out of scope for this
   propose-change.

## Proposal: make-cross-plugin-contract-support-external-orchestration

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Make explicit two properties of the existing cross-plugin contract that an
external (out-of-repo) orchestrator depends on, WITHOUT adding any new fields
to the `next` output — preserving the thin-transport skills' cohesion:
(a) each candidate's `action` value is a dispatchable verb in the emitting
plugin's own published skill surface, so an orchestrator dispatches
`<plugin>:<action> <work-item-ref|target>` with no out-of-band mapping;
(b) the thin-transport query skills (`next`, `list-work-items`,
`list-memos`) MUST accept a `--project-root <path>` flag so an orchestrator
can query any repository's state through the published wrapper rather than
reading the store directly.

### Motivation

An orchestrator distributed as a separate plugin cannot reach into impl-store
internals and cannot assume it runs inside the target repository. It needs
(a) to turn a ranked candidate into an invocation deterministically and
(b) to query sibling repos' state through the contract. (a) is already true
for the spec-side `action` enum (its values are the `/livespec:<action>`
skill names) and for the impl surface; this finding makes the property
normative rather than incidental, and guarantees forward-compatible graceful
degradation (an orchestrator skips an `action` verb it does not recognize).
(b) is already satisfied by the spec-side and impl-side `next` wrappers (both
accept `--project-root`); this finding extends the same flag symmetrically to
the remaining required query skills so the whole machine-query surface is
uniformly addressable across repositories. Neither change adds an output
field; `next` stays a pure thin-transport ranker.

### Proposed Changes

1. In §"Output schema" (and the parallel impl-`next` bullet under the
   impl-plugin required-skill surface), add: each candidate's `action` MUST
   name a dispatchable skill in the emitting plugin's published surface (spec
   side: the existing `action` enum corresponds to `/livespec:<action>`; impl
   side: each `action` value MUST correspond to a skill the impl plugin
   publishes), so a consumer MAY dispatch `<plugin>:<action>
   <work-item-ref|target>` without any out-of-band action→skill mapping.
   `action: "none"` is the sole non-dispatchable value and signals "no ripe
   work." This adds NO output field; it constrains the meaning of the existing
   `action` field.
2. In the §"Thin-transport skills … required machine query surface"
   descriptions for `next`, `list-work-items`, and `list-memos`, require each
   to accept `--project-root <path>` (default `Path.cwd()`) with identical
   semantics to the spec-side `next` `--project-root`, so an external
   orchestrator can address any repository's state through the published
   wrapper. This is an INPUT flag only; it MUST NOT change any output schema.

## Proposal: recast-layer-3-discoverability-nudge-to-gate-on-orchestrator-reachability

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/spec.md

### Summary

Recast the §"Layer 3 discoverability nudge" requirement so the
`/livespec:next` nudge fires only when the orchestration plugin is actually
installed / reachable from the current project, and reconcile the naming
contradiction between contracts.md (which calls the driver "project-local"
and cross-references a nonexistent spec.md subsection "Layer 3 —
Project-local composition") and spec.md (whose heading is "Layer 3 —
Cross-repo orchestration (livespec-resident)").

### Motivation

Under the current contract the nudge fires on every direct `/livespec:next`
invocation and points the user at a Layer 3 driver that — pre-recast — only
the `livespec` repo carries, and that — post-recast — is an optional plugin a
given project may not have installed. In both cases an unconditional nudge is
a dead-end pointer for any consumer lacking the driver. Gating the nudge on
the orchestrator's reachability makes it actionable: surface it only when the
orchestration plugin is present; otherwise stay silent (or, at most, point at
how to obtain the optional orchestrator). Separately, contracts.md §"Layer 3
discoverability nudge" cross-references a spec.md subsection titled "Layer 3 —
Project-local composition" that does not exist (spec.md's heading is
"…(livespec-resident)"), and labels the driver "project-local" while spec.md
labels it "livespec-resident"; the recast must converge both on the new
"optional standalone plugin" framing and remove the dangling cross-reference.

### Proposed Changes

1. In §"Layer 3 discoverability nudge", change the requirement so the nudge is
   surfaced only when the orchestration plugin is installed / reachable from
   the current project; when it is absent, `/livespec:next` MUST NOT emit a
   dead-end nudge (it MAY, at most, point the user at how to obtain the
   optional orchestrator). Preserve the existing skip-when-invoked-by-another-
   skill clause and the wrapper-stays-thin-transport clause.
2. Replace the "project-local Layer 3 loop driver per `spec.md`
   §"Three-layer orchestration architecture" → "Layer 3 — Project-local
   composition"" phrasing with a reference to the recast spec.md bullet
   "Layer 3 — Cross-repo orchestration (optional standalone plugin)", and
   remove the dangling subsection cross-reference. Reconcile "project-local"
   vs "livespec-resident" wording to the new "optional standalone plugin"
   framing throughout the affected contracts.md references (including
   §"Cross-plugin invocation" and §"Cross-boundary handoffs" if they still
   describe "livespec's Layer 3 loop driver").
