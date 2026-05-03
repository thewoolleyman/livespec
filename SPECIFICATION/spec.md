# Specification — `livespec`

This document MUST be read alongside `contracts.md`, `constraints.md`, and `scenarios.md`. The four files together constitute the canonical natural-language specification for `livespec` per the `livespec` template's multi-file convention. Each file scopes a different concern: this file describes intent and behavior; `contracts.md` carries the wire-level interfaces; `constraints.md` carries the architecture-level constraints; `scenarios.md` carries the behavioral narratives.

## Project intent

`livespec` provides governance and lifecycle management for a living `SPECIFICATION` directory. It MUST NOT be conflated with a spec authoring format, an implementation engine, or a workflow runner. The central invariant: a project's `SPECIFICATION` is the maintained source of truth for intended system behavior, and all changes to that `SPECIFICATION` flow through a documented, versioned propose → revise → acknowledge → validate cycle.

The seeded `SPECIFICATION/` tree at this revision (v001) derives from the brainstorming archive at `brainstorming/approach-2-nlspec-based/PROPOSAL.md` (frozen at v036) and `brainstorming/approach-2-nlspec-based/goals-and-non-goals.md`. Companion docs in that archive (the Python style requirements, the NLSpec discipline doc, lifecycle and terminology docs, prior-art survey) MUST migrate via dedicated Phase 8 propose-change cycles per Plan §"Phase 8 — Process every deferred-items entry" rather than land en masse in this seed.

## Runtime and packaging

`livespec` ships as a Claude Code plugin at `.claude-plugin/`. The plugin bundle MUST contain (a) skill prompts under `skills/<sub-command>/SKILL.md`, (b) a Python wrapper layer under `scripts/bin/<sub-command>.py` and `scripts/livespec/commands/<sub-command>.py`, (c) built-in templates under `specification-templates/<name>/`, and (d) vendored pure-Python libraries under `scripts/_vendor/`.

Python 3.10 is the minimum runtime per `.python-version` and `pyproject.toml`'s `requires-python`. The `_bootstrap.py` shebang-wrapper preamble MUST exit 127 on Python below 3.10 with an install-instruction message before any `livespec` import.

Vendored runtime dependencies are: `fastjsonschema`, `returns` (+ vendored upstream `typing_extensions` per v027 D1), `structlog`, and a hand-authored JSONC shim per v026 D1. Each vendored entry MUST appear in `.vendor.jsonc` with non-placeholder `upstream_url`, `upstream_ref`, and `vendored_at` fields.

## Specification model

A spec tree is a directory rooted at the `spec_root` path declared in the active template's `template.json`. The tree MUST contain the template-declared spec files (e.g., `spec.md`, `contracts.md`, `constraints.md`, `scenarios.md`, `README.md` for the `livespec` template), a `proposed_changes/` subdir, and a `history/` subdir. Both the `proposed_changes/` and `history/` subdirs carry a skill-owned `README.md` written by the seed wrapper at seed time and never modified by `revise`; per `contracts.md` §"Sub-spec structural mechanism", every sub-spec tree carries the same skill-owned README pair.

Multi-tree projects (the meta-project case where the project ships its own `livespec` templates) MAY emit one sub-spec tree per template under `<spec_root>/templates/<template-name>/`. Sub-specs follow the same internal structure as the main spec uniformly per v020 Q1, decoupled from the user-facing template's end-user spec convention.

## Sub-command lifecycle

`livespec` exposes six sub-commands: `seed`, `propose-change`, `critique`, `revise`, `prune-history`, and `doctor`. Each sub-command MAY be invoked via `/livespec:<name>` from Claude Code, which dispatches to the matching `skills/<name>/SKILL.md` prompt. The skill prose MUST orchestrate (a) dialogue capture, (b) prompt-driven content generation, (c) wrapper invocation, and (d) structured-finding interpretation.

Per PROPOSAL.md §"Sub-command lifecycle orchestration", every command except `help`, `doctor`, and `resolve_template` MUST run a pre-step `doctor`-static check before its action and a post-step `doctor`-static check after. Pre-step ensures the working state is consistent before mutation; post-step ensures the result is consistent before returning success.

## Versioning

The `SPECIFICATION/history/v<NNN>/` directory holds an immutable snapshot of every spec file as it stood when revision `vNNN` was finalized. Snapshots are produced by `revise`; they MUST be byte-identical to the live spec files at the moment the revision is committed. The version sequence is contiguous: `v001`, `v002`, `v003`, … with no gaps.

`livespec` itself versions via Conventional Commits + semantic-release per v034 D1. Releases happen on `master` as a side-effect of `feat:` / `fix:` commits landing through the protected-branch PR workflow.

## Pruning history

`prune-history` MAY remove the oldest contiguous block of `history/v*/` directories down to a caller-specified retention horizon while preserving the contiguous-version invariant for the remaining tail. Phase 3 lands the parser-only stub; Phase 7 widens it to the actual pruning mechanic.

## Proposed-change and revision file formats

`<spec-target>/proposed_changes/<topic>.md` holds an in-flight change request. The file MUST contain one or more `## Proposal: <name>` sections with `### Target specification files`, `### Summary`, `### Motivation`, and `### Proposed Changes` subsections per PROPOSAL.md §"propose-change". Topic-canonicalization rules widen in Phase 7.

`<spec-target>/proposed_changes/<topic>-revision.md` is the paired revision record produced by `revise`. It records the per-proposal accept/reject decision plus the resulting spec edits. After the revise commit lands, both files move atomically into `<spec-target>/history/v<NNN>/proposed_changes/`.

## Testing approach

Every Python source file under `livespec/`, `bin/`, and `dev-tooling/checks/` MUST have a paired test file at the mirrored path under `tests/`, except: (a) **private-helper modules** — `.py` files whose filename starts with `_` and is NOT `__init__.py` (e.g., `_seed_railway_emits.py`); these are covered transitively through the public function that imports them. (b) **Pure-declaration modules** — files whose AST contains no `FunctionDef` / `AsyncFunctionDef` anywhere (no module-level or class-level functions); covers boilerplate `__init__.py`, pure dataclass declarations, value-object modules, and the `LivespecError` hierarchy — none have testable behavior independent of their consumers. The `bin/_bootstrap.py` shebang preamble has its own special-cased test at `tests/bin/test_bootstrap.py`. The `dev-tooling/checks/tests_mirror_pairing.py` script enforces the binding mechanically and runs in the `just check` aggregate. Per-file line+branch coverage MUST be 100% (enforced by `dev-tooling/checks/per_file_coverage.py`). Coverage is computed under `pytest --cov` with `pyproject.toml`'s `[tool.coverage.run]` settings active.

The v034 D2-D3 Red→Green replay contract gates every `feat:` / `fix:` commit: the Red commit stages exactly one new test file and zero impl files; the Green amend stages the impl that turns the test green; the commit-msg hook verifies the temporal Red→Green order via reflog inspection plus test-file SHA-256 checksum.

## Developer-tooling layout

`justfile` is the single source of truth for every dev-tooling invocation. `lefthook.yml` and CI workflows MUST delegate to `just <target>` and MUST NOT shell out to underlying tools directly (enforced by `dev-tooling/checks/no_direct_tool_invocation.py`). Tool versions for non-Python binaries (`uv`, `just`, `lefthook`) pin via `.mise.toml`; Python and Python packages pin via `uv` against `pyproject.toml`'s `[dependency-groups.dev]`. Lefthook pre-commit runs `just lint-autofix-staged` as its first step, which applies `ruff check --fix` + `ruff format` to the staged Python files only and re-stages them in place; this lets auto-fixable lint trivia (import ordering, formatting) get fixed without forcing a full pre-commit retry. The autofix step runs BEFORE the v034 D3 commit-msg replay hook computes the Red commit's test-file SHA-256 checksum, so the recorded checksum reflects post-autofix bytes; the Green amend stages impl files only (not the test), preserving the test-file-byte-identical invariant the replay hook enforces.

The canonical `just check` aggregate is enumerated in the justfile recipe and re-enumerated in PROPOSAL.md §"Canonical target list". The aggregate runs sequentially with continue-on-failure semantics and exits non-zero if any target fails.

## Definition of Done

A `livespec` change MUST satisfy the Definition of Done in PROPOSAL.md §"Definition of Done" before merge. Bootstrap-minimum: `just check` aggregate passes, paired tests exist for every new source file, the CLAUDE.md coverage check passes, the heading-coverage check passes against `tests/heading-coverage.json`, and the v034 D3 replay-hook trailers are present on `feat:` / `fix:` commits.

The full DoD widens via Phase 7 dogfooded propose-change cycles when individual DoD items surface as needing more rigorous specification.

## Non-goals

`livespec` v1 explicitly does NOT solve subdomain ownership inside a `SPECIFICATION`, semantic routing of cross-cutting changes, or any universal decomposition strategy. It does NOT replace implementation engines. It does NOT define the full template mechanism beyond the v1 contract. See the seeded `goals-and-non-goals` material (this revision's seed input) and the deferred-items archive at `brainstorming/approach-2-nlspec-based/deferred-items.md` for the long-form non-goal rationale.

## Self-application

`livespec` is self-applied: this very `SPECIFICATION/` tree is the seeded output of running `/livespec:seed` against the project's own brainstorming archive. The Phase 6 self-application is bootstrap-only, with the imperative window closing at this seed commit per PROPOSAL.md §"Self-application" (v018 Q2; v019 Q1 clarification). All subsequent mutations to this `SPECIFICATION/` MUST flow through `/livespec:propose-change` → `/livespec:revise` against this tree (or, for the two sub-spec trees under `templates/`, against the corresponding sub-spec target).

The v021 Q3 imperative one-time `tests/heading-coverage.json` population step lands alongside this seed commit; from this revision onward, every revise that adds, changes, or removes a `##` heading MUST update `tests/heading-coverage.json` via the governed propose-change/revise loop's `resulting_files[]` mechanism.
