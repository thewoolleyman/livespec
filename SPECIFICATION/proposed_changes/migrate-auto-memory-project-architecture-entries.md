---
topic: migrate-auto-memory-project-architecture-entries
author: claude-opus-4-7
created_at: 2026-05-26T08:34:26Z
---

## Proposal: Migrate tmp/ ownership convention into non-functional-requirements.md

### Target specification files

- non-functional-requirements.md

### Summary

Codify the existing project convention (currently held only in auto-memory project_tmp_directory_ownership.md) that the repo-root tmp/ directory is user-owned personal scratch space and MUST NOT be deleted, cleared, or treated as transient by any tooling, agent, or skill; tooling-owned scratch MUST scope under a subdirectory such as tmp/bootstrap/.

### Motivation

Auto-memory entry project_tmp_directory_ownership.md documents a long-standing convention (established 2026-04-25) that the user's personal scratch at tmp/ is sacred. This belongs in non-functional-requirements.md as a contributor-facing architectural invariant on the repo layout, so future agents and tooling discover it without depending on per-agent auto-memory. Per livespec memory's own discipline 'Spec is for contracts, not tracking', a persistent layout invariant IS a contract and belongs in spec.

Migration audit context for the entire propose-change file (file-level review per feedback_revise_decisions_are_per_file): three project_*.md auto-memory entries are migrated by this file (this finding, plus the research/workflow-processes/ split and the vendored-lib pyright resolution findings below). Five auto-memory entries were considered and deliberately NOT migrated: (a) project_enforcement_suite_framing.md, project_mise_for_tool_versions.md, project_uv_python_toolchain.md — already covered by existing spec at non-functional-requirements.md §Enforcement-suite invocation and §Toolchain pins; (b) project_li_xxjopf_pyright_epic.md, project_li_nhz_comment_discipline_epic.md — completion-log entries that belong in git log per the 'Spec is for contracts, not tracking' rule, NOT in spec. All feedback_*.md and user_*.md entries are excluded by category — they are agent-collaboration preferences and user-role profile, not project architectural commitments.

### Proposed Changes

Add a new H3 subsection under non-functional-requirements.md §Constraints (sibling to §Developer-tooling layout, §Package layout, etc.) titled '### Repo-root tmp/ ownership':

> The repo-root `tmp/` directory is user-owned personal scratch space. Tooling, agents, and skills MUST NOT delete, clear, or otherwise mutate files under `tmp/` directly; `rm -r tmp/`, `rm tmp/*`, and assumptions that `tmp/` is empty or disposable are forbidden. Tooling-owned scratch MUST scope under a named subdirectory (typically `tmp/bootstrap/` for bootstrap scaffolding, or another scoped name) that the tooling MAY freely create, write, and clear. `tmp/` itself MUST remain git-untracked.

No `tests/heading-coverage.json` change is needed (the addition is an H3-level subsection under existing H2 sections), but verify against the file's current state at revise time.

## Proposal: Codify research/workflow-processes/ tool-agnostic-vs-implementation split

### Target specification files

- non-functional-requirements.md

### Summary

Codify the existing project convention (currently held only in auto-memory project_tool_agnostic_vs_workflow_docs.md) that research/workflow-processes/ contains two structurally separate artifacts: tool-agnostic-workflow.md (generic spec-implementation workflow vocabulary, future SPECIFICATION content) and architecture-summary.html (livespec-specific implementation of that workflow). The two MUST stay separate; the tool-agnostic doc is the source of truth and MUST NOT carry livespec-* names; the livespec-specific doc renders the same pattern in livespec terms.

### Motivation

Auto-memory entry project_tool_agnostic_vs_workflow_docs.md documents a deliberate authoring discipline that prevents the conceptual model from being recursively tangled with livespec implementation names. Without spec codification, future revisions of either doc can silently collapse the split. The convention is architectural (it shapes which content can promote into SPECIFICATION/ and which is implementation-local) and belongs in non-functional-requirements.md.

### Proposed Changes

Add a new H3 subsection under non-functional-requirements.md §Constraints titled '### research/workflow-processes/ tool-agnostic vs implementation-specific split':

> The `research/workflow-processes/` directory MUST host two structurally separate artifacts. `tool-agnostic-workflow.md` describes the generic spec ↔ implementation workflow pattern using tooling-agnostic vocabulary ("Specification", "Implementation", "Capture Impl Gaps", "Capture Spec Drift", "Spec Reader", "Persistent Agent Knowledge", etc.); it MUST NOT reference `livespec-*` names. `architecture-summary.html` describes the livespec-specific implementation of that workflow using `livespec-core`, `livespec-impl-plaintext`, `livespec-impl-beads`, `/livespec:*`, and other tooling-specific names. The tool-agnostic doc is the source of truth — concept changes (e.g., gap-vs-drift naming) MUST land in the tool-agnostic doc first and then regenerate the livespec-specific doc to match. The two MUST NOT be collapsed into a single document. If the two drift, contributors MUST halt and reconcile rather than letting either become silently authoritative.

No `tests/heading-coverage.json` change is needed (the addition is an H3-level subsection under existing H2 sections), but verify against the file's current state at revise time.

## Proposal: Codify vendored-lib pyright resolution discipline (extraPaths + stubPath)

### Target specification files

- non-functional-requirements.md

### Summary

Codify the vendored-import pyright resolution mechanism (currently held only in auto-memory project_pyright_cascade_fix.md) as an architectural commitment: vendored libs MUST resolve to typed surfaces under pyright via the combination of `[tool.pyright].extraPaths` covering both `.claude-plugin/scripts` and `.claude-plugin/scripts/_vendor`, plus `[tool.pyright].stubPath = ".claude-plugin/scripts/_stubs"` for libs lacking a py.typed marker. Per-vendor stub trees MUST live under `.claude-plugin/scripts/_stubs/<lib>-stubs/` for any vendored lib without an upstream py.typed marker.

### Motivation

Auto-memory entry project_pyright_cascade_fix.md documents the architectural mechanism that made check-types viable across the vendored-libs surface. The mechanism is required for every livespec-impl-* sibling repo (per the memo's 'How to apply') and is therefore an architectural commitment, not an ephemeral epic-completion artifact. The completion log itself (li-xxjopf) is intentionally NOT migrated — only the persistent architectural pattern. The existing §Typechecker rule set names `_vendor/**` exclusion and `useLibraryCodeForTypes = true` but does not codify the extraPaths/stubPath/per-vendor-stubs triple that actually makes vendored imports resolve.

### Proposed Changes

Add a new H4 subsection under non-functional-requirements.md §Constraints §Typechecker rule set, immediately following the existing '#### Vendored-lib type-safety integration' subsection, titled '#### Vendored-import pyright resolution discipline':

> Vendored libs under `.claude-plugin/scripts/_vendor/` MUST resolve to typed surfaces under pyright via three coupled `pyproject.toml` `[tool.pyright]` settings:
>
> - `extraPaths` MUST include both `.claude-plugin/scripts` (for first-party imports) and `.claude-plugin/scripts/_vendor` (for vendored libs). Without these, vendored-import lookups resolve as Unknown and cascade into `reportUnknownMemberType` / `reportUnknownVariableType` / `reportUnknownArgumentType` at every downstream call site.
> - `stubPath` MUST be set to `.claude-plugin/scripts/_stubs` so pyright finds per-vendor PEP 561 stub trees for vendored libs lacking an upstream `py.typed` marker.
> - For each vendored lib without an upstream `py.typed` marker, a project-local stub tree at `.claude-plugin/scripts/_stubs/<lib>-stubs/` MUST exist, carrying at minimum `__init__.pyi` declaring the public surface used in first-party code. The stub tree MUST be excluded from strict-mode coverage via `[tool.pyright].exclude += ["**/_stubs/**"]`.
>
> The same `_stubs/` tree and `[tool.pyright]` block MUST be copied into every new `livespec-impl-*` sibling repository at creation time so pyright resolves vendored imports identically across the family.

No `tests/heading-coverage.json` change is needed (the addition is an H4-level subsection under an existing H3); verify against the file's current state at revise time.
