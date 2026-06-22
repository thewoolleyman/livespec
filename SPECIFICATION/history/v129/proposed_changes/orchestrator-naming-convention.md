---
topic: orchestrator-naming-convention
author: claude-opus-4-8
created_at: 2026-06-21T04:37:59Z
---

## Proposal: Redefine the orchestrator-plugin repo-naming convention to livespec-orchestrator-<ledger>[-<loop>]

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/contracts.md

### Summary

The normative orchestrator-plugin repo-naming convention is currently `livespec-impl-<X>`, where `X` is the tracking mechanism (the ledger). This proposal redefines it to `livespec-orchestrator-<ledger>[-<loop>]`, which MUST name BOTH the ledger axis and an OPTIONAL loop axis, because a loop driver is ledger-portable: one loop (e.g. Fabro's parallel-sandbox loop) MAY run over multiple ledgers, so the loop MUST be nameable rather than implied by the ledger. The two reference orchestrators are renamed in spec text accordingly: `livespec-impl-beads` -> `livespec-orchestrator-beads-fabro` (Beads/Dolt ledger, Fabro parallel loop) and `livespec-impl-git-jsonl` -> `livespec-orchestrator-git-jsonl` (git-jsonl ledger, homegrown serial loop; the ledger alone is unambiguous, so no `<loop>` segment). The core repo `livespec` KEEPS its name and is explicitly NOT subject to the convention (the `livespec` -> `livespec-core` rename was retired per `history/v068`). The change also updates the one stale `livespec-impl-git-jsonl` version-prefix example token in `non-functional-requirements.md` and the concrete reference-orchestrator example in `contracts.md` §"Plugin distribution" so the published install-contract example matches the new name.

### Motivation

Slice livespec-4moata.4.2 of the contract re-steering realization epic; root S2 of the rename wave, which gates the git-jsonl rename arm. The `impl-` prefix names only the ledger/tracking axis and cannot express the loop driver, which is a separate, portable axis: Fabro is loop-portable across ledgers, so a Beads-ledger repo running Fabro and a hypothetical git-jsonl-ledger repo running Fabro would collide under a ledger-only name. Naming both axes (`<ledger>[-<loop>]`) disambiguates while keeping the common single-loop case terse (the serial git-jsonl reference needs no loop segment). This is normative CORE spec text, so the redefinition MUST flow through the propose-change / revise loop, and the revise ratification is maintainer-owned. Scope is the minimal slice: the naming rule + version-prefix examples in non-functional-requirements.md and the concrete reference-orchestrator examples in contracts.md §"Plugin distribution". The generic `livespec-impl-*` glob class references elsewhere and the `templates/impl-plugin/` copier directory path (a filesystem path) are intentionally OUT of scope for this slice. The two reference-orchestrator repo renames are the downstream beads-tracked arms that depend on this contract landing first.

### Proposed Changes

Three edits across two files. No `## ` (H2) heading is added, removed, or renamed (heading-coverage.json tracks only H2 entries and is untouched). One H3 retitle in non-functional-requirements.md keeps the section name consistent with the new vocabulary; H3 retitles are not tracked by heading-coverage.json.

**Edit 1 — `SPECIFICATION/non-functional-requirements.md`, retitle the H3 and redefine the convention in §"Implementation plugin ecosystem".**

H3 retitle:

```diff
-### Implementation plugin ecosystem
+### Orchestrator plugin ecosystem
```

Convention rule (the section's first paragraph):

```diff
-The implementation workflow lives in a sibling-repo topology distinct from `livespec`. Every implementation plugin MUST live in its own repository under the name `livespec-impl-<X>`, where `X` identifies the tracking mechanism, not the substrate (examples: `livespec-impl-git-jsonl`, `livespec-impl-beads`, `livespec-impl-gitlab`, `livespec-impl-gascity`, `livespec-impl-darkfactory-kilroy`). Each `livespec-impl-*` plugin MUST dogfood its own `SPECIFICATION/`. Cross-boundary conformance is the orchestrator CLI contract published by `livespec` (`contracts.md` §"Orchestrator CLI contract — the three named CLIs"): the orchestrator owns its work-item machinery, and core's contract sees only the three named CLIs.
+The implementation workflow lives in a sibling-repo topology distinct from `livespec`. Every orchestrator plugin MUST live in its own repository under the name `livespec-orchestrator-<ledger>[-<loop>]`, naming BOTH axes that distinguish one orchestrator from another: `<ledger>` identifies the work-item ledger substrate (e.g., `beads`, `git-jsonl`, `gitlab`), and the OPTIONAL `<loop>` segment identifies the loop driver when the ledger admits more than one (e.g., `fabro` for the parallel-sandbox loop). The `<loop>` segment is REQUIRED whenever naming the ledger alone would be ambiguous — a loop is ledger-portable (one loop driver MAY run over multiple ledgers), so a repo carrying a distinct loop MUST name it rather than letting the ledger imply it (examples: `livespec-orchestrator-beads-fabro`, `livespec-orchestrator-git-jsonl`, `livespec-orchestrator-gitlab`). Each `livespec-orchestrator-*` plugin MUST dogfood its own `SPECIFICATION/`. Cross-boundary conformance is the orchestrator CLI contract published by `livespec` (`contracts.md` §"Orchestrator CLI contract — the three named CLIs"): the orchestrator owns its work-item machinery, and core's contract sees only the three named CLIs.
```

Reference-orchestrator paragraph:

```diff
-`livespec-impl-beads` backs the parallel-capable Beads/Dolt + Fabro reference orchestrator that the livespec family itself dogfoods; the serial git-jsonl reference orchestrator carries the existing homegrown orchestration logic (see `spec.md` §"Contract + reference implementations architecture" for both). Other catalog variants (`livespec-impl-gitlab`, `livespec-impl-gascity`, `livespec-impl-darkfactory-kilroy`) are deferred from immediate implementation but retained as recognized future variants.
+`livespec-orchestrator-beads-fabro` backs the parallel-capable Beads/Dolt ledger + Fabro loop reference orchestrator that the livespec family itself dogfoods; `livespec-orchestrator-git-jsonl` carries the existing homegrown serial orchestration logic over a git-jsonl ledger (see `spec.md` §"Contract + reference implementations architecture" for both). The two reference names illustrate why both axes are named: Fabro is loop-portable across ledgers, so the loop MUST be named (`-fabro`), not just the ledger; the git-jsonl reference carries a single homegrown serial loop, so the ledger name alone is unambiguous and no `<loop>` segment is needed. Other catalog variants (e.g., a `gitlab` ledger) are deferred from immediate implementation but retained as recognized future variants.
```

Standalone-installability paragraph:

```diff
-`livespec` itself MUST NOT depend on any `livespec-impl-*` plugin in its code dependency graph: it MUST be installable standalone. The implementation-side skills are simply unavailable until a consumer installs an impl plugin.
+`livespec` itself KEEPS its name and is NOT subject to the `livespec-orchestrator-*` convention: it is the core meta-tool, not an orchestrator plugin (the `livespec` → `livespec-core` rename was retired per `history/v068`). `livespec` MUST NOT depend on any `livespec-orchestrator-*` plugin in its code dependency graph: it MUST be installable standalone. The orchestrator-side skills are simply unavailable until a consumer installs an orchestrator plugin.
```

**Edit 2 — `SPECIFICATION/non-functional-requirements.md`, §"Prose conventions", the version-reference example list.** Only the stale impl-named example token changes; the rule itself MUST remain unchanged.

```diff
-Every version reference in spec prose MUST be prefixed with the owning project name. Examples: `livespec v078`, `livespec-runtime v0.3.0`, `livespec-impl-git-jsonl v0.x`, `livespec-dev-tooling v0.5.x`. External dependency versions follow the same shape (`uv 0.5.x`, `gh 2.x`, `Python 3.10+`). Rationale: livespec-governed repos cross-reference each other constantly; a bare `v0.2.0` is ambiguous between the meta-tool and its siblings.
+Every version reference in spec prose MUST be prefixed with the owning project name. Examples: `livespec v078`, `livespec-runtime v0.3.0`, `livespec-orchestrator-git-jsonl v0.x`, `livespec-dev-tooling v0.5.x`. External dependency versions follow the same shape (`uv 0.5.x`, `gh 2.x`, `Python 3.10+`). Rationale: livespec-governed repos cross-reference each other constantly; a bare `v0.2.0` is ambiguous between the meta-tool and its siblings.
```

**Edit 3 — `SPECIFICATION/contracts.md`, §"Plugin distribution", the `.claude/settings.json` example block + the prose beneath it.** Updates the concrete reference-orchestrator example to the new name so the published install contract example matches reality. Consumers MUST substitute their own orchestrator for the example name.

```diff
-    "livespec-impl-beads":    { "source": { "source": "github", "repo": "thewoolleyman/livespec-impl-beads" } }
+    "livespec-orchestrator-beads-fabro": { "source": { "source": "github", "repo": "thewoolleyman/livespec-orchestrator-beads-fabro" } }
```

```diff
-    "livespec-impl-beads@livespec-impl-beads": true
+    "livespec-orchestrator-beads-fabro@livespec-orchestrator-beads-fabro": true
```

```diff
-Consumer projects MUST enable `livespec` (core) plus the Claude Code Driver plus the impl-plugin named by the project's `.livespec.jsonc` `implementation.plugin` key — substitute that impl (e.g. `livespec-impl-plaintext`) for `livespec-impl-beads` in both blocks above.
+Consumer projects MUST enable `livespec` (core) plus the Claude Code Driver plus the orchestrator plugin named by the project's `.livespec.jsonc` `implementation.plugin` key — substitute that orchestrator for `livespec-orchestrator-beads-fabro` in both blocks above.
```
