# Contracts — `livespec`

This file enumerates the wire-level interfaces between `livespec`'s skill prompts, Python wrappers, and templates. Per `livespec`'s repo-native principle, contracts MUST be language-neutral (JSON or CLI argument shapes), so any tool authored against the contracts works regardless of which language internalizes them.

## Wrapper CLI surface

Every Python wrapper under `.claude-plugin/scripts/bin/<sub-command>.py` MUST accept `--project-root <path>` per PROPOSAL.md §"Wrapper CLI surface" lines 349-356, defaulting to `Path.cwd()`. Each sub-command adds its own flags above that baseline.

| Sub-command | Required flags | Optional flags |
|---|---|---|
| `seed` | `--seed-json <path>` | `--project-root <path>` |
| `propose-change` | `--findings-json <path>`, `<topic>` (positional) | `--author <id>`, `--reserve-suffix <text>`, `--spec-target <path>`, `--project-root <path>` |
| `critique` | `--findings-json <path>` | `--author <id>`, `--spec-target <path>`, `--project-root <path>` |
| `revise` | `--revise-json <path>` | `--author <id>`, `--spec-target <path>`, `--project-root <path>` |
| `prune-history` | (varies; Phase 7 widens) | (Phase 7 widens) |
| `doctor` (static) | (none) | `--project-root <path>` |
| `resolve-template` | `--template <value>` (Phase-3-min required; Phase-7 widens to optional) | `--project-root <path>` |

The `--spec-target <path>` flag MUST select a spec tree (the main spec or a sub-spec) explicitly. When omitted, the wrapper SHOULD default to `<project-root>/SPECIFICATION/` (the main spec).

## Lifecycle exit-code table

Every wrapper MUST emit one of the following exit codes per PROPOSAL.md §"Exit code contract":

| Code | Meaning |
|---|---|
| `0` | success — operation completed and any documented stdout was emitted |
| `1` | internal bug — uncaught exception; structured traceback on stderr |
| `2` | `UsageError` — bad CLI invocation (unknown flag, missing required arg, wrong arg count) |
| `3` | `PreconditionError` — project-state precondition not met (missing config, malformed file, idempotency conflict) |
| `4` | `ValidationError` — schema or wire-format validation failure on inbound payload (retryable per the calling SKILL.md's retry-on-exit-4 contract) |
| `127` | too-old Python or missing tool — `_bootstrap.py` early exit |

Domain errors flow as `Failure(<LivespecError>)` payloads on the railway; the supervisor `main()` pattern-matches and lifts the exit code from the error's `exit_code` ClassVar. Bugs propagate as raised exceptions to the supervisor's bug-catcher and result in exit 1.

## Skill ↔ template JSON contracts

The seed flow exchanges a JSON payload conforming to `seed_input.schema.json`. The schema is co-authoritative with its paired dataclass at `livespec/schemas/dataclasses/seed_input.py` per the schema-dataclass-pairing convention (v013 M6). Drift is caught by `dev-tooling/checks/schema_dataclass_pairing.py`.

The propose-change flow ingests `proposal_findings.schema.json`-conforming JSON via `--findings-json <path>`. The critique flow emits `proposal_findings.schema.json`-conforming JSON for downstream propose-change consumption. The doctor flow emits `doctor_findings.schema.json`-conforming JSON to stdout for the supervisor's exit-code derivation.

The revise flow ingests `revise_input.schema.json`-conforming JSON describing per-proposal accept/reject decisions and the resulting spec edits. Future widening MAY add additional payload schemas; each new schema MUST land with its paired dataclass in the same revision.

## Sub-spec structural mechanism

Sub-spec emission is opt-in per v020 Q2: the seed prompt's pre-seed dialogue asks "Does this project ship its own livespec templates that should be governed by sub-spec trees?" On "yes", the prompt emits one `sub_specs[]` entry per template named in the dialogue, each carrying a per-template `files[]` array with its own spec-file paths under `<spec_root>/templates/<template_name>/`.

The seed wrapper materializes the main spec tree AND each sub-spec tree atomically per v018 Q1: a single `bin/seed.py --seed-json <payload>` invocation writes, for every spec tree, (a) every template-declared spec file, (b) the skill-owned `proposed_changes/README.md` and `history/README.md` directory-description files, (c) the `history/v001/` snapshot of every template-declared spec file, and (d) the `history/v001/proposed_changes/` subdirectory marker preserved in git via `.gitkeep` when the directory would otherwise be empty. The auto-captured `history/v001/proposed_changes/seed.md` + `seed-revision.md` are emitted for the main spec only; sub-specs do NOT receive auto-captured seed proposals per v018 Q1 — the main-spec `seed.md` documents the multi-tree creation as a whole, and each sub-spec's `history/v001/proposed_changes/` is consequently empty (the `.gitkeep` is the marker).

The `propose-change`, `revise`, `critique`, and `doctor` sub-commands all accept `--spec-target <path>` to scope their operation to one specific spec tree. `--spec-target <project-root>/SPECIFICATION/templates/livespec/` targets the `livespec` template's sub-spec; `--spec-target <project-root>/SPECIFICATION/` targets the main spec; etc.

## Per-sub-spec doctor parameterization

The doctor static phase runs once per spec tree. The wrapper's main loop enumerates the main spec plus every `<spec_root>/templates/<name>/` sub-spec, runs the static checks against each, and emits per-tree findings on stdout. The wrapper's overall exit code is the worst per-tree code: any `fail` finding lifts the wrapper to exit non-zero.

The static-check registry per v022 D7 is a narrowed enumeration in `livespec/doctor/static/__init__.py`. Each registered check exports `run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]`; the `ctx.spec_root` attribute carries the per-tree root. Per-check applicability dispatch (some checks apply only to main specs, some only to sub-specs) is finalized via the `DoctorContext`'s template-config inspection per v021 Q1.

## Resolved-template stdout contract

`bin/resolve_template.py` MUST emit on success exactly one line: the resolved template directory as an absolute POSIX path, followed by `\n`. Paths containing spaces are emitted literally; callers MUST NOT pipe through shells that re-split on whitespace. The contract is frozen in v1; future template-discovery extensions MUST extend, not replace, the stdout shape and CLI flag set.

## Help-requested escape

Every wrapper MUST treat `-h` / `--help` as a `HelpRequested` signal, emit the argparse-rendered help text on stdout, and exit 0 (NOT exit 2). Per `commands/CLAUDE.md`, `HelpRequested.text` is one of two `commands/`-layer stdout-write exemptions (the other being `resolve_template`'s resolved-path emission).

## Pre-commit step ordering

Lefthook pre-commit runs three commands in order: `00-lint-autofix-staged` (delegates to `just lint-autofix-staged`; ruff fix + format on staged `.py` files; non-blocking — unfixable issues fall through to be caught by `just check`'s `check-lint`/`check-format` later); `01-commit-pairs-source-and-test` (delegates to `just check-commit-pairs-source-and-test`; cheap staged-file-list inspection per v033 D3); `02-check-pre-commit` (delegates to `just check-pre-commit`; the heavy check aggregate, Red-mode-aware per v036 D1). Earlier steps fail-fast so the developer learns about a missing test pair without waiting for pytest. Commit-msg stage runs `just check-red-green-replay {1}` (the v034 D3 replay hook). Pre-push runs `just check` (the full aggregate).

When the staged tree contains ZERO `.py` files, `just check-pre-commit` runs a CONSERVATIVE doc-only subset (`check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`) instead of the full aggregate, since the Python-related gates have no work to do on doc-only commits. The classification trigger is the strict "zero `.py` staged" predicate; any `.py` file in the staged tree (even a single test file in Red mode) routes through the full aggregate. Pre-push and CI never apply this subsetting — the full aggregate is the load-bearing safety net for any branch landing on `master`.
