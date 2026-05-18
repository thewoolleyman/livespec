---
topic: multi-repo-distribution-and-coordination
author: claude-opus-4-7
created_at: 2026-05-18T17:14:42Z
---

## Proposal: Multi-repo plugin ecosystem and rename livespec → livespec-core

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Replace the single-plugin distribution model with a multi-repo plugin ecosystem in which a `livespec-core` plugin (renamed from `livespec`) owns the spec lifecycle and a separate sibling `livespec-impl-<X>` plugin owns the implementation workflow. Consumer projects install `livespec-core` plus exactly one `livespec-impl-*` plugin. `livespec-impl-plaintext` is the immediate dogfood target; `livespec-impl-beads`, `livespec-impl-gitlab`, and other variants are catalog-recognized but deferred. The current `.claude/plugins/livespec-implementation/` project-local model is retired in favor of a published sibling repo, and the canonical detailed contract for each `livespec-impl-*` plugin lives in that plugin's OWN `SPECIFICATION/` (this spec only describes the cross-plugin envelope).

### Motivation

The pluggable-implementation intent recorded in `research/architecture/multi-repo-implementation-providers.md` and the architecture decisions in `research/workflow-processes/architecture-summary.html` (Decisions 1 and 2) require independent repos for CI isolation, agent context isolation, and independent release cadence. The single-plugin model conflates spec lifecycle with one specific implementation. Renaming the existing plugin to `livespec-core` is conventional plugin-ecosystem hygiene (unambiguous when paired with N implementation siblings) and is a stable v1 contract change that cannot wait for the multi-repo split itself to land. The 2026-05-18 research revisions narrowed the immediate scope to `livespec-impl-plaintext` as the dogfood target; other variants remain in the catalog but their detailed contracts are out of scope for this proposal.

### Proposed Changes

In `SPECIFICATION/contracts.md` §"Plugin distribution":

- The marketplace catalog at `.claude-plugin/marketplace.json` MUST list the `livespec-core` plugin (the rename of the current `livespec` plugin). The plugin and marketplace names share the value `livespec-core` by deliberate choice; both names remain stable v1 contracts and renaming either MUST flow through a propose-change cycle.
- End-user install path MUST be documented as: `/plugin marketplace add thewoolleyman/livespec-core` followed by `/plugin install livespec-core@livespec-core`. The GitHub repository SHOULD be renamed from `thewoolleyman/livespec` to `thewoolleyman/livespec-core` as part of this proposal's adoption so that the repo name, marketplace name, and plugin name all share the same value; GitHub's automatic redirect mechanism preserves access via the old `thewoolleyman/livespec` URL after rename, but the canonical install path MUST use the new name.
- Consumer projects MUST install `livespec-core` plus exactly one `livespec-impl-<X>` plugin (the active implementation choice). The active implementation MUST be declared in `.livespec.jsonc` via a top-level `implementation.plugin` key naming the active plugin. The schema root is `additionalProperties: true`; each plugin owns a top-level section named for the plugin and MUST validate its own section on read and MUST tolerate unknown sections.
- Secrets MUST NOT live in `.livespec.jsonc`. External-tracker implementations needing credentials MUST use a separate credentials channel (environment variables, OS keyring, secret manager).
- The seven currently-shipped slash commands MUST be renamespaced from `/livespec:*` to `/livespec-core:*` (one-for-one rename; behavior unchanged).
- The Daily dogfooding path described in this section MUST remain valid for `livespec-core` development; the `--plugin-dir .` mechanism is unchanged.

In `SPECIFICATION/non-functional-requirements.md` §"Repo-local implementation workflow":

- The entire section MUST be replaced with a new section titled "Implementation plugin ecosystem" that describes the sibling-repo topology: every implementation plugin MUST live in its own repository under the name `livespec-impl-<X>` (where X identifies the tracking mechanism, not the substrate — examples: `livespec-impl-plaintext`, `livespec-impl-beads`, `livespec-impl-gitlab`, `livespec-impl-gascity`, `livespec-impl-darkfactory-kilroy`). Each MUST dogfood its own `SPECIFICATION/` and MUST conform to the implementation-plugin contract published by `livespec-core` (the detailed contract surface is defined by a later propose-change cycle).
- The new section MUST state that `livespec-impl-plaintext` is `livespec-core`'s designated dogfood target and that `livespec-impl-beads` and other catalog variants are deferred from immediate implementation but retained as recognized future variants.
- The section MUST state that `livespec-core` itself MUST NOT depend on any `livespec-impl-*` plugin in its code dependency graph: it MUST be installable standalone (the implementation-side skills are simply unavailable until a consumer installs an impl plugin).

In `SPECIFICATION/non-functional-requirements.md` §"Project-local implementation plugin command surface" and §"Implementation justfile namespace" and §"Implementation-gap report shape" and §"Beads invariants" and §"Gap-tied issue closure verification" (the cluster describing the v058-era beads-based project-local plugin):

- These sections MUST be removed from `livespec-core`'s spec because they describe content that now belongs to each respective `livespec-impl-<X>` plugin's own `SPECIFICATION/` — the generic shape (command surface, justfile namespace, gap-report schema) lives in every impl plugin's spec, while backend-specific invariants (Beads invariants in particular) live only in `livespec-impl-beads`'s own spec. `livespec-impl-plaintext` is the immediate dogfood target whose own `SPECIFICATION/` MUST carry the plaintext-equivalent of these sections; `livespec-impl-beads`'s own spec is deferred until that plugin is actively revived. A one-paragraph stub MUST replace the removed sections in `livespec-core`'s spec, stating: "Each `livespec-impl-<X>` plugin's command surface, justfile namespace, gap-report schema, and backend-specific invariants are defined in that plugin's own `SPECIFICATION/`. `livespec-core` only publishes the abstract implementation-plugin contract envelope, defined by the `implementation-plugin-contract-9-skill-surface` propose-change cycle."

In `SPECIFICATION/non-functional-requirements.md` §"Codex dogfooding compatibility":

- The references to `/livespec-implementation:*` slash commands MUST be updated to reflect the sibling-repo split: the Codex dogfooding adapter MAY map both `/livespec-core:*` (against `livespec-core`'s skills) and `/livespec-impl-<X>:*` (against the active impl plugin's skills) consistently with the multi-repo topology. The detailed mapping table SHOULD be deferred to the impl-plugin-specific spec or to a later refinement.

## Proposal: Pin-and-bump cross-repo coordination via per-plugin compat block in .livespec.jsonc

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Define the cross-repo coordination mechanism between `livespec-core` and its sibling `livespec-impl-*` plugins as pin-and-bump: every consumer project MUST declare which `livespec-core` release tag the active impl plugin is currently pinned against. The pin lives in a per-plugin `compat` block inside `.livespec.jsonc` (Obsidian-style per-plugin compatibility manifest). The active impl plugin's autonomous loop runs against the pinned `livespec-core` release, never against HEAD. When `livespec-core` ships a new release, a bump-pin pull request fires in each consumer project (and in each impl plugin's own repository when relevant), and the migration to the new pinned version is the explicit scope of that PR.

### Motivation

Multi-repo evolution requires explicit coordination between `livespec-core`'s contract changes and each `livespec-impl-*` plugin's migration to those changes. The research consensus in `research/architecture/multi-repo-implementation-providers.md` §"Cross-repo coordination — pin-and-bump" identified this as the GCC-bootstrap pattern operationalized for sibling repos: every development cycle pulls in a previously published artifact, not source, which keeps the workflow dependency acyclic in practice. A third coordinating repo was considered and explicitly rejected at the current solo-maintainer scale. Doctor enforcement of contract-version compatibility (the bridge between this proposal and proposal 3's invariant catalog) closes the loop by surfacing drift as a hard finding rather than silent breakage.

### Proposed Changes

In `SPECIFICATION/contracts.md` (add a new section titled "Cross-repo coordination — pin-and-bump"):

- Every consumer project's `.livespec.jsonc` MUST include a per-plugin `compat` block on the active impl plugin's top-level section, with two required fields: `livespec_core` (a semver range describing supported `livespec-core` versions, e.g., `>=2.0.0,<3.0.0`) and `pinned` (the specific `livespec-core` release tag the consumer currently runs against, e.g., `v2.3.0`).
- The active impl plugin's automation and the consumer project's autonomous workflows MUST run against the pinned `livespec-core` release, NOT against HEAD. Running against HEAD bypasses the audited coordination mechanism and MUST be considered an out-of-contract operation.
- When `livespec-core` ships a new release tag, a bump-pin pull request MAY be opened automatically (auto-merge bot architecture deferred; v1 MAY rely on manual bump-pin PRs). The bump-pin PR's acceptance criterion is that the active impl plugin and the consumer project both continue to pass the post-bump invariant suite.
- Breaking contract changes in `livespec-core` MUST be landed additively: the old contract surface stays valid for one or more releases; impl plugins migrate at their own cadence; only after the active impl plugin's release adopting the new surface ships MAY the old surface be removed in a subsequent `livespec-core` release. This mirrors the Kubernetes CRD multi-version-served pattern and the GCC `N` / `N-1` support window.
- `.livespec.jsonc` MUST NOT carry secrets; the `compat` block contains only non-sensitive version metadata.
- Example `.livespec.jsonc` excerpt (illustrative; the canonical schema lives in `livespec-core`'s JSON Schema fragment):

```jsonc
{
  "template": "livespec",
  "spec_root": "SPECIFICATION",
  "implementation": { "plugin": "livespec-impl-plaintext" },
  "livespec-impl-plaintext": {
    "format": "jsonl",
    "compat": {
      "livespec_core": ">=2.0.0,<3.0.0",
      "pinned": "v2.3.0"
    }
  }
}
```

- A subsequent propose-change cycle defining doctor's expanded invariant catalog MUST include a `contract-version-compatibility` invariant that fires when `livespec_core` semver range OR `pinned` tag drift exceeds the configured threshold; the threshold value itself is out of scope for this proposal.

## Proposal: Copier-based shared content sync between livespec-core and livespec-impl-* repos

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Define the shared-content sync mechanism between `livespec-core` and its sibling `livespec-impl-*` repos as `copier`: `livespec-core/templates/impl-plugin/` is the canonical scaffold for shared non-functional content (justfile, lefthook, mise, ruff/pyright, GitHub Actions workflows, and a starter project-local loop skill). Every `livespec-impl-*` repo MUST be generated from this template via `copier copy` and re-synced via `copier update`; each MUST carry a `.copier-answers.yml` tracking the template version it was last generated from. CI in each impl repo SHOULD run `copier update --dry-run` to surface drift, with `.claude/skills/loop/SKILL.md` explicitly excluded from drift detection because local divergence there is expected by the orchestration-layer design.

### Motivation

Multi-repo distribution surfaces a real cost: non-functional content (TDD workflow, code style, CI conventions, lint rules, Python pins, lefthook setup, starter orchestration skill) lives in multiple plugins and must stay in sync. The research consensus in `research/architecture/multi-repo-implementation-providers.md` §"New concerns surfaced by the brainstorm → Shared content sync" identified `copier` as the 2026-mature Python-native answer for "N sibling repos sharing a generated scaffold with re-sync." Alternatives considered and rejected: `git subtree` (requires monorepo-of-record discipline), `git submodule` (poor edit ergonomics for shared docs), hand-rolled copy-from-source CI scripts (reinvents `copier`), and a third meta-repo (premature at solo-maintainer scale per the same research doc).

### Proposed Changes

In `SPECIFICATION/contracts.md` (add a new section titled "Shared content sync — copier template"):

- `livespec-core` MUST publish a copier template at `templates/impl-plugin/` (project-root-relative) containing the canonical scaffolding every `livespec-impl-*` repo derives from: `justfile`, `lefthook.yml`, `.mise.toml`, `pyproject.toml` (with the ruff/pyright config), `.github/workflows/*.yml`, `.claude-plugin/marketplace.json` and `plugin.json` skeletons, a starter `SPECIFICATION/` skeleton, and a starter `.claude/skills/loop/SKILL.md` orchestration driver.
- Every `livespec-impl-*` repository MUST be generated from this template via `copier copy gh:thewoolleyman/livespec-core/templates/impl-plugin <target> --vcs-ref=<core-release-tag>` and MUST carry a `.copier-answers.yml` at the repo root tracking the template version it was last generated from.
- When `livespec-core`'s `templates/impl-plugin/` changes, each impl repo SHOULD run `copier update` to re-sync; the 3-way merge preserves local divergence where possible and surfaces conflicts as merge markers.
- Each impl repo's CI SHOULD run `copier update --dry-run` and fail or warn on detected drift. `.claude/skills/loop/SKILL.md` MUST be excluded from drift detection because local divergence there is expected by the orchestration-layer design (a later propose-change cycle defines that layer in detail).
- Secrets MUST NOT be templated through `copier`; secret material lives only in environment variables, OS keyring, or a secret manager.

In `SPECIFICATION/non-functional-requirements.md` (under the new §"Implementation plugin ecosystem" section introduced by Finding 1):

- Add a sub-section titled "Shared content provenance" stating that the non-functional requirements documented in this spec (TDD discipline, testing approach, definition of done, contributor toolchain pins, enforcement-suite invocation, code style, CI conventions, lefthook setup, project-local plugin layout where applicable, commit and merge discipline) MUST be authoritative for `livespec-core` AND MUST flow into every `livespec-impl-*` repo via the `copier` template. Drift between `livespec-core`'s requirements and an impl repo's generated content MUST surface either via CI's `copier update --dry-run` check or via the doctor's contract-version-compatibility invariant (defined in a later propose-change cycle).
- The sub-section MUST explicitly note that `.claude/skills/loop/SKILL.md` (the project-local orchestration driver, defined in detail by the `orchestration-layer-and-memo-paradigm` propose-change cycle) is exempt from the drift check because per-project tuning of that skill is expected and load-bearing.
- The sub-section MUST state that `copier` MUST be pinned via `uv` against `pyproject.toml`'s `[dependency-groups.dev]` (consistent with the existing rule that `uv` manages Python and Python packages while `mise` pins only non-Python binaries). The pin MUST be present in every consuming repo's `pyproject.toml` so `uv` resolves a reproducible `copier` version per the existing lock-file discipline.
