---
topic: orchestrator-naming-convention
author: claude-opus-4-8
created_at: 2026-06-21T04:37:59Z
---

## Proposal: Redefine the orchestrator-plugin repo-naming convention to livespec-orchestrator-<ledger>[-<loop>] and sweep all core-spec prose

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/contracts.md

### Summary

The normative orchestrator-plugin repo-naming convention is currently `livespec-impl-<X>`, where `X` is the tracking mechanism (the ledger). This proposal redefines it to `livespec-orchestrator-<ledger>[-<loop>]`, which MUST name BOTH the ledger axis and an OPTIONAL loop axis, because a loop driver is ledger-portable: one loop (e.g. Fabro's parallel-sandbox loop) MAY run over multiple ledgers, so the loop MUST be nameable rather than implied by the ledger. The two reference orchestrators are renamed across all core-spec prose accordingly: `livespec-impl-beads` -> `livespec-orchestrator-beads-fabro` (Beads/Dolt ledger, Fabro parallel loop) and `livespec-impl-git-jsonl` -> `livespec-orchestrator-git-jsonl` (git-jsonl ledger, homegrown serial loop; the ledger alone is unambiguous, so no `<loop>` segment). This is a COMPREHENSIVE prose rename: every forward-looking `livespec-impl-*` glob, `livespec-impl-<X>` notation, concrete reference-orchestrator name, and "impl-plugin"/"implementation plugin" CLASS-LABEL reference in the two non-frozen contributor-facing spec files is renamed. The core repo `livespec` KEEPS its name and is explicitly NOT subject to the convention (the `livespec` -> `livespec-core` rename was retired per `history/v068`). Three categories are deliberately KEPT verbatim: the literal `templates/impl-plugin/` copier-directory PATH token (renaming the directory is a separate copier-channel migration; the string must still resolve); the `.livespec.jsonc` `implementation.plugin` KEY name (a separate Phase-2 config contract); and historical incident citations (the `livespec-impl-plaintext` PR #26 2026-05-26 incident — historical record).

### Motivation

Slice livespec-4moata.4.2 of the contract re-steering realization epic; root S2 of the rename wave, which gates the git-jsonl and beads rename arms. The `impl-` prefix names only the ledger/tracking axis and cannot express the loop driver, which is a separate, portable axis: Fabro is loop-portable across ledgers, so a Beads-ledger repo running Fabro and a hypothetical git-jsonl-ledger repo running Fabro would collide under a ledger-only name. Naming both axes (`<ledger>[-<loop>]`) disambiguates while keeping the common single-loop case terse (the serial git-jsonl reference needs no loop segment). The maintainer ratified expanding this from the minimal naming-rule slice to a comprehensive core-spec prose rename so that nothing forward-looking retains `impl-`: leaving scattered `livespec-impl-*` references after redefining the convention would create exactly the drift the spec warns against. This is normative CORE spec text, so the redefinition flows through the propose-change / revise loop, with the revise ratification maintainer-owned.

### Proposed Changes

A comprehensive prose rename across the two non-frozen contributor-facing spec files. No `## ` (H2) heading is added, removed, or renamed anywhere (verified: the `## ` heading set of both files is byte-identical before and after; `tests/heading-coverage.json` tracks only H2 and is therefore untouched — NO co-edit). One H3 retitle in non-functional-requirements.md (`### Implementation plugin ecosystem` -> `### Orchestrator plugin ecosystem`), which is not tracked by heading-coverage.

**RENAME rules applied (per the maintainer's classification):**

- `livespec-impl-*` glob / `livespec-impl-<X>` notation -> `livespec-orchestrator-*` / `livespec-orchestrator-<ledger>[-<loop>]`.
- Concrete `livespec-impl-beads` -> `livespec-orchestrator-beads-fabro`; `livespec-impl-git-jsonl` -> `livespec-orchestrator-git-jsonl` (contract leads reality).
- "impl-plugin" / "implementation plugin" CLASS-LABEL terminology -> "orchestrator plugin" / "orchestrator-plugin" where it is clearly the class concept (consistent with the `### Implementation plugin ecosystem` -> `### Orchestrator plugin ecosystem` H3 retitle).

**KEEP rules applied (NOT changed):**

- The literal `templates/impl-plugin/` PATH token wherever it names the copier directory (renaming the dir is a separate copier-channel migration; the string must still resolve). Only the surrounding glob/class nouns were reworded, never the path token.
- The `.livespec.jsonc` `implementation.plugin` KEY name (separate Phase-2 contract).
- Historical incident citations (the `livespec-impl-plaintext` PR #26 2026-05-26 reference) — verbatim.
- `impl-side` / `spec ↔ impl` adjudication terminology (the implementation-side concept, not the naming pattern).

**Edit 1 — `SPECIFICATION/non-functional-requirements.md`.** The `### Implementation plugin ecosystem` section is retitled `### Orchestrator plugin ecosystem` and its three paragraphs redefine the convention (full `livespec-orchestrator-<ledger>[-<loop>]` definition naming both axes, the two reference-orchestrator renames, and the explicit `livespec` core-name exemption). The remaining forward-looking `livespec-impl-*` glob / `livespec-impl-<X>` notation / concrete-name / class-label references throughout the file — in §"Boundary", §"Shared content provenance", the Codex-dogfooding sections, §"Toolchain pins" (the `bd` entry), §"CI telemetry export", §"Orchestrator contract delegation", §"Shared content sync — copier template", §"Shared code sync — livespec-dev-tooling", §"Prose conventions" (the version-prefix example), §"Workflow discipline — spec-side changes" (the commit-refuse-hook + bootstrap + CI-merge-gate family-wide rules), and the fleet-manifest section (repo-class enum label + per-orchestrator beads-tenant pointer) — are all renamed per the RENAME rules, while every `templates/impl-plugin/` path token and the `livespec-impl-plaintext` PR #26 citation are KEPT verbatim.

**Edit 2 — `SPECIFICATION/contracts.md`.** §"Interactive dialogue ownership (orchestrator-side)" (the concrete beads front-end name), §"Doctor cross-boundary invariants" (the `primary-checkout-commit-refuse-hook-installed`, `copier-template-workflow-coverage`, and `wiring-completeness-cross-repo` glob/class references), §"Plugin distribution" (the `.claude/settings.json` example block + the substitute-your-orchestrator prose), §"Driver-shipped hooks" (the two hooks' "active impl-plugin" class labels), and §"CLI end-to-end harness contract" (the "impl-plugin marketplaces" class label) are all renamed per the RENAME rules. The `implementation.plugin` config key and `impl-side ranking` concept term are KEPT.

The full post-edit bodies of both files are carried in this revise pass's `resulting_files[]` payload (spec-target-relative `non-functional-requirements.md` and `contracts.md`).
