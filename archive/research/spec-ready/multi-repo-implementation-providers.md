# Multi-repo architecture for pluggable implementation providers

LiveSpec is distributed as a set of plugins across separate
repos. The plugin catalog, marketplace install flow, and
implementation-plugin contract are described in
[`livespec-architecture.md`](./livespec-architecture.md). This
document focuses on the architectural shape of the multi-repo
decision: topology, dependency direction, contract-vs-dogfooding
distinction, and bootstrap considerations.

## Topology

```
livespec-core
├── ships:    spec-lifecycle plugin
│             7 skills: seed, propose-changes, critique, revise,
│             doctor, prune-history, help
├── defines:  spec contract
│             (SPECIFICATION/ tree shape, history/vNNN/,
│             proposed_changes/, .livespec.jsonc core schema)
└── defines:  implementation-plugin contract
              (skill surface, Spec Reader required capabilities,
              untriaged-memo machine query, Persistent Agent
              Knowledge conventions, per-plugin .livespec.jsonc
              section ownership)

livespec-impl-plaintext (LiveSpec's own dogfood)
├── depends on: livespec-core's contracts (read-only consumer)
├── ships:      6 impl skills under /livespec-impl-plaintext:* namespace
│               (md / jsonl / yaml / html backend; format choice in
│                .livespec.jsonc)
└── conforms:   implementation-plugin contract

livespec-impl-beads
├── ships:      same skill surface, Dolt-backed beads as the
│               work-item + memo store
└── primary use case: adopters with concurrent multi-contributor
                       profiles

livespec-impl-gascity, livespec-impl-darkfactory-kilroy,
livespec-impl-gitlab, ...
└── ships:      same skill surface, project-specific backend
```

Each provider variant ships its own repo with its own
`SPECIFICATION/` (dogfooded the same way `livespec-core` dogfoods
itself), its own release cadence, and its own version history.
A LiveSpec-using project picks ONE provider variant and installs
it alongside `livespec-core` via the standard Claude Code
marketplace flow.

## Implementation-plugin skill surface

The implementation-plugin skill surface is six canonical skills.
Each plugin exposes them under its own namespace prefix. The full
skill table is in
[`livespec-architecture.md`](./livespec-architecture.md). At a
glance:

| Skill | Purpose |
|---|---|
| `capture-impl-gaps` | Mechanical spec → impl gap detection via the Spec Reader; files gap-tied work items. |
| `capture-spec-drift` | Heuristic impl → spec drift detection; routes findings to `/livespec:propose-changes` as a cross-boundary handoff. |
| `capture-work-item` | Freeform direct filing of an impl-side work item. |
| `implement` | Drives Red → Green for a single work item; closes via gap-tied fix / freeform fix / non-fix paths. |
| `capture-memo` | Low-friction in-flight observation deposit. |
| `process-memos` | Per-memo handholding with four dispositions (spec-bound / impl-bound / persistent-knowledge / discard). |

`list-memos` is plugin-discretionary. Detection in
`capture-impl-gaps` is ephemeral and in-memory; there is no
persistent intermediate artifact (e.g., no `current.json`).

## Dependency direction

**Code dependency is acyclic.** Every `livespec-impl-*` depends
on `livespec-core` (it reads core's spec format and honors core's
contract). `livespec-core` does NOT depend on any
`livespec-impl-*` — it can be installed standalone with no
implementation plugin (the implementation skills are simply
unavailable until a plugin is chosen).

**Workflow dependency (dogfooding) looks circular but is not.**
When developing `livespec-core`, the maintainer uses an installed
`livespec-impl-*` to track implementation work. When developing
`livespec-impl-plaintext` (LiveSpec's own dogfood), the maintainer
uses an installed `livespec-impl-plaintext` (their own published
version) to track THAT repo's implementation work. The "circle"
only exists if you imagine using *unreleased source* of one repo
to develop the other; in practice each development cycle pulls in
a previously published artifact, not source. Identical to the
GCC bootstrap pattern.

The only real failure mode: a breaking change to
`livespec-core`'s contract simultaneously breaks every
`livespec-impl-*` AND those plugins are needed to develop the fix.
Mitigation: cut breaking changes on a feature branch, keep
developing using a still-working OLD version of the impl plugin,
ship core first, then update impl plugins to match, ship those.

## What `livespec-core`'s contract MUST require of every plugin

The implementation-plugin contract obligates each plugin to:

1. **Expose the six canonical skills** under its own
   `/livespec-impl-*:` namespace prefix.
2. **Provide a Spec Reader adapter** with four required
   capabilities (read current Specification; read Specification
   History; report current spec version `vNNN`; read / diff
   between versions).
3. **Expose an untriaged-memo machine query** that
   `/livespec:doctor` reads for the memo-hygiene invariant.
4. **Honor the Persistent Agent Knowledge conventions** for the
   persistent-knowledge memo disposition. Form is plugin-dependent
   (file-based plugins use harness instruction files; other
   plugins MAY use a long-lived memory store).
5. **Read its OWN top-level section** of `.livespec.jsonc`;
   tolerate unknown sections owned by other plugins.
6. **Honor the spec-mutation rule**: `SPECIFICATION/` is read-only
   from the impl plugin's perspective. It mutates the spec only
   via cross-boundary handoffs into `/livespec:propose-changes`.

Detection state in `capture-impl-gaps` is ephemeral and in-memory.
No persistent intermediate gap-report artifact is required or
allowed.

## Per-project provider selection

`.livespec.jsonc` gains an `implementation.plugin` key naming the
active plugin, plus per-plugin configuration sections. Schema is
open at the root (`additionalProperties: true`) so plugins
extend without central coordination.

```jsonc
{
  "implementation": {
    "plugin": "livespec-impl-plaintext"
  },
  "livespec-impl-plaintext": {
    "format": "md"
  }
}
```

Each plugin MUST validate its own section on read and MUST
tolerate unknown sections. Secrets MUST NOT live in
`.livespec.jsonc`; external-tracker plugins need a separate
credentials channel.

## Plugin distribution mechanics

- **Marketplace install** is the canonical channel.
  `livespec-core` and each `livespec-impl-*` are published as
  Claude Code marketplace plugins. Consumer projects install both
  via `/plugin install`.
- **Skill namespacing** prevents collisions across implementations.
  Every plugin's skills live under its own `/livespec-impl-*:`
  namespace prefix.
- **Live-reload mode** (`claude --plugin-dir .`) is available for
  plugin development.

## Concerns to address before formalizing into SPECIFICATION/

The following concerns are load-bearing for the spec amendment
that codifies this architecture but are not themselves required
to ship the multi-repo split:

- **Shared content sync.** Non-functional-requirement sections
  (TDD workflow, code style, CI conventions, lint rules, Python
  pins, lefthook setup) genuinely live in multiple plugins. The
  sync mechanism (subtree / pinned package / generator /
  dedicated meta-repo) is unspecified.
- **Contract evolution.** Semver in both core and providers seems
  right; what triggers a MINOR vs MAJOR bump in the contract
  surface — and how Doctor invariants react to provider-vs-core
  version skew — is unspecified.
- **Bootstrap / stage 0.** A `livespec-impl-*` plugin cannot be
  used to develop the FIRST version of itself. The first cycle
  of any new variant is manual / hand-driven. Once the first
  version ships, subsequent development is dogfooded.
- **Distribution friction.** Each contributor on a LiveSpec-using
  project needs two `/plugin install` commands. A
  `livespec-bundle-*` meta-plugin pattern could smooth this;
  unspecified whether to ship one.
- **Cross-variant migration.** When a LiveSpec-using project wants
  to switch from one impl variant to another (e.g.,
  `livespec-impl-plaintext` → `livespec-impl-beads` when the team
  grows past single-author), the migration mechanism is
  unspecified.
- **Doctor behavior under version skew.** How the pre/post-step
  Doctor contract reacts when the active impl plugin is between
  versions, or absent entirely, is unspecified.
- **Spec Reader capability extension.** The four required
  capabilities are agreed; richer capabilities (semantic search,
  embedding-based retrieval, denormalized graph reads) are
  unstandardized. Whether the contract enumerates them or leaves
  them as plugin-private extensions is unspecified.
- **Plugin discovery beyond the marketplace.** The marketplace
  provides install; what surface answers "what implementations
  exist? what does each offer?" is unspecified.
- **`.livespec.jsonc` schema fragmentation.** Each impl plugin
  publishes its own JSON Schema fragment for its section. How
  those fragments get loaded for IDE validation / pre-commit
  linting is unspecified.
