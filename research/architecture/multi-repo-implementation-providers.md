# Multi-repo architecture for pluggable implementation providers

**Date captured:** 2026-05-10
**Last updated:** 2026-05-17 (post-elephant brainstorm refresh)
**Status:** Substantially advanced — the architecture brainstorm and
its elephant follow-up settled many of this doc's open questions.
Awaiting formalization into `SPECIFICATION/` via
`/livespec:propose-change` → `/livespec:revise`.
**Related artifacts:**

- Bug investigation that surfaced this discussion: anthropics/claude-code [#57737](https://github.com/anthropics/claude-code/issues/57737) (project-local plugin slash commands don't register)
- Spec section currently describing the implementation layer:
  `SPECIFICATION/non-functional-requirements.md` v058 §"Repo-local
  implementation workflow" (assumes a single project-local plugin
  named `livespec-implementation`)
- Canonical conceptual model of the workflow these plugins
  implement: [`research/workflow-processes/tool-agnostic-workflow.md`](../workflow-processes/tool-agnostic-workflow.md)
- LiveSpec-specific instantiation of that model:
  [`research/workflow-processes/architecture-summary.html`](../workflow-processes/architecture-summary.html)

## Context — why this conversation happened

The current livespec implementation layer lives at
`.claude/plugins/livespec-implementation/` per the v058 spec. It
uses beads as the issue tracker. While debugging a Claude Code
bug that prevented project-local plugins from exposing their
slash commands, the maintainer raised a broader architectural
intent: eventually there should be MULTIPLE implementation
provider variants — one based on beads (the current one), one
based on Gas City, one based on Darkfactory's Kilroy tracker.

This implies a topology where livespec's "implementation
provider" is a pluggable choice per livespec-using project, not
a hard-coded single workflow. The 2026-05-10 conversation
explored what that topology looks like and surfaced concerns
about repo dependencies, contract abstraction, and bootstrap
ordering.

The 2026-05-11 architecture brainstorm (with its multi-day
elephant follow-up) then worked through most of the load-bearing
shape. The plugin catalog is now firm; the implementation
plugin's required skill surface grew from 3 to 6 with the
addition of `capture-spec-drift` (resolving the impl → spec
direction), `capture-work-item` (freeform filing), and the memo
pair (`capture-memo` / `process-memos`). The cross-boundary
contract has acquired the Spec Reader adapter and Persistent
Agent Knowledge as a named first-class store. See the related
artifacts above for the conceptual model and LiveSpec-specific
landings.

## Proposed topology

```
livespec-core (renamed from `livespec`)
├── ships:    spec-lifecycle plugin
│             skills: seed, propose-changes, critique, revise,
│             doctor, prune-history, help (7 skills total)
├── defines:  spec contract
│             (SPECIFICATION/ tree shape, history/vNNN/,
│             proposed_changes/, .livespec.jsonc core schema)
└── defines:  implementation-plugin contract
              (skill surface, Spec Reader required capabilities,
              untriaged-memo machine query, Persistent Agent
              Knowledge conventions, per-plugin .livespec.jsonc
              section ownership)

livespec-impl-plaintext (new repo — LiveSpec's own dogfood)
├── depends on: livespec-core's contracts (read-only consumer)
├── ships:      6 impl skills under /livespec-impl-plaintext:* namespace
│               (md / jsonl / yaml / html backend; format choice in
│                .livespec.jsonc)
└── conforms:   implementation-plugin contract

livespec-impl-beads (new repo — bd-backed alternative)
├── ships:      same skill surface, Dolt-backed beads as the
│               work-item + memo store
└── primary use case: adopters with concurrent multi-contributor
                       profiles (Gas City, etc.)

livespec-impl-gascity, livespec-impl-darkfactory-kilroy,
livespec-impl-gitlab, ... (future repos)
└── ships:      same skill surface, project-specific backend
```

Each provider variant ships its own repo with its own
SPECIFICATION/ (dogfooded the same way livespec-core dogfoods
itself), its own release cadence, and its own version history.
A livespec-using project picks ONE provider variant and installs
it alongside livespec-core via the standard Claude Code
marketplace flow.

### The 6-skill impl surface

The implementation-plugin skill surface settled at six required
skills (post-elephant). Each plugin exposes them under its own
namespace prefix.

| Skill | Purpose |
|---|---|
| `capture-impl-gaps` | Mechanical spec → impl gap detection via the Spec Reader; files gap-tied work items (per-gap user consent). Collapses the old `refresh-gaps` + `plan` pair into one ephemeral-detection skill. |
| `capture-spec-drift` | Heuristic impl → spec drift detection (LLM-driven); routes findings to `/livespec:propose-changes` as a cross-boundary handoff. Asymmetric counterpart to `capture-impl-gaps`; resolves the pre-elephant unresolved direction. |
| `capture-work-item` | Freeform direct filing of an impl-side work item (bugs, refactors, tactical tasks). No gap-id; closes via the freeform path. |
| `implement` | Drives Red → Green for a single work item; verifies gap-tied items via dry-run re-detection; closes. Three closure paths: gap-tied fix (verify + audit), freeform fix (simple reason), non-fix (administrative). |
| `capture-memo` | Low-friction free-text deposit of an in-flight observation. Transient by construction. |
| `process-memos` | Per-memo handholding: spec-bound (→ propose-changes) / impl-bound (→ freeform work item) / persistent-knowledge (→ Persistent Agent Knowledge store) / discard. |

`list-memos` is plugin-discretionary (each plugin MAY expose a
user-facing memo search). The doctor-hygiene contract uses a
separate untriaged-memo machine query that does NOT require a
slash command surface.

## On the "circular dependency" concern

The maintainer's intuition: if both repos always run from
*published* versions, there's no problem. **This is correct.**

Two flavors that look similar but are different:

**Code dependency** is acyclic: every `livespec-impl-*` depends
on `livespec-core` (it reads core's spec format and honors core's
contract). `livespec-core` does NOT depend on any
`livespec-impl-*` (it can be installed standalone with no
implementation plugin — the implementation skills are simply
unavailable until a plugin is chosen). Acyclic graph.

**Workflow dependency (dogfooding)** looks circular but isn't:
when developing `livespec-core`, the maintainer uses an installed
`livespec-impl-*` to track implementation work. When developing
`livespec-impl-plaintext` (livespec's own dogfood), the
maintainer uses an installed `livespec-impl-plaintext` (their
own published version) to track THAT repo's implementation work.
The "circle" only exists if you imagine using *unreleased
source* of one repo to develop the other; in practice each
development cycle pulls in a *previously published artifact*,
not source. Identical to the GCC bootstrap pattern.

The only real failure mode: a breaking change to `livespec-core`'s
contract simultaneously breaks every `livespec-impl-*` AND those
plugins are needed to develop the fix. Mitigation: cut breaking
changes on a feature branch, keep developing using a
still-working OLD version of the impl plugin, ship core first,
then update impl plugins to match, ship those.

## What `livespec-core` must add to its spec

The biggest new thing is the **implementation-plugin contract**,
substantially fleshed out by the post-elephant brainstorm. Today,
the implementation layer is described in
`non-functional-requirements.md` as a specific beads-based
workflow with 3 skills. To support multiple variants under the
post-elephant model, the spec needs:

1. **Abstract the contract.** An implementation plugin MUST:
   - Expose the six skills above under its own `/livespec-impl-*:`
     namespace prefix.
   - Provide a Spec Reader adapter with four required capabilities
     (read current Specification; read Specification History;
     report current spec version `vNNN`; read/diff between
     versions).
   - Expose an untriaged-memo machine query that `/livespec:doctor`
     reads for the memo-hygiene invariant.
   - Honor the Persistent Agent Knowledge conventions for the
     persistent-knowledge memo disposition (form is plugin-
     dependent — file-based plugins use harness instruction files;
     other plugins MAY use a long-lived memory store).
   - Read its OWN top-level section of `.livespec.jsonc`; tolerate
     unknown sections owned by other plugins.
   - Honor the spec-mutation rule: `SPECIFICATION/` is read-only
     from the impl plugin's perspective (it only mutates via
     cross-boundary handoffs into `/livespec:propose-changes`).

2. **Drop the persistent `current.json` artifact.** Detection is
   now ephemeral and in-memory; the old
   `implementation-gaps/current.json` intermediate artifact
   disappears entirely. Each plugin owns its work-item / memo
   storage in whatever backend it chooses.

3. **Move plugin-specific details out of livespec-core's spec.**
   They live in each `livespec-impl-*` repo's own
   `SPECIFICATION/`. Core only describes the abstract contract.

4. **Document plugin selection.** `.livespec.jsonc` gains an
   `implementation.plugin` key naming the active plugin. Each
   plugin owns a top-level section named for the plugin (open
   `additionalProperties: true` at the root). Secrets MUST NOT
   live in `.livespec.jsonc`.

5. **Document the marketplace install flow.** Consumer projects
   run `/plugin install livespec-core@livespec` plus exactly one
   `/plugin install livespec-impl-<choice>@<marketplace>`.

This is a substantial amendment to the v058 spec — likely a
multi-themed `/livespec:propose-change` cycle. NOT done yet.

## Genuine concerns — current status

The 2026-05-10 capture surfaced seven concerns. Five are now
substantially resolved by the brainstorm; two remain open.

1. **Per-project provider selection.** ✓ Resolved —
   `.livespec.jsonc`'s `implementation.plugin` key names the
   active plugin, with per-plugin configuration sections.

2. **Skill name collisions.** ✓ Resolved — every plugin's skills
   live under its own `/livespec-impl-*:` namespace prefix
   (marketplace install path). The earlier Claude Code bug
   blocking namespace surfacing is no longer load-bearing for
   this architecture, since the marketplace install path is the
   sanctioned distribution channel.

3. **Contract evolution.** Still open. Semver in both core and
   providers seems right; what triggers a MINOR vs MAJOR bump in
   the contract surface — and how the doctor invariants react to
   provider-vs-core version skew — is unspecified.

4. **Bootstrap / stage 0.** Still applies. You can't use a
   `livespec-impl-*` plugin to develop the FIRST version of a
   `livespec-impl-*` plugin. The first cycle of any new variant
   is manual / hand-driven. Once the first version ships,
   subsequent development is dogfooded. (Same pattern as the
   2026-05-09 bootstrap of the current implementation layer.)

5. **Distribution friction.** Still applies — each contributor
   needs two `/plugin install` commands. A `livespec-bundle-*`
   meta-plugin pattern could smooth this; deferred decision.

6. **Naming conventions.** ✓ Resolved — pattern is
   `livespec-impl-<tracking-mechanism>` where the mechanism (not
   the substrate) is the differentiator. Catalog: `-plaintext`,
   `-beads`, `-gascity`, `-darkfactory-kilroy`, `-gitlab`, etc.

7. **Spec layout for the implementation plugin itself.** ✓
   Resolved — when the multi-repo split lands, the v058 spec
   section describing the project-local plugin is either deleted
   (it's the impl repo's concern) or rewritten as the abstract
   provider contract. Each `livespec-impl-*` repo dogfoods its
   own `SPECIFICATION/` describing its own internal workings.

## New concerns surfaced by the brainstorm

Issues that did not exist in the 2026-05-10 frame and need to
flow through into the spec amendment:

- **Shared content sync.** Non-functional-requirement sections
  (TDD workflow, code style, CI conventions, lint rules, Python
  pins, lefthook setup) genuinely live in multiple plugins. The
  sync mechanism (subtree / pinned package / generator /
  dedicated meta-repo) is unspecified.
- **livespec stops dogfooding beads.** The Beads weight-pull
  assessment in the architecture-summary settled that LiveSpec
  itself uses `livespec-impl-plaintext` going forward.
  `livespec-impl-beads` remains a first-class implementation for
  adopters with the concurrency profile that justifies Dolt.
  This affects which repo gets seeded first and which contract
  details bake in based on plaintext's quirks.
- **Spec Reader capability surface.** The four required
  capabilities are agreed; richer capabilities (semantic search,
  embedding-based retrieval, denormalized graph reads) are
  unstandardized. Whether the contract enumerates them or leaves
  them as plugin-private extensions is open.
- **Plugin discovery beyond the marketplace.** The marketplace
  provides install; what surface answers "what implementations
  exist? what does each offer?" — a curated catalog, a registry,
  a directory in livespec-core's docs — is unspecified.
- **Schema fragmentation for `.livespec.jsonc`.** Each impl
  plugin publishes its own JSON Schema fragment for its section.
  How those fragments get loaded for IDE validation /
  pre-commit linting is unspecified.

## Superseded: the 2026-05-10 immediate-term decision

The original capture recorded a short-term unblocker: move the
current implementation skills from a project-local plugin to
PROJECT SKILLS at `.claude/skills/<name>/SKILL.md` with names
prefixed `livespec-implementation-beads:`. This worked around the
Claude Code project-local-plugin slash-command bug.

**This is now superseded.** As of v049 the `.claude/skills`
symlink was removed; the marketplace install path
(`/plugin marketplace add thewoolleyman/livespec` +
`/plugin install livespec@livespec`) is the canonical channel.
The colon-prefix naming pattern survives as the namespace
prefix in the final layout, but no longer as a workaround for a
missing feature. The dev-loop alternative — `claude --plugin-dir .`
for live-reload during plugin development — covers the
maintainer-side need.

## Things to sit with before formalizing the multi-repo split

Most of the original "things to sit with" are now settled. What
remains:

- Is `livespec-bundle-*` worth shipping — a meta-plugin that
  installs `livespec-core` plus a specific impl variant in one
  command, smoothing distribution friction? Or is two-step
  install acceptable?
- What's the migration story when a livespec-using project wants
  to switch from one impl variant to another (e.g.,
  `livespec-impl-plaintext` → `livespec-impl-beads` when the team
  grows past single-author)?
- How does the doctor's pre/post-step contract react when the
  active impl plugin is between versions, or absent entirely?

These don't block the multi-repo split itself; they sharpen the
spec amendment that will codify it.
