# Multi-repo architecture for pluggable implementation providers

**Date captured:** 2026-05-10
**Status:** Open exploration. Not yet formalized in `SPECIFICATION/`.
**Related artifacts:**
- Bug investigation that surfaced this discussion: anthropics/claude-code [#57737](https://github.com/anthropics/claude-code/issues/57737) (project-local plugin slash commands don't register)
- Spec section currently describing the implementation layer:
  `SPECIFICATION/non-functional-requirements.md` v058 §"Repo-local
  implementation workflow" (assumes a single project-local plugin
  named `livespec-implementation`)

## Context — why this conversation happened

The current livespec implementation layer lives at
`.claude/plugins/livespec-implementation/` per the v058 spec. It
uses beads as the issue tracker. While debugging a Claude Code
bug that prevented project-local plugins from exposing their
slash commands, the maintainer raised a broader architectural
intent: eventually there should be MULTIPLE implementation
provider variants — one based on beads (the current one), one
based on Gas City, one based on KilroyRoy / dark factory.

This implies a topology where livespec's "implementation
provider" is a pluggable choice per livespec-using project, not
a hard-coded single workflow. The conversation explored what
that topology looks like and surfaced a concern about
circular dependencies between repos.

## Proposed topology

```
livespec-core (this repo, eventually renamed)
├── ships:    spec-lifecycle plugin
│             (skills: seed, propose-change, revise, critique,
│             doctor, prune-history, help)
├── defines:  spec contract
│             (SPECIFICATION/ tree shape, history/,
│             proposed_changes/, etc.)
└── defines:  implementation-provider contract
              (what any pluggable implementation plugin must
              expose: skill names, file shapes, invariants)

livespec-impl-beads (new repo)
├── depends on: livespec-core's contracts (read-only consumer)
├── ships:      refresh-gaps, plan, implement skills (beads-backed)
└── conforms:   implementation-provider contract

livespec-impl-gascity (future repo)
├── depends on: livespec-core's contracts
└── ships:      same skill surface, Gas City backend

livespec-impl-kilroy (future repo)
└── ships:      same skill surface, dark-factory / KilroyRoy backend
```

Each provider variant ships its own repo with its own
SPECIFICATION/ (dogfooded the same way livespec-core dogfoods
itself), its own release cadence, and its own version history.
A livespec-using project picks ONE provider variant and installs
it alongside livespec-core.

## On the "circular dependency" concern

The maintainer's intuition: if both repos always run from
*published* versions, there's no problem. **This is correct.**

Two flavors that look similar but are different:

**Code dependency** is acyclic: `livespec-impl-beads` depends
on `livespec-core` (it reads core's spec format). `livespec-core`
does NOT depend on `livespec-impl-beads` (it can be used
standalone with no implementation provider at all). Acyclic
graph.

**Workflow dependency (dogfooding)** looks circular but isn't:
when developing `livespec-core`, the maintainer uses an installed
`livespec-impl-beads` to track implementation work. When
developing `livespec-impl-beads`, the maintainer uses an installed
`livespec-impl-beads` (their own published version) to track
THAT repo's implementation work. The "circle" only exists if you
imagine using *unreleased source* of one repo to develop the
other; in practice each development cycle pulls in a *previously
published artifact*, not source. Identical to the GCC bootstrap
pattern.

The only real failure mode: a breaking change to `livespec-core`'s
contract simultaneously breaks every `livespec-impl-*` AND those
plugins are needed to develop the fix. Mitigation: cut breaking
changes on a feature branch, keep developing using a
still-working OLD version of the impl plugin, ship core first,
then update impl plugins to match, ship those.

## What this requires `livespec-core` to add

The biggest new thing is the **implementation-provider contract**.
Today, the implementation layer is described in
`non-functional-requirements.md` as a specific beads-based
workflow. To support multiple variants, we'd need to:

1. **Abstract the contract:** "an implementation provider MUST
   expose three skills with names `refresh-gaps`, `plan`,
   `implement`; MUST honor the spec-mutation rule (read-only on
   `SPECIFICATION/`); MUST produce
   `implementation-gaps/current.json` against the schema; MAY
   use any backend tracker (beads, Gas City, KilroyRoy, ...)."
2. **Move beads-specific details out:** they live in the
   `livespec-impl-beads` repo's spec, not in `livespec-core`.
   Core only knows about the abstract contract.
3. **Document how to plug in a variant:** how a contributor
   selects which provider repo to install for a given
   livespec-using project.

This is a substantial amendment to the v058 spec — likely a
multi-themed `/livespec:propose-change` cycle. NOT done yet.

## Genuine concerns worth thinking through

1. **Per-project provider selection.** A project using livespec
   needs to declare WHICH implementation provider it uses (so
   contributors install the right one). Where does this live?
   Probably `.livespec.jsonc` (already exists at the project
   root) gains an `implementation_provider` field, e.g.:
   ```jsonc
   {
     "template": "livespec",
     "implementation_provider": "livespec-impl-beads"
   }
   ```
   Documented in livespec-core's getting-started docs.

2. **Skill name collisions.** All variants ship `/refresh-gaps`,
   `/plan`, `/implement`. If a contributor accidentally has TWO
   providers installed, namespacing matters. Plugin namespace
   prefix (`/livespec-impl-beads:refresh-gaps` vs
   `/livespec-impl-gascity:refresh-gaps`) handles this — but
   only if the prefix actually surfaces in autocomplete (the bug
   we hit). Until that's fixed, project skills with explicit
   colon-prefixed names (e.g.
   `livespec-implementation-beads:refresh-gaps`) is the
   workable pattern.

3. **Contract evolution.** If `livespec-core` changes the
   gap-report schema in a non-backward-compatible way, every
   provider needs to update. Versioning strategy: probably
   semver in both core and providers, with core's MINOR version
   bumps requiring provider compatibility checks. Implementable
   but real overhead.

4. **Bootstrap / stage 0.** You can't use a `livespec-impl-*`
   plugin to develop the FIRST version of a `livespec-impl-*`
   plugin. The first cycle of any new variant is manual /
   hand-driven. Once the first version ships, subsequent
   development is dogfooded. (Same problem we had during the
   2026-05-09 bootstrap of the current implementation layer —
   manually-driven first iteration, automated thereafter.)

5. **Distribution friction.** Each contributor on a
   livespec-using project needs to install BOTH `livespec-core`
   and the chosen `livespec-impl-*`. Two `/plugin install`
   commands instead of one. Could be smoothed by a
   `livespec-bundle-beads` meta-plugin that depends on both.

6. **Naming conventions.** Several options for
   `livespec-implementation-beads`:
   - `livespec-impl-beads` (short; relationship clear; room for siblings)
   - `livespec-beads` (shortest; relationship implicit)
   - `beads-livespec-impl` (variant first; reads weird)
   - `livespec-tracker-beads` (clarifies what beads does)

   Maintainer leans toward `livespec-impl-beads`; future repos
   would be `livespec-impl-gascity`, `livespec-impl-kilroy`, etc.

7. **Spec layout for the implementation plugin itself.**
   Today, the v058 spec mandates the project-local plugin tree
   under `.claude/plugins/livespec-implementation/`. When this
   moves to its own repo, that section is either deleted (it's
   the impl repo's concern, not core's) or rewritten as the
   abstract provider contract. Either way, propose-change
   territory.

## Immediate-term decision (2026-05-10)

While the multi-repo split is being deferred (substantial work,
needs to wait for both Anthropic to fix project-local plugin
slash commands AND for spec amendments), the maintainer chose a
short-term unblocker:

**Move the current implementation skills from a project-local
plugin to PROJECT SKILLS** at `.claude/skills/<name>/SKILL.md`,
with names prefixed `livespec-implementation-beads:` (with a
colon delimiter inside the skill name itself).

Project skills:
- Auto-load for any contributor working in the project, no
  plugin install or `extraKnownMarketplaces` wiring required.
- Empirically tested 2026-05-10: colons in skill directory
  names work; `/livespec-implementation-beads:refresh-gaps`
  surfaces in autocomplete as expected.
- The colon prefix in the name foreshadows the eventual plugin
  namespace (when the multi-repo split happens, the same
  prefix becomes the actual plugin namespace).

This unblocks usage today without precluding the future
multi-repo split.

## Things to sit with before formalizing the multi-repo split

The maintainer has not yet decided to do the multi-repo split.
Open questions:

- Is the variant-multiplexing intent firm (beads + Gas City +
  KilroyRoy)? Or is beads-only plausible long-term?
- Who is `livespec-core`'s consumer base — broader adoption, or
  primarily the maintainer's own work? Answer shapes how heavy
  a provider abstraction is worth.
- Where does `livespec-impl-beads`'s own spec live — its own
  repo's `SPECIFICATION/` (recursive dogfooding) or shared
  somewhere?
- Should `livespec-bundle-*` meta-plugins exist to smooth
  distribution friction?

These don't need answers to do the immediate-term unblocker;
they do need answers before the multi-repo split is formalized
into `SPECIFICATION/`.
