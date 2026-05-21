---
topic: declare-livespec-dev-tooling-shared-code-mechanism
author: claude-opus-4-7
created_at: 2026-05-21T04:13:46Z
---

## Proposal: Shared code sync — livespec-dev-tooling library

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Adds a new top-level section `## Shared code sync — livespec-dev-tooling` to `contracts.md`, sibling to `## Shared content sync — copier template`. The new section declares `livespec-dev-tooling` as the canonical mechanism for delivering shared executable code (notably the enforcement-suite checks) to every livespec-governed project, distinct from copier (which remains the mechanism for shared static scaffolds). Codifies the canonical repo, the consumption contract (Python package via `uv` git source; composite Actions and reusable workflows via `uses:` references), the shared-vs-private partition principle for enforcement-suite checks, and the pin-and-bump applicability.

### Motivation

The 2026-05-20 `just bootstrap` failure in `livespec-impl-plaintext` is the most visible symptom of a broader structural gap: `contracts.md` §"Shared content sync — copier template" names `copier` as the *sole* shared-content mechanism, but copier cannot deliver executable code — only static scaffolds. The 39 scripts under `livespec-core/dev-tooling/checks/` are referenced by the impl-plugin template's `justfile` but never actually delivered to consumers; every consumer either (a) re-implements the checks (drift), (b) silently misses them (rot), or (c) hits a bootstrap failure when the template's `justfile` references a missing script. Epic `li-fgqgnk` resolves this by extracting `dev-tooling/checks/` into a livespec-governed sibling library, `livespec-dev-tooling`. This propose-change (Phase G.1 of the epic) is the spec-side amendment that establishes the new sibling's place in the contract surface; subsequent phases (G.2–G.7) author the repo, migrate the scripts, and rewire consumers.

### Proposed Changes

Insert a new section, `## Shared code sync — livespec-dev-tooling`, immediately AFTER the existing `## Shared content sync — copier template` section in `SPECIFICATION/contracts.md`. The new section MUST establish the following:

1. **Mechanism.** The shared-code sync mechanism between `livespec` and every livespec-governed consumer (`livespec`-core itself, every `livespec-impl-*` plugin, and any future sibling library or application) is `livespec-dev-tooling`: a versioned Python package and a set of GitHub composite Actions plus reusable workflows, both published from `github.com/thewoolleyman/livespec-dev-tooling`. The mechanism is sibling-and-complementary to `copier` (which remains the shared-SCAFFOLD mechanism per §"Shared content sync — copier template"); `copier` MUST NOT deliver executable Python or shell code, and `livespec-dev-tooling` MUST NOT deliver static scaffolds.

2. **Repository governance.** `livespec-dev-tooling` MUST be governed by livespec via its own seeded `SPECIFICATION/` tree (the `livespec` 4-file template plus `non-functional-requirements.md`) and MUST track its own work via the active `livespec-impl-*` plugin per `.livespec.jsonc` (currently `livespec-impl-plaintext`). The sibling library MUST declare a `compat` block pinning its `livespec_core` semver range identically to how every `livespec-impl-*` consumer declares pins (cf. §"Cross-repo coordination — pin-and-bump").

3. **Consumption contract.** Consumers MUST consume `livespec-dev-tooling` via two parallel surfaces:
   - **Python package** — added to `pyproject.toml` `[dependency-groups].dev` via `[tool.uv.sources]` declaring a `git = "..."` plus `tag = "vX.Y.Z"`. Invocation MUST take the form `uv run python -m livespec_dev_tooling.checks.<slug>`. PyPI publishing is NOT required in v1; the uv git-source path is sufficient.
   - **Composite Actions and reusable workflows** — invoked via `uses: thewoolleyman/livespec-dev-tooling/.github/actions/<name>@vX.Y.Z` and `uses: thewoolleyman/livespec-dev-tooling/.github/workflows/<name>.yml@vX.Y.Z` from each consumer's `.github/workflows/ci.yml`.

4. **Shared-vs-private partition.** Enforcement-suite checks that ship in `livespec-dev-tooling` MUST be those whose intent and CLI surface are stable across every livespec-governed project (e.g., style gates, coverage-pairing gates, AST gates, CI-alignment gates, red-green-replay gates). Checks whose intent is specific to `livespec-core` itself (e.g., checks asserting properties of the `templates/impl-plugin/` scaffold; checks asserting schema/dataclass pairing in `livespec-core`'s own package layout) MUST remain `livespec-core`-private and MUST NOT migrate. The canonical partition list MUST live in `livespec-dev-tooling`'s own `contracts.md` and is established by a subsequent propose-change cycle against that spec (Phase G.4 of `li-fgqgnk`).

5. **Stability surface.** `livespec-dev-tooling` MUST declare a semver-stable CLI surface: each check's argv contract, exit-code semantics (0 = pass; non-zero = fail with structured stderr), and `python -m` invocation slug MUST NOT change without a MAJOR version bump. Composite-action and reusable-workflow input/output contracts are subject to the same rule. Implementation internals (function signatures, module structure inside `livespec_dev_tooling/`) MAY change at any version increment.

6. **Constraint inheritance.** `livespec-dev-tooling` MUST NOT perform network I/O from any check; MUST target Python 3.10+ exclusively (matching `livespec-core`'s floor); MUST NOT take a runtime dependency on `livespec` itself (the library is consumed by `livespec`, not the other way around); MUST follow the comment, type, and coverage disciplines codified in `livespec`'s `non-functional-requirements.md` §"Linter rule set", §"Typechecker rule set", and §"Coverage gate".

No other section in `contracts.md` requires deletion under this finding; the existing `## Shared content sync — copier template` section remains valid in scope (it now governs only static scaffolds, as the new section's first bullet explicitly states).

## Proposal: Generalize pin-and-bump to sibling libraries

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Amends `contracts.md` §"Cross-repo coordination — pin-and-bump" to generalize the pin-and-bump mechanism from `livespec` ↔ `livespec-impl-*` plugins ONLY to `livespec` ↔ every sibling livespec-governed repository, explicitly including sibling libraries such as `livespec-dev-tooling`. The mechanism, the `compat` block schema, the bump-pin PR shape, and the additive-breaking-change rule remain unchanged in substance; only the consumer enumeration widens.

### Motivation

Phase G.1 of `li-fgqgnk` introduces `livespec-dev-tooling` as a livespec-governed sibling library — neither an impl-plugin nor a consumer application. The existing pin-and-bump prose names `livespec-impl-*` consumers exclusively, which leaves the new library's relationship to `livespec` semver-undefined. The library's `.livespec.jsonc` MUST carry a `compat` block identically to every impl-plugin consumer, so the cleanest amendment is to generalize the section's consumer enumeration rather than introduce a parallel mechanism. This finding is a structural prerequisite for Finding 1 above: that finding's bullet (2) cross-references this section.

### Proposed Changes

Amend the opening paragraph and surrounding prose of `## Cross-repo coordination — pin-and-bump` in `SPECIFICATION/contracts.md` per the following:

- Every reference to "`livespec-impl-*` plugins" or "the active impl plugin" that names the *type* of consumer (as opposed to specifying impl-plugin-specific behavior such as the 9-skill surface) MUST be generalized to "every livespec-governed sibling consumer (impl-plugins AND sibling libraries such as `livespec-dev-tooling`)".
- The two required `compat` fields (`livespec` semver range; `pinned` release tag) and their placement ("on the active impl plugin's top-level section") MUST be generalized to "on each consumer's top-level section keyed by consumer name" — i.e., a `livespec-dev-tooling` consumer's `compat` block lives under a `livespec-dev-tooling` top-level key in its own `.livespec.jsonc`, structurally identical to how `livespec-impl-plaintext` declares its block today.
- The illustrative `.livespec.jsonc` example block MUST be retained as an *impl-plugin* example (the existing shape is correct for that case). A second illustrative block MAY be added showing the same `compat` shape under a sibling-library key, but is OPTIONAL.
- The "bump-pin PR" shape and the "additive-breaking-change" rule (old contract surface MUST stay valid for one or more releases; consumers migrate at their own cadence) MUST apply identically to sibling libraries — no special-casing.
- The doctor `contract-version-compatibility` invariant currently described downstream of this section MUST be understood to apply to every consumer's `compat` block, not just impl-plugins'. No re-wording of the doctor invariant text is required under this finding; the generalization is by implication once the consumer enumeration widens.

No new sub-headings under this section are required; the changes are prose-level.

## Proposal: Provenance acknowledges livespec-dev-tooling as a sibling source

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Amends `non-functional-requirements.md` §"Shared content provenance" to acknowledge `livespec-dev-tooling` as a parallel sibling provenance source alongside `copier`. The current text designates `copier` as the sole provenance channel for non-functional requirements flowing into every `livespec-impl-*` repo; this finding extends the text so that requirements expressed *as executable enforcement-suite code* flow via `livespec-dev-tooling` rather than via `copier`, while requirements expressed *as static scaffolding* continue to flow via `copier`.

### Motivation

Phase G.1 of `li-fgqgnk` partitions livespec's shared content into two channels: static scaffolds (copier) and executable enforcement-suite code (`livespec-dev-tooling`). The non-functional-requirements provenance section currently names only copier as the flow mechanism, which leaves the new code-channel's provenance silently undefined. This finding closes that gap so the provenance contract matches the contracts.md amendments in Findings 1 and 2.

### Proposed Changes

Amend the existing paragraph(s) of `#### Shared content provenance` in `SPECIFICATION/non-functional-requirements.md` per the following:

- The current sentence asserting that all enumerated non-functional requirements MUST flow into every `livespec-impl-*` repo via the `copier` template MUST be retained for those requirements whose expression is static scaffolding (`justfile`, `lefthook.yml`, `.mise.toml`, `pyproject.toml` skeletons, `.github/workflows/` scaffolds, the starter `.claude/skills/loop/SKILL.md`, etc.).
- A parallel sentence MUST be added asserting that non-functional requirements whose expression is *executable enforcement-suite code* — notably the checks under `dev-tooling/checks/` that mechanically enforce style, coverage, AST shape, CI alignment, and red-green-replay discipline — flow via `livespec-dev-tooling` per `contracts.md` §"Shared code sync — livespec-dev-tooling".
- The drift-detection sentence (currently asserting that drift MUST surface via CI's `copier update --dry-run` check or via the doctor's contract-version-compatibility invariant) MUST be retained AND extended: drift in `livespec-dev-tooling`-delivered code MUST surface via the same `contract-version-compatibility` invariant reading the consumer's `compat` block (cf. `contracts.md` §"Cross-repo coordination — pin-and-bump"), since the library's pin lives in the same `compat` mechanism as the impl-plugin's.
- The orchestration-layer sentence (currently asserting that every `livespec-impl-*` repo inherits a starter `.claude/skills/loop/SKILL.md` from the copier template) MUST be retained unchanged — the loop skill remains a static-scaffold concern and stays in the copier channel.

No other sections of `non-functional-requirements.md` require amendment under this finding; the cross-reference in the body to `contracts.md` §"Shared content sync — copier template" remains valid as a pointer to that specific section even after Finding 1 adds the sibling §"Shared code sync — livespec-dev-tooling" section.
